"""Clause extraction engine."""

import httpx
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDoc
import hashlib
import re
from .models import Clause, Document
from datetime import datetime
from typing import Optional


class Extraction:
    """Extracts clauses from legal documents."""
    
    def __init__(self, timeout: int = 15, max_bytes: int = 1_000_000):
        """Initialize extraction engine."""
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
    
    def extract_document(self, url: str, doc_type: str) -> Optional[Document]:
        """
        Extract clauses from a legal document URL.
        
        Returns Document with clauses or None if extraction fails.
        """
        try:
            response = self.client.get(url)
            response.raise_for_status()
            
            if len(response.content) > self.max_bytes:
                return None
            
            html = response.text
            
            title = self._extract_title(html)
            
            clauses = self._extract_clauses(html, url)
            
            document = Document(
                url=url,
                doc_type=doc_type,
                title=title,
                last_updated=datetime.now(),
                clauses=clauses
            )
            
            return document
        
        except Exception as e:
            print(f"Extraction error for {url}: {e}")
            return None
    
    def _extract_title(self, html: str) -> str:
        """Extract document title."""
        try:
            doc = ReadabilityDoc(html)
            return doc.short_title()
        except:
            try:
                soup = BeautifulSoup(html, 'lxml')
                title_tag = soup.find('title')
                if title_tag:
                    return title_tag.get_text(strip=True)
                h1 = soup.find('h1')
                if h1:
                    return h1.get_text(strip=True)
            except:
                pass
        return "Untitled Document"
    
    def _extract_clauses(self, html: str, url: str) -> list[Clause]:
        """Extract individual clauses from HTML."""
        clauses = []
        
        try:
            doc = ReadabilityDoc(html)
            content_html = doc.summary()
            
            soup = BeautifulSoup(content_html, 'lxml')
            
            sections = self._sectionize(soup)
            
            paragraph_index = 0
            for section in sections:
                heading = section.get('heading', 'General')
                text = section.get('text', '')
                
                if len(text.strip()) < 50:
                    continue
                
                paragraphs = self._split_into_paragraphs(text)
                
                for para_text in paragraphs:
                    if len(para_text.strip()) < 50:
                        continue
                    
                    clause_id = self._generate_clause_id(url, paragraph_index, para_text)
                    
                    clause = Clause(
                        id=clause_id,
                        text=para_text,
                        section_title=heading,
                        paragraph_index=paragraph_index,
                        document_url=url
                    )
                    
                    clauses.append(clause)
                    paragraph_index += 1
        
        except Exception as e:
            print(f"Clause extraction error: {e}")
            soup = BeautifulSoup(html, 'lxml')
            paragraphs = soup.find_all(['p', 'li'])
            
            for idx, para in enumerate(paragraphs[:100]):
                text = para.get_text(strip=True)
                if len(text) > 50:
                    clause_id = self._generate_clause_id(url, idx, text)
                    clause = Clause(
                        id=clause_id,
                        text=text,
                        section_title="General",
                        paragraph_index=idx,
                        document_url=url
                    )
                    clauses.append(clause)
        
        return clauses
    
    def _sectionize(self, soup: BeautifulSoup) -> list[dict]:
        """Break content into sections based on headings."""
        sections = []
        current_heading = "General"
        current_texts = []
        
        for element in soup.descendants:
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                if current_texts:
                    sections.append({
                        'heading': current_heading,
                        'text': ' '.join(current_texts)
                    })
                    current_texts = []
                current_heading = element.get_text(strip=True)
            
            elif element.name in ['p', 'li']:
                text = element.get_text(strip=True)
                if text:
                    current_texts.append(text)
        
        if current_texts:
            sections.append({
                'heading': current_heading,
                'text': ' '.join(current_texts)
            })
        
        return sections
    
    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into logical paragraphs."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        paragraphs = []
        current = []
        
        for sentence in sentences:
            current.append(sentence)
            if len(' '.join(current)) > 200:
                paragraphs.append(' '.join(current))
                current = []
        
        if current:
            paragraphs.append(' '.join(current))
        
        return paragraphs
    
    def _generate_clause_id(self, url: str, index: int, text: str) -> str:
        """Generate unique clause ID."""
        content = f"{url}:{index}:{text[:100]}"
        hash_obj = hashlib.sha256(content.encode())
        return f"clause_{hash_obj.hexdigest()[:12]}"
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
