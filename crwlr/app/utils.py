import re
from urllib.parse import urljoin, urlparse
import tldextract


def is_probable_policy_path(path: str) -> bool:
    keywords = ['privacy', 'terms', 'policy', 'legal', 'conditions', 'tos']
    path_lower = path.lower()
    return any(keyword in path_lower for keyword in keywords)


def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)


def clean_text(s: str) -> str:
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def same_registrable_domain(a: str, b: str) -> bool:
    ext_a = tldextract.extract(a)
    ext_b = tldextract.extract(b)
    
    domain_a = f"{ext_a.domain}.{ext_a.suffix}" if ext_a.suffix else ext_a.domain
    domain_b = f"{ext_b.domain}.{ext_b.suffix}" if ext_b.suffix else ext_b.domain
    
    return domain_a == domain_b
