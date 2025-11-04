"""Multi-domain and subdomain discovery engine."""

import httpx
from bs4 import BeautifulSoup
import tldextract
import time
import random
from typing import Set
from urllib.parse import urljoin, urlparse

from .user_agents import get_headers


class Discovery:
    """Discovers legal documents across domains and subdomains."""
    
    POLICY_KEYWORDS = [
        'privacy', 'terms', 'legal', 'policy', 'agreement',
        'tos', 'service', 'conditions', 'eula', 'gdpr', 'ccpa'
    ]
    
    # Optimized: Most common paths first, removed rarely-used ones
    COMMON_PATHS = [
        '/privacy',
        '/terms',
        '/legal',
        '/privacy-policy',
        '/terms-of-service',
    ]
    
    def __init__(self, timeout: int = 15, max_docs: int = 10, max_valid_docs: int = 3):
        """Initialize discovery engine."""
        self.timeout = timeout
        self.max_docs = max_docs
        self.max_valid_docs = max_valid_docs  # Stop after finding this many valid docs
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.failed_urls = set()  # Cache failed URLs
    
    def discover(self, seed_url: str) -> list[dict]:
        """
        Discover all policy documents for a domain.
        
        Returns list of dicts with url, doc_type, confidence.
        """
        if not seed_url.startswith(('http://', 'https://')):
            seed_url = f'https://{seed_url}'
        
        discovered = set()
        policy_urls = []
        valid_count = 0
        
        try:
            response = self.client.get(seed_url, headers=get_headers())
            response.raise_for_status()
            
            discovered_urls = self._extract_policy_links(seed_url, response.text)
            discovered.update(discovered_urls)
            
            fallback_urls = self._generate_fallback_urls(seed_url)
            discovered.update(fallback_urls)
            
            # Validate URLs with HEAD requests and stop early
            for url in list(discovered)[:self.max_docs]:
                # Skip if we already found enough valid documents
                if valid_count >= self.max_valid_docs:
                    break
                
                # Add random delay (1-3 seconds) to mimic human behavior
                time.sleep(random.uniform(1.0, 3.0))
                
                # Check if URL exists before adding
                if self._url_exists(url):
                    doc_type = self._classify_document_type(url)
                    confidence = self._calculate_confidence(url)
                    policy_urls.append({
                        'url': url,
                        'doc_type': doc_type,
                        'confidence': confidence
                    })
                    valid_count += 1
        
        except Exception as e:
            print(f"Discovery error for {seed_url}: {e}")
        
        return policy_urls
    
    def _extract_policy_links(self, base_url: str, html: str) -> Set[str]:
        """Extract policy-related links from HTML."""
        links = set()
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            base_domain = tldextract.extract(base_url)
            
            for anchor in soup.find_all('a', href=True):
                href = anchor.get('href', '')
                absolute_url = urljoin(base_url, href)
                
                if self._is_same_registrable_domain(absolute_url, base_url):
                    if self._is_probable_policy_url(absolute_url):
                        links.add(absolute_url)
        
        except Exception:
            pass
        
        return links
    
    def _generate_fallback_urls(self, base_url: str) -> Set[str]:
        """Generate common policy URL patterns including mobile/AMP versions."""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Extract domain parts for mobile variants
        ext = tldextract.extract(base_url)
        domain = ext.domain
        suffix = ext.suffix
        
        fallbacks = set()
        
        # Standard paths on main domain
        for path in self.COMMON_PATHS:
            fallbacks.add(f"{base}{path}")
            
            # Try mobile versions (m.domain.com)
            if not ext.subdomain or ext.subdomain != 'm':
                mobile_url = f"{parsed.scheme}://m.{domain}.{suffix}{path}"
                fallbacks.add(mobile_url)
            
            # Try AMP versions
            fallbacks.add(f"{base}{path}?amp=1")
            fallbacks.add(f"{base}{path}?print=true")
        
        # Try mobile domain without paths
        if not ext.subdomain or ext.subdomain != 'm':
            fallbacks.add(f"{parsed.scheme}://m.{domain}.{suffix}/privacy")
            fallbacks.add(f"{parsed.scheme}://m.{domain}.{suffix}/terms")
        
        return fallbacks
    
    def _is_same_registrable_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs share the same registrable domain."""
        ext1 = tldextract.extract(url1)
        ext2 = tldextract.extract(url2)
        return (ext1.domain == ext2.domain and ext1.suffix == ext2.suffix)
    
    def _is_probable_policy_url(self, url: str) -> bool:
        """Check if URL likely contains policy content."""
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in self.POLICY_KEYWORDS)
    
    def _classify_document_type(self, url: str) -> str:
        """Classify document type based on URL."""
        url_lower = url.lower()
        
        if 'privacy' in url_lower:
            return 'Privacy Policy'
        elif 'terms' in url_lower or 'tos' in url_lower:
            return 'Terms of Service'
        elif 'cookie' in url_lower:
            return 'Cookie Policy'
        elif 'eula' in url_lower:
            return 'EULA'
        elif 'acceptable' in url_lower or 'aup' in url_lower:
            return 'Acceptable Use Policy'
        else:
            return 'Legal Document'
    
    def _calculate_confidence(self, url: str) -> float:
        """Calculate confidence score for URL."""
        url_lower = url.lower()
        score = 0.5
        
        if '/privacy' in url_lower or '/terms' in url_lower:
            score += 0.3
        
        keyword_count = sum(1 for kw in self.POLICY_KEYWORDS if kw in url_lower)
        score += min(keyword_count * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _url_exists(self, url: str) -> bool:
        """
        Check if URL exists using HEAD request with GET fallback.
        
        Returns True for 2xx and 3xx responses, False for 404/errors.
        Caches only true failures (404, network errors) to avoid retries.
        """
        if url in self.failed_urls:
            return False
        
        try:
            # Try HEAD request first (lightweight) with random user-agent
            response = self.client.head(url, timeout=5, headers=get_headers())
            
            # Accept 2xx and 3xx status codes
            if 200 <= response.status_code < 400:
                return True
            
            # If HEAD not allowed (405/501), fallback to GET with minimal download
            if response.status_code in (405, 501):
                # Try GET request but limit download with new headers
                response = self.client.get(url, timeout=5, headers=get_headers())
                if 200 <= response.status_code < 400:
                    return True
            
            # True failures: 404, 403, 500, etc.
            if response.status_code in (404, 410):
                self.failed_urls.add(url)
            
            return False
        
        except Exception:
            # Network errors, timeouts, DNS failures - mark as failed
            self.failed_urls.add(url)
            return False
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
