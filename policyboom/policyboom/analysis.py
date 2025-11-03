"""Severity analysis and category tagging engine."""

import re
from .models import Clause, Finding, Severity, Category
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
        
        Returns list of findings.
        """
        findings = []
        text_lower = clause.text.lower()
        
        for rule in self.rules:
            match = rule.pattern.search(text_lower)
            if match:
                snippet = self._extract_snippet(clause.text, match.start(), match.end())
                
                finding = Finding(
                    clause_id=clause.id,
                    category=rule.category,
                    severity=rule.severity,
                    text=clause.text,
                    snippet=snippet,
                    section_title=clause.section_title,
                    document_url=clause.document_url,
                    matched_pattern=rule.label
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
