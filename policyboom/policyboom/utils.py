"""Utility functions for PolicyBoom."""

import re
from urllib.parse import quote


def generate_text_fragment_url(base_url: str, text: str, max_words: int = 5) -> str:
    """
    Generate a URL with text fragment that auto-scrolls browsers to specific text.
    
    Text fragments use the #:~:text= syntax which makes modern browsers:
    1. Scroll to the matching text
    2. Highlight it in yellow
    
    Args:
        base_url: The base URL of the document
        text: The full text to create fragment from
        max_words: Maximum words to use in fragment (default 5)
    
    Returns:
        URL with text fragment appended
        
    Example:
        >>> generate_text_fragment_url(
        ...     "https://example.com/policy",
        ...     "Users agree to binding arbitration"
        ... )
        'https://example.com/policy#:~:text=users%20agree%20to%20binding%20arbitration'
    """
    # Clean and normalize text
    clean_text = re.sub(r'\s+', ' ', text.strip())
    
    # Extract unique, identifying snippet (first N words)
    words = clean_text.split()[:max_words]
    fragment_text = ' '.join(words)
    
    # Lowercase for better matching
    fragment_text = fragment_text.lower()
    
    # URL encode the fragment
    encoded_fragment = quote(fragment_text)
    
    # Remove any existing fragments from base URL
    base_url = base_url.split('#')[0]
    
    # Append text fragment
    return f"{base_url}#:~:text={encoded_fragment}"


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
