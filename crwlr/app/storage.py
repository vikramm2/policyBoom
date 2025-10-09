import sqlite3
import json
import time
import os


DB_PATH = os.getenv('CRWLR_DB_PATH', 'crwlr.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            url TEXT PRIMARY KEY,
            fetched_at INTEGER,
            title TEXT,
            raw_length INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_url TEXT,
            heading TEXT,
            text TEXT,
            tags_json TEXT,
            FOREIGN KEY (doc_url) REFERENCES documents(url)
        )
    ''')
    
    conn.commit()
    conn.close()


def store_document(url: str, title: str, raw_length: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    fetched_at = int(time.time())
    
    cursor.execute('''
        INSERT OR REPLACE INTO documents (url, fetched_at, title, raw_length)
        VALUES (?, ?, ?, ?)
    ''', (url, fetched_at, title, raw_length))
    
    conn.commit()
    conn.close()


def store_findings(doc_url: str, findings: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM findings WHERE doc_url = ?', (doc_url,))
    
    for finding in findings:
        cursor.execute('''
            INSERT INTO findings (doc_url, heading, text, tags_json)
            VALUES (?, ?, ?, ?)
        ''', (doc_url, finding['heading'], finding['text'], json.dumps(finding['tags'])))
    
    conn.commit()
    conn.close()


def get_cached_result(url: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT title FROM documents WHERE url = ?', (url,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    title = row[0]
    
    cursor.execute('SELECT heading, text, tags_json FROM findings WHERE doc_url = ?', (url,))
    findings_rows = cursor.fetchall()
    
    findings = []
    for heading, text, tags_json in findings_rows:
        tags = json.loads(tags_json)
        snippet = text[:500] if len(text) > 500 else text
        findings.append({
            'heading': heading,
            'text': text,
            'snippet': snippet,
            'tags': tags
        })
    
    conn.close()
    
    return {
        'url': url,
        'title': title,
        'cached': True,
        'findings': findings
    }
