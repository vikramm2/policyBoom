from app.utils import same_registrable_domain
from app.crawler import discover_policy_links


def test_same_domain_filter():
    assert same_registrable_domain('https://example.com', 'https://help.example.com')
    assert same_registrable_domain('https://example.com', 'https://www.example.com')
    assert not same_registrable_domain('https://example.com', 'https://example.co')
    assert not same_registrable_domain('https://example.com', 'https://different.com')


def test_fallbacks_included():
    links = discover_policy_links('https://example.com')
    
    assert 'https://example.com/privacy' in links
    assert 'https://example.com/privacy-policy' in links
    assert 'https://example.com/terms' in links
    assert 'https://example.com/terms-of-service' in links
    assert 'https://example.com/legal/terms' in links
    assert 'https://example.com/legal/privacy' in links
