import os
import time
import requests
from bs4 import BeautifulSoup
from .utils import is_probable_policy_path, absolutize, same_registrable_domain


CRWLR_TIMEOUT_SECONDS = int(os.getenv('CRWLR_TIMEOUT_SECONDS', '15'))
CRWLR_MAX_DOCS = int(os.getenv('CRWLR_MAX_DOCS', '4'))
CRWLR_UA = os.getenv('CRWLR_UA', 'CRWLR/0.1 (+contact@example.invalid)')
CRWLR_MAX_BYTES = int(os.getenv('CRWLR_MAX_BYTES', '1048576'))


def discover_policy_links(seed_url: str) -> list[str]:
    links = set()
    
    try:
        resp = fetch(seed_url, timeout=CRWLR_TIMEOUT_SECONDS)
        soup = BeautifulSoup(resp.text, 'lxml')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = absolutize(seed_url, href)
            
            if same_registrable_domain(seed_url, absolute_url):
                if is_probable_policy_path(absolute_url):
                    links.add(absolute_url)
    except Exception:
        pass
    
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(seed_url)
    base_url = urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    
    fallbacks = [
        '/privacy',
        '/privacy-policy',
        '/terms',
        '/terms-of-service',
        '/legal/terms',
        '/legal/privacy'
    ]
    
    for path in fallbacks:
        fallback_url = base_url + path
        links.add(fallback_url)
    
    return sorted(list(links))


def fetch(url: str, timeout: int = 15) -> requests.Response:
    headers = {
        'User-Agent': CRWLR_UA
    }
    
    resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
    
    content_length = resp.headers.get('Content-Length')
    if content_length and int(content_length) > CRWLR_MAX_BYTES:
        raise ValueError(f"Content-Length {content_length} exceeds max bytes {CRWLR_MAX_BYTES}")
    
    resp.raise_for_status()
    
    return resp
