"""AI-powered document extraction using Together AI with OpenAI SDK."""

import os
import httpx
from typing import Optional
from openai import OpenAI
from .models import Document, Clause
from .user_agents import get_headers
from datetime import datetime
import json
import re


class LlamaExtractor:
    """Extract clauses from legal documents using Llama AI."""
    
    def __init__(self, timeout: int = 30):
        """Initialize Llama Stack client with Together AI."""
        self.timeout = timeout
        self.http_client = httpx.Client(timeout=timeout, follow_redirects=True)
        
        # Initialize OpenAI client pointing to Together AI
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable not set")
        
        # Use Together AI via OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1"
        )
        
        # Use Llama 3.3 70B for best extraction quality
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    
    def cleanup(self):
        """Close the HTTP client."""
        if hasattr(self, 'http_client'):
            self.http_client.close()
    
    def extract_document(self, url: str, doc_type: str) -> Optional[Document]:
        """
        Extract clauses from a legal document using AI.
        
        Returns Document with intelligently parsed clauses.
        """
        try:
            # Fetch the HTML with random user-agent
            response = self.http_client.get(url, headers=get_headers())
            response.raise_for_status()
            
            # Validate content before processing
            if not self._is_valid_html_content(response):
                return None
            
            html = response.text
            
            # Extract metadata
            title = self._extract_title(html)
            last_updated = self._extract_last_updated(html)
            
            # Use AI to extract clauses
            clauses = self._extract_clauses_with_ai(html, url, doc_type, last_updated)
            
            if not clauses:
                print(f"No clauses extracted from {url}")
            
            # Always return a Document, even if no clauses found
            # This ensures all fetched documents appear in metadata
            document = Document(
                url=url,
                doc_type=doc_type,
                title=title,
                last_updated=last_updated,
                clauses=clauses  # May be empty list
            )
            
            return document
        
        except Exception as e:
            print(f"AI extraction error for {url}: {e}")
            return None
    
    def _is_valid_html_content(self, response: httpx.Response) -> bool:
        """
        Validate that response contains valid HTML suitable for AI extraction.
        
        Checks Content-Type, length, and basic HTML structure.
        """
        # Check Content-Type header
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type:
            return False
        
        # Check content length (minimum 500 chars, max 5MB)
        content = response.text
        if len(content) < 500 or len(content) > 5_000_000:
            return False
        
        # Check for basic HTML structure (has opening tags)
        if not ('<html' in content.lower() or '<body' in content.lower() or '<div' in content.lower()):
            return False
        
        # Check it's not an error page (common error page indicators)
        content_lower = content.lower()
        error_indicators = ['404 not found', 'page not found', 'error occurred', 'access denied']
        if any(indicator in content_lower[:1000] for indicator in error_indicators):
            return False
        
        return True
    
    def _extract_clauses_with_ai(self, html: str, url: str, doc_type: str, last_updated: Optional[str]) -> list[Clause]:
        """Use Llama AI to intelligently extract and categorize clauses."""
        
        # Remove HTML tags but preserve structure
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Get clean text with preserved spacing
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Validate text content has enough substance
        if len(text_content) < 200:
            return []
        
        # Limit to reasonable size (Llama can handle long context but be efficient)
        if len(text_content) > 20000:
            text_content = text_content[:20000]
        
        # Craft extraction prompt
        prompt = f"""You are analyzing a legal policy document. Extract important clauses that users should be aware of.

Focus on these categories:
- **Data Sale/Sharing**: Any mention of selling, renting, monetizing, sharing, or licensing user data to third parties
- **Arbitration**: Forced arbitration, class action waivers, litigation restrictions
- **Tracking**: Analytics, cookies, pixels, user behavior tracking
- **Location Data**: GPS, location tracking, geolocation
- **Data Retention**: How long data is kept
- **Children's Data**: COPPA compliance, data from minors

For each concerning clause you find:
1. Extract the EXACT text as it appears (preserve capitalization, punctuation, spacing)
2. Identify the section heading it belongs to
3. Categorize it (dataSale, arbitration, tracking, location, retention, children)
4. Rate severity (high, medium, low)

Return ONLY a JSON array of clauses. Each clause must have:
- "text": exact clause text (verbatim from document)
- "section": section heading
- "category": one of the categories above
- "severity": high, medium, or low
- "reason": brief explanation why it's concerning

Document text:
{text_content}

Return valid JSON only, no markdown formatting:"""

        try:
            content = None  # Initialize for error handling
            
            # Call Llama via Together AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal document analyzer. Return only valid JSON arrays with no markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4096
            )
            
            # Parse response
            content = response.choices[0].message.content
            if not content:
                return []
            
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            # Parse JSON
            extracted_clauses = json.loads(content)
            
            # Convert to Clause objects
            clauses = []
            for idx, clause_data in enumerate(extracted_clauses):
                # Generate unique ID
                clause_id = f"clause_ai_{idx}_{hash(clause_data.get('text', '')[:50]) % 10000}"
                
                clause = Clause(
                    id=clause_id,
                    text=clause_data.get('text', ''),
                    section_title=clause_data.get('section', 'General'),
                    paragraph_index=idx,
                    document_url=url,
                    document_type=doc_type,
                    last_updated=last_updated,
                    context_before="",
                    context_after="",
                    ai_category=clause_data.get('category'),
                    ai_severity=clause_data.get('severity'),
                    ai_reason=clause_data.get('reason')
                )
                clauses.append(clause)
            
            return clauses
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            if content is not None:
                print(f"Response was: {content[:500]}")
            return []
        except Exception as e:
            print(f"AI extraction failed: {e}")
            return []
    
    def _extract_title(self, html: str) -> str:
        """Extract document title."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text(strip=True)
            
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)
        except:
            pass
        
        return "Legal Document"
    
    def _extract_last_updated(self, html: str) -> Optional[str]:
        """Extract last updated date."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            text = soup.get_text()
            
            patterns = [
                r'(?:last updated|last modified|updated|effective date|last revised)[\s:]*([A-Za-z]+ \d{1,2},? \d{4})',
                r'(?:last updated|last modified|updated|effective date|last revised)[\s:]*(\d{1,2}/\d{1,2}/\d{4})',
                r'(?:last updated|last modified|updated|effective date|last revised)[\s:]*(\d{4}-\d{2}-\d{2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        except:
            pass
        
        return None
    
    def close(self):
        """Close HTTP client."""
        self.http_client.close()
