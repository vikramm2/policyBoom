"""SQLite database layer for local storage."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import Scan, Document, Clause, Finding, Severity, Category


class Database:
    """Local SQLite database for caching scans."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            home = Path.home()
            db_dir = home / ".policyboom"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "scans.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                url TEXT NOT NULL,
                doc_type TEXT,
                title TEXT,
                last_updated TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clauses (
                id TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                section_title TEXT,
                paragraph_index INTEGER,
                document_url TEXT,
                document_type TEXT,
                last_updated TEXT,
                context_before TEXT,
                context_after TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clause_id TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                text TEXT NOT NULL,
                snippet TEXT,
                section_title TEXT,
                document_url TEXT,
                matched_pattern TEXT,
                document_type TEXT,
                paragraph_number INTEGER,
                full_text TEXT,
                context_before TEXT,
                context_after TEXT,
                last_updated TEXT,
                FOREIGN KEY (clause_id) REFERENCES clauses(id),
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_domain ON scans(domain)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_category ON findings(category)
        """)
        
        self._migrate_schema(cursor)
        
        self.conn.commit()
    
    def _migrate_schema(self, cursor):
        """Add new columns to existing tables if they don't exist."""
        try:
            cursor.execute("PRAGMA table_info(clauses)")
            clause_columns = {row[1] for row in cursor.fetchall()}
            
            if 'document_type' not in clause_columns:
                cursor.execute("ALTER TABLE clauses ADD COLUMN document_type TEXT")
            if 'last_updated' not in clause_columns:
                cursor.execute("ALTER TABLE clauses ADD COLUMN last_updated TEXT")
            if 'context_before' not in clause_columns:
                cursor.execute("ALTER TABLE clauses ADD COLUMN context_before TEXT")
            if 'context_after' not in clause_columns:
                cursor.execute("ALTER TABLE clauses ADD COLUMN context_after TEXT")
            
            cursor.execute("PRAGMA table_info(findings)")
            finding_columns = {row[1] for row in cursor.fetchall()}
            
            if 'document_type' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN document_type TEXT")
            if 'paragraph_number' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN paragraph_number INTEGER")
            if 'full_text' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN full_text TEXT")
            if 'context_before' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN context_before TEXT")
            if 'context_after' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN context_after TEXT")
            if 'last_updated' not in finding_columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN last_updated TEXT")
        except Exception as e:
            pass
    
    def save_scan(self, scan: Scan):
        """Save a scan to the database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO scans (id, domain, created_at, status, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            scan.id,
            scan.domain,
            scan.created_at.isoformat(),
            scan.status,
            json.dumps({})
        ))
        
        self.conn.commit()
    
    def save_document(self, scan_id: str, document: Document) -> int:
        """Save a document and return its ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (scan_id, url, doc_type, title, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (
            scan_id,
            document.url,
            document.doc_type,
            document.title,
            document.last_updated
        ))
        
        self.conn.commit()
        doc_id = cursor.lastrowid
        if doc_id is None:
            raise ValueError("Failed to save document")
        return doc_id
    
    def save_clause(self, document_id: int, clause: Clause):
        """Save a clause to the database with full evidence."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO clauses 
            (id, document_id, text, section_title, paragraph_index, document_url,
             document_type, last_updated, context_before, context_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clause.id,
            document_id,
            clause.text,
            clause.section_title,
            clause.paragraph_index,
            clause.document_url,
            clause.document_type,
            clause.last_updated,
            clause.context_before,
            clause.context_after
        ))
        
        self.conn.commit()
    
    def save_finding(self, scan_id: str, finding: Finding):
        """Save a finding to the database with full evidence and metadata."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO findings 
            (clause_id, scan_id, category, severity, text, snippet, 
             section_title, document_url, matched_pattern, document_type,
             paragraph_number, full_text, context_before, context_after, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding.clause_id,
            scan_id,
            finding.category.value,
            finding.severity.value,
            finding.text,
            finding.snippet,
            finding.section_title,
            finding.document_url,
            finding.matched_pattern,
            finding.document_type,
            finding.paragraph_number,
            finding.full_text,
            finding.context_before,
            finding.context_after,
            finding.last_updated
        ))
        
        self.conn.commit()
    
    def get_scan(self, scan_id: str) -> Optional[Scan]:
        """Retrieve a scan by ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        scan = Scan(
            id=row['id'],
            domain=row['domain'],
            created_at=datetime.fromisoformat(row['created_at']),
            status=row['status']
        )
        
        return scan
    
    def get_findings(
        self, 
        scan_id: str, 
        severity: Optional[Severity] = None,
        category: Optional[Category] = None
    ) -> list[Finding]:
        """Retrieve findings for a scan with optional filters, including all evidence."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM findings WHERE scan_id = ?"
        params = [scan_id]
        
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        
        if category:
            query += " AND category = ?"
            params.append(category.value)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        findings = []
        for row in rows:
            findings.append(Finding(
                clause_id=row['clause_id'],
                category=Category(row['category']),
                severity=Severity(row['severity']),
                text=row['text'],
                snippet=row['snippet'],
                section_title=row['section_title'],
                document_url=row['document_url'],
                matched_pattern=row['matched_pattern'],
                document_type=row['document_type'] or "Unknown",
                paragraph_number=row['paragraph_number'] or 0,
                full_text=row['full_text'] or row['text'],
                context_before=row['context_before'] or "",
                context_after=row['context_after'] or "",
                last_updated=row['last_updated']
            ))
        
        return findings
    
    def close(self):
        """Close database connection."""
        self.conn.close()
