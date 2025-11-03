"""Utility functions for PolicyBoom."""

import re
from urllib.parse import quote


def generate_text_fragment_url(base_url: str, text: str, max_words: int = None) -> str:
    """
    Generate a verification URL that helps users find the clause using browser search.
    
    Instead of fragile text fragments, this creates a URL to a verification page that:
    1. Shows the snippet to search for
    2. Copies it to clipboard
    3. Opens the target page
    4. User can press Ctrl+F to find it
    
    Args:
        base_url: The base URL of the document
        text: The text to search for (matched clause pattern)
        max_words: Maximum words to use (unused, kept for compatibility)
    
    Returns:
        URL to verification page with snippet and target URL
        
    Example:
        >>> generate_text_fragment_url(
        ...     "https://example.com/policy",
        ...     "agree to binding arbitration"
        ... )
        'http://localhost:5000/verify?url=https%3A%2F%2Fexample.com%2Fpolicy&snippet=agree+to+binding+arbitration'
    """
    # Clean and normalize text
    clean_text = re.sub(r'\s+', ' ', text.strip())
    
    # URL encode both the target URL and the snippet
    encoded_url = quote(base_url, safe='')
    encoded_snippet = quote(clean_text)
    
    # Generate verification page URL
    # Note: In production, replace localhost:5000 with actual domain
    verify_base = "http://localhost:5000/verify"
    
    return f"{verify_base}?url={encoded_url}&snippet={encoded_snippet}"


def extract_unique_snippet(text: str, min_words: int = 3, max_words: int = 7) -> str:
    """
    Extract a unique snippet from text suitable for text fragments.
    
    Tries to find the most distinctive words to maximize match accuracy.
    
    Args:
        text: Full text to extract from
        min_words: Minimum words in snippet
        max_words: Maximum words in snippet
        
    Returns:
        Snippet suitable for text fragment URL
    """
    # Remove common filler words for better uniqueness
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    words = text.strip().split()
    
    # Find first sequence with at least one non-stopword
    best_start = 0
    for i in range(len(words)):
        if words[i].lower() not in stopwords:
            best_start = i
            break
    
    # Extract snippet starting from best position
    end_idx = min(best_start + max_words, len(words))
    snippet_words = words[best_start:end_idx]
    
    # Ensure minimum length
    while len(snippet_words) < min_words and best_start > 0:
        best_start -= 1
        snippet_words = words[best_start:end_idx]
    
    return ' '.join(snippet_words)
