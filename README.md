# policyBoom - Terms & Privacy Policy Analyzer

## Overview

policyBoom is a web service that automatically discovers, fetches, and analyzes Terms of Service and Privacy Policy pages from websites. Given a seed URL, the system crawls the same domain to find policy documents, extracts their content, and identifies concerning clauses using pattern-based rules. The service is designed for resilience - network failures, timeouts, or malformed pages never crash the service. Results are cached in SQLite for performance.


## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **FastAPI** serves as the web framework with automatic OpenAPI documentation
- **Uvicorn** ASGI server handles HTTP requests
- Static file serving for a minimal demo UI at `/static/index.html`

### Core Processing Pipeline

The system follows a 4-stage pipeline:

1. **Discovery** (`crawler.py`): 
   - Finds policy-related URLs by scraping anchor tags from the seed page
   - Filters links to same registrable domain using `tldextract`
   - Adds fallback URLs (`/privacy`, `/terms`, etc.) to ensure coverage
   - Limits discovery to `CRWLR_MAX_DOCS` documents (default: 4)

2. **Fetching** (`crawler.py`):
   - HTTP requests with configurable timeout (default: 15s)
   - User-agent string configurable via `CRWLR_UA`
   - Response size limited to `CRWLR_MAX_BYTES` (default: 1MB)
   - Graceful error handling with categorized failures (timeout, 4xx, 5xx, network, parse)

3. **Extraction** (`extract.py`):
   - Uses `readability-lxml` to extract main content from noisy HTML
   - Sections content by headings (h1-h4) with associated paragraph/list text
   - BeautifulSoup with lxml parser for DOM traversal
   - Prioritizes semantic containers (main, article, #content, .content)

4. **Analysis** (`analyze.py`):
   - Rule-based pattern matching using regex against lowercased text
   - Extensible "rule packs" system (currently: 'base' pack with 6 rules)
   - Tags sections with findings: data_sale, arbitration, tracking, location, retention, children
   - Severity levels: low, medium, high

### Data Storage

- **SQLite database** for caching analyzed documents
- Two tables:
  - `documents`: Stores URL, fetch timestamp, title, content length
  - `findings`: Stores section headings, text, and JSON-serialized tags
- Database path configurable via `CRWLR_DB_PATH` (default: `crwlr.db`)
- Cache-aware API responses include `cached: true/false` flag

### API Design

**Primary endpoint**: `GET /analyze`
- Query params: `url` (required), `packs` (optional, comma-separated)
- Returns: seed URL, discovered policy links, results array, errors array
- Response model uses Pydantic for validation and automatic schema generation

**Models**:
- `AnalyzeResponse`: Top-level response with seed, policy_links, results, errors
- `Result`: Per-document findings with URL, title, cached flag, findings list
- `Finding`: Section-level with heading, text, snippet (truncated), tags
- `ErrorItem`: Failed URLs with categorized failure reason
- `Tag`: Rule match with id, label, severity

### Utility Functions

**Domain validation** (`utils.py`):
- `same_registrable_domain()`: Compares registrable domains (handles subdomains)
- `is_probable_policy_path()`: Keyword matching for policy-related paths
- `absolutize()`: Resolves relative URLs using `urllib.parse.urljoin`
- `clean_text()`: Normalizes whitespace in extracted text

### Configuration via Environment Variables

- `CRWLR_TIMEOUT_SECONDS`: HTTP request timeout (default: 15)
- `CRWLR_MAX_DOCS`: Maximum policy documents to analyze (default: 4)
- `CRWLR_UA`: User-agent string for requests
- `CRWLR_MAX_BYTES`: Maximum response size (default: 1MB)
- `CRWLR_DB_PATH`: SQLite database location (default: crwlr.db)

### Error Handling Strategy

The system categorizes failures into 5 types:
- **timeout**: Request exceeded time limit
- **http_4xx**: Client errors (404, 403, etc.)
- **http_5xx**: Server errors
- **network**: Connection failures, DNS errors
- **parse**: HTML parsing failures

All errors are captured and returned in the `errors` array - the service never crashes on individual document failures.

## External Dependencies

### Python Libraries
- **fastapi==0.115.0**: Web framework with async support
- **uvicorn==0.30.6**: ASGI server
- **requests==2.32.3**: HTTP client for fetching pages
- **beautifulsoup4==4.12.3**: HTML parsing and DOM traversal
- **lxml==5.3.0**: Fast XML/HTML parser backend for BeautifulSoup
- **readability-lxml==0.8.1**: Content extraction from noisy web pages
- **tldextract==5.1.2**: Domain/subdomain parsing and comparison
- **pytest==8.3.3**: Testing framework

### Storage
- **SQLite 3**: Embedded database for caching (no external service required)

### Testing Infrastructure
- Test fixtures include sample HTML documents (minimal and Chrome-style formatting)
- Tests cover: API endpoints, domain filtering, rule matching, fallback URL generation
- Uses FastAPI's TestClient for integration testing
