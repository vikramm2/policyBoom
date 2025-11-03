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
    findings: list[dict] = field(default_factory=list)


@dataclass
class Finding:
    """Represents a concerning clause finding."""
    clause_id: str
    category: Category
    severity: Severity
    text: str
    snippet: str
    section_title: str
    document_url: str
    matched_pattern: str


@dataclass
class Document:
    """Represents a legal document."""
    url: str
    doc_type: str
    title: str
    last_updated: Optional[datetime]
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
        """Export results to file."""
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
                writer.writerow(["Clause ID", "Category", "Severity", "Section", "Snippet", "URL"])
                for finding in self.findings:
                    writer.writerow([
                        finding.clause_id,
                        finding.category.value,
                        finding.severity.value,
                        finding.section_title,
                        finding.snippet[:100],
                        finding.document_url,
                    ])
