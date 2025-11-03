"""Data models for PolicyBoom."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    """Severity levels for findings."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    """Categories of concerning clauses."""
    ARBITRATION = "arbitration"
    DATA_SALE = "dataSale"
    TRACKING = "tracking"
    LOCATION = "location"
    RETENTION = "retention"
    CHILDREN_DATA = "childrenData"


@dataclass
class Clause:
    """Represents a single clause in a legal document."""
    id: str
    text: str
    section_title: str
    paragraph_index: int
    document_url: str
    document_type: str = "Unknown"
    last_updated: Optional[str] = None
    context_before: str = ""
    context_after: str = ""
    findings: list[dict] = field(default_factory=list)


@dataclass
class Finding:
    """Represents a concerning clause finding with full evidence and source attribution.
    
    The document_url includes text fragment (#:~:text=...) for browser auto-scroll and highlighting.
    """
    clause_id: str
    category: Category
    severity: Severity
    text: str
    snippet: str
    section_title: str
    document_url: str
    matched_pattern: str
    document_type: str = "Unknown"
    full_text: str = ""
    context_before: str = ""
    context_after: str = ""
    last_updated: Optional[str] = None


@dataclass
class Document:
    """Represents a legal document."""
    url: str
    doc_type: str
    title: str
    last_updated: Optional[str] = None
    clauses: list[Clause] = field(default_factory=list)


@dataclass
class Scan:
    """Represents a complete scan of a domain."""
    id: str
    domain: str
    created_at: datetime
    status: str
    documents: list[Document] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


@dataclass
class ScanResult:
    """Result object returned by scanner operations."""
    scan: Scan
    findings: list[Finding]
    metadata: dict
    
    def export(self, filename: str, format: str = "json"):
        """Export results to file with full evidence and metadata."""
        import json
        
        if format == "json":
            data = {
                "scan_id": self.scan.id,
                "domain": self.scan.domain,
                "created_at": self.scan.created_at.isoformat(),
                "findings_count": len(self.findings),
                "findings": [
                    {
                        "clause_id": f.clause_id,
                        "category": f.category.value,
                        "severity": f.severity.value,
                        "text": f.text,
                        "snippet": f.snippet,
                        "section_title": f.section_title,
                        "document_url": f.document_url,
                        "document_type": f.document_type,
                        "full_text": f.full_text,
                        "context_before": f.context_before,
                        "context_after": f.context_after,
                        "last_updated": f.last_updated,
                        "matched_pattern": f.matched_pattern,
                    }
                    for f in self.findings
                ],
                "metadata": self.metadata,
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Clause ID", "Category", "Severity", "Section",
                    "Document Type", "Snippet", "Full Text", "URL", "Last Updated"
                ])
                for finding in self.findings:
                    writer.writerow([
                        finding.clause_id,
                        finding.category.value,
                        finding.severity.value,
                        finding.section_title,
                        finding.document_type,
                        finding.snippet[:100],
                        finding.full_text[:200] if finding.full_text else "",
                        finding.document_url,
                        finding.last_updated or "Unknown",
                    ])
