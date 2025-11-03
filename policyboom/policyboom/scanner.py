"""Core scanner with fluent dot-notation API."""

from .models import Scan, ScanResult, Severity, Category, Finding
from .discovery import Discovery
from .extraction import Extraction
from .analysis import Analysis
from .database import Database
from datetime import datetime
import uuid
from typing import Optional


class ScanOperation:
    """Represents an ongoing scan operation with fluent API."""
    
    def __init__(self, domain: str, db: Optional[Database] = None):
        """Initialize scan operation."""
        self.domain = domain
        self.db = db or Database()
        self.scan_id = str(uuid.uuid4())
        self._findings = None
        self._scan = None
        self._executed = False
    
    def _execute(self):
        """Execute the scan if not already done."""
        if self._executed:
            return
        
        print(f"🔍 Scanning {self.domain}...")
        
        discovery = Discovery()
        extraction = Extraction()
        analysis = Analysis()
        
        try:
            policy_urls = discovery.discover(self.domain)
            print(f"📄 Found {len(policy_urls)} policy documents")
            
            scan = Scan(
                id=self.scan_id,
                domain=self.domain,
                created_at=datetime.now(),
                status="in_progress"
            )
            
            self.db.save_scan(scan)
            
            all_findings = []
            
            for policy in policy_urls:
                url = policy['url']
                doc_type = policy['doc_type']
                
                print(f"  📖 Extracting: {doc_type} ({url})")
                
                document = extraction.extract_document(url, doc_type)
                if not document:
                    continue
                
                doc_id = self.db.save_document(self.scan_id, document)
                
                for clause in document.clauses:
                    self.db.save_clause(doc_id, clause)
                    
                    findings = analysis.analyze_clause(clause)
                    for finding in findings:
                        self.db.save_finding(self.scan_id, finding)
                        all_findings.append(finding)
            
            scan.status = "completed"
            self.db.save_scan(scan)
            
            print(f"✅ Scan complete! Found {len(all_findings)} concerning clauses")
            
            self._scan = scan
            self._findings = all_findings
            self._executed = True
        
        finally:
            discovery.close()
            extraction.close()
    
    def summarizeHigh(self) -> 'FilteredScanOperation':
        """Filter to high severity findings only."""
        return FilteredScanOperation(self, severity=Severity.HIGH)
    
    def summarizeMedium(self) -> 'FilteredScanOperation':
        """Filter to medium severity findings only."""
        return FilteredScanOperation(self, severity=Severity.MEDIUM)
    
    def summarizeLow(self) -> 'FilteredScanOperation':
        """Filter to low severity findings only."""
        return FilteredScanOperation(self, severity=Severity.LOW)
    
    def summarizeAll(self) -> 'FilteredScanOperation':
        """Get all findings."""
        return FilteredScanOperation(self)
    
    def get_findings(self, severity: Optional[Severity] = None) -> list[Finding]:
        """Get findings with optional severity filter."""
        self._execute()
        
        if severity is None:
            return self._findings or []
        
        return [f for f in (self._findings or []) if f.severity == severity]


class FilteredScanOperation:
    """Represents a filtered scan operation."""
    
    def __init__(self, parent: ScanOperation, severity: Optional[Severity] = None):
        """Initialize filtered operation."""
        self.parent = parent
        self.severity_filter = severity
        self.category_filter = None
        self._result = None
    
    @property
    def findings(self) -> list[Finding]:
        """Get findings with current filters."""
        return self._get_filtered_findings()
    
    @property
    def result(self) -> ScanResult:
        """Get full scan result."""
        return self._execute_and_build_result()
    
    def category(self, category_name: str) -> 'FilteredScanOperation':
        """Filter by category."""
        try:
            cat = Category(category_name)
            self.category_filter = cat
        except ValueError:
            print(f"⚠️  Unknown category: {category_name}")
            print(f"Valid categories: {', '.join([c.value for c in Category])}")
        
        return self
    
    def findLinks(self) -> 'FilteredScanOperation':
        """Include source links (already included in findings)."""
        return self
    
    def metadata(self) -> dict:
        """Get metadata about the scan."""
        self.parent._execute()
        
        findings = self._get_filtered_findings()
        
        metadata = {
            'scan_id': self.parent.scan_id,
            'domain': self.parent.domain,
            'total_findings': len(findings),
            'severity_breakdown': self._get_severity_breakdown(findings),
            'category_breakdown': self._get_category_breakdown(findings),
        }
        
        return metadata
    
    def _get_filtered_findings(self) -> list[Finding]:
        """Get findings with current filters applied."""
        findings = self.parent.get_findings(self.severity_filter)
        
        if self.category_filter:
            findings = [f for f in findings if f.category == self.category_filter]
        
        return findings
    
    def _get_severity_breakdown(self, findings: list[Finding]) -> dict:
        """Get count by severity."""
        breakdown = {'high': 0, 'medium': 0, 'low': 0}
        for f in findings:
            breakdown[f.severity.value] += 1
        return breakdown
    
    def _get_category_breakdown(self, findings: list[Finding]) -> dict:
        """Get count by category."""
        breakdown = {}
        for f in findings:
            cat = f.category.value
            breakdown[cat] = breakdown.get(cat, 0) + 1
        return breakdown
    
    def _execute_and_build_result(self) -> ScanResult:
        """Execute scan and build result."""
        if self._result is not None:
            return self._result
        
        self.parent._execute()
        
        if self.parent._scan is None:
            raise ValueError("Scan execution failed")
        
        findings = self._get_filtered_findings()
        metadata = self.metadata()
        
        result = ScanResult(
            scan=self.parent._scan,
            findings=findings,
            metadata=metadata
        )
        
        self._result = result
        return result
    
    def __repr__(self) -> str:
        """String representation for terminal output."""
        result = self._execute_and_build_result()
        
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"PolicyBoom Scan Results - {result.scan.domain}")
        output.append(f"{'='*80}\n")
        
        output.append(f"Scan ID: {result.scan.id}")
        output.append(f"Total Findings: {len(result.findings)}")
        
        if self.severity_filter:
            output.append(f"Filtered by: {self.severity_filter.value.upper()} severity")
        if self.category_filter:
            output.append(f"Category: {self.category_filter.value}")
        
        output.append(f"\nSeverity Breakdown:")
        for sev, count in result.metadata['severity_breakdown'].items():
            output.append(f"  {sev.upper()}: {count}")
        
        output.append(f"\nCategory Breakdown:")
        for cat, count in result.metadata['category_breakdown'].items():
            output.append(f"  {cat}: {count}")
        
        if result.findings:
            output.append(f"\n{'─'*80}")
            output.append(f"Top Findings:\n")
            
            for i, finding in enumerate(result.findings[:10], 1):
                output.append(f"{i}. [{finding.severity.value.upper()}] {finding.matched_pattern}")
                output.append(f"   Section: {finding.section_title}")
                output.append(f"   Snippet: {finding.snippet[:150]}...")
                output.append(f"   URL: {finding.document_url}\n")
        
        output.append(f"{'='*80}\n")
        
        return '\n'.join(output)
    
    def export(self, filename: str, format: str = "json"):
        """Export results to file."""
        result = self._execute_and_build_result()
        result.export(filename, format)
        print(f"✅ Results exported to {filename}")


def scan(domain: str, db: Optional[Database] = None) -> ScanOperation:
    """
    Start a new scan operation with fluent API.
    
    Examples:
        scan("slack.com").summarizeHigh()
        scan("stripe.com").summarizeHigh().category("arbitration")
        scan("example.com").summarizeAll().metadata()
    """
    return ScanOperation(domain, db)
