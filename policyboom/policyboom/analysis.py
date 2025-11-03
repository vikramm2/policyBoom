"""Severity analysis and category tagging engine."""

import re
from .models import Clause, Finding, Severity, Category
from .utils import generate_text_fragment_url
from typing import Optional


class RulePattern:
    """A single analysis rule pattern."""
    
    def __init__(self, category: Category, severity: Severity, pattern: str, label: str):
        self.category = category
        self.severity = severity
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.label = label


class Analysis:
    """Analyzes clauses for concerning legal patterns."""
    
    def __init__(self):
        """Initialize analysis engine with rule patterns."""
        self.rules = self._load_rules()
    
    def _load_rules(self) -> list[RulePattern]:
        """Load analysis rule patterns."""
        rules = [
            RulePattern(
                Category.ARBITRATION,
                Severity.HIGH,
                r'(arbitration|waive.*class action|waive.*jury trial|binding arbitration)',
                'Forced arbitration or class action waiver'
            ),
            RulePattern(
                Category.DATA_SALE,
                Severity.HIGH,
                r'(sell.*information|monetize.*data|share.*third.{0,20}parties|disclose.*data.*partners)',
                'Data sale or third-party sharing'
            ),
            RulePattern(
                Category.TRACKING,
                Severity.MEDIUM,
                r'(track|cookies|web beacon|pixel|analytics|advertising.*identifier)',
                'Tracking and advertising technology'
            ),
            RulePattern(
                Category.LOCATION,
                Severity.MEDIUM,
                r'(location.*data|geolocation|gps|precise.*location)',
                'Location data collection'
            ),
            RulePattern(
                Category.RETENTION,
                Severity.MEDIUM,
                r'(retain.*data|keep.*information|storage.*period|data.*retention)',
                'Data retention policy'
            ),
            RulePattern(
                Category.CHILDREN_DATA,
                Severity.HIGH,
                r'(children.*data|coppa|under.*13|minors.*information|parental consent)',
                "Children's data handling (COPPA)"
            ),
            RulePattern(
                Category.DATA_SALE,
                Severity.HIGH,
                r'(without.*notice|without.*consent).*(?:data|information)',
                'Data use without consent'
            ),
            RulePattern(
                Category.ARBITRATION,
                Severity.HIGH,
                r'(cannot.*sue|may not.*bring.*claim|waive.*right.*court)',
                'Litigation rights waiver'
            ),
            RulePattern(
                Category.TRACKING,
                Severity.LOW,
                r'(google.*analytics|facebook.*pixel|third.{0,10}party.*analytics)',
                'Third-party analytics'
            ),
        ]
        
        return rules
    
    def analyze_clause(self, clause: Clause) -> list[Finding]:
        """
        Analyze a single clause for concerning patterns.
        
        Returns list of findings with full evidence and metadata.
        """
        findings = []
        text_lower = clause.text.lower()
        
        for rule in self.rules:
            match = rule.pattern.search(text_lower)
            if match:
                snippet = self._extract_snippet(clause.text, match.start(), match.end())
                
                # Generate text fragment URL using the matched text for precise targeting
                # Guarantee matched text is included by centering on it
                import re as snippet_re
                
                # Normalize whitespace in the entire clause first
                normalized_text = snippet_re.sub(r'\s+', ' ', clause.text)
                
                # Find the match in the normalized text
                normalized_match = rule.pattern.search(normalized_text.lower())
                if normalized_match:
                    # Get the matched substring
                    matched_substring = normalized_text[normalized_match.start():normalized_match.end()]
                    
                    # Split clause into words
                    words = normalized_text.split()
                    
                    # Find which words contain or surround the match
                    char_pos = 0
                    match_word_start = 0
                    match_word_end = len(words)
                    
                    for i, word in enumerate(words):
                        word_start = char_pos
                        word_end = char_pos + len(word)
                        
                        # If this word overlaps with match start
                        if word_start <= normalized_match.start() < word_end:
                            match_word_start = i
                        
                        # If this word overlaps with match end
                        if word_start < normalized_match.end() <= word_end:
                            match_word_end = i + 1
                            break
                        
                        char_pos = word_end + 1  # +1 for space
                    
                    # Take 5 words before match, the matched words, and 5 words after
                    context_words = 5
                    snippet_start_word = max(0, match_word_start - context_words)
                    snippet_end_word = min(len(words), match_word_end + context_words)
                    
                    # Build snippet centered on matched words
                    unique_snippet = ' '.join(words[snippet_start_word:snippet_end_word])
                else:
                    # Fallback: use first 10 words
                    unique_snippet = ' '.join(normalized_text.split()[:10])
                
                fragment_url = generate_text_fragment_url(clause.document_url, unique_snippet)
                
                finding = Finding(
                    clause_id=clause.id,
                    category=rule.category,
                    severity=rule.severity,
                    text=clause.text,
                    snippet=snippet,
                    section_title=clause.section_title,
                    document_url=fragment_url,
                    matched_pattern=rule.label,
                    document_type=clause.document_type,
                    full_text=clause.text,
                    context_before=clause.context_before,
                    context_after=clause.context_after,
                    last_updated=clause.last_updated
                )
                
                findings.append(finding)
        
        return findings
    
    def _extract_snippet(self, text: str, start: int, end: int, context: int = 100) -> str:
        """Extract a snippet of text around a match."""
        snippet_start = max(0, start - context)
        snippet_end = min(len(text), end + context)
        
        snippet = text[snippet_start:snippet_end]
        
        if snippet_start > 0:
            snippet = '...' + snippet
        if snippet_end < len(text):
            snippet = snippet + '...'
        
        return snippet.strip()
