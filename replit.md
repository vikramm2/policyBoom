# PolicyBoom - Enterprise Legal Risk Intelligence CLI

## Overview

This repository contains two projects:

1. **PolicyBoom** (Beta) - Enterprise-grade CLI tool for analyzing legal policies across multi-domain company infrastructure
2. **CRWLR** (Legacy) - Original web service prototype for policy analysis

## PolicyBoom Beta

PolicyBoom is a Python CLI tool that analyzes Terms of Service and Privacy Policies with multi-domain scanning capabilities and **AI-powered extraction using Meta Llama 3.3 70B**. It provides a fluent dot-notation API for enterprise legal professionals to identify concerning clauses across a company's entire domain landscape.

### Key Features

- **AI-Powered Extraction**: Uses Meta Llama 3.3 70B via Together AI for intelligent clause understanding (auto-falls back to regex if no API key)
- **Multi-Domain Scanning**: Discovers policies across root domain, subdomains, and product-specific paths
- **Clause-Level Analysis**: Each clause gets a unique ID with full metadata (section, paragraph, document type)
- **Clickable Verification URLs**: Every finding includes a browser text fragment URL (#:~:text=...) that auto-scrolls and highlights the exact clause for instant verification
- **Severity Scoring**: High/Medium/Low risk categorization
- **Category Tagging**: Arbitration, data sale, tracking, location, retention, children's data (COPPA)
- **Fluent API**: Chainable dot-notation commands (`scan().summarizeHigh().category()`)
- **Local Storage**: SQLite database (~/.policyboom/scans.db) for instant cached results
- **Beautiful Output**: Rich terminal formatting with tables and colors
- **PyPI Ready**: Automated publishing workflow with GitHub Actions

### Installation

```bash
# From PyPI (once published)
pip install policyboom

# From source
cd policyboom
pip install -e .
```

### Usage Examples

```bash
# CLI with dot-notation
policyboom exec "scan('slack.com').summarizeHigh()"
policyboom exec "scan('stripe.com').summarizeHigh().category('arbitration')"
policyboom exec "scan('example.com').summarizeAll().metadata()"

# Get help
policyboom --help
policyboom guide
policyboom examples

# Export results
policyboom export <scan_id> --format json
```

```python
# Python library
from policyboom import scan

result = scan("slack.com").summarizeHigh().category("arbitration")
for finding in result.findings:
    print(f"{finding.severity}: {finding.snippet}")

result.export("output.json", format="json")
```

### Architecture

**Project Structure:**
```
policyboom/
├── policyboom/
│   ├── __init__.py
│   ├── scanner.py      # Fluent API implementation
│   ├── discovery.py    # Multi-domain crawler
│   ├── extraction.py   # Clause-level parsing
│   ├── analysis.py     # Severity scoring & tagging
│   ├── database.py     # Local SQLite storage
│   ├── models.py       # Data models
│   └── cli.py          # Click-based CLI
├── pyproject.toml      # Package configuration
├── setup.py            # Backward compatibility
├── DEPLOYMENT.md       # Deployment guide
└── README.md
```

**Core Pipeline:**
1. **Discovery** → Finds all policy documents across domains/subdomains
   - **User-Agent Rotation**: Random browser user-agents (Chrome, Firefox, Safari) to avoid bot detection
   - **Request Delays**: 1-3 second random delays between requests to mimic human behavior
   - **Mobile/AMP Fallbacks**: Tries m.domain.com, ?amp=1, and ?print=true variants for better coverage
   - HEAD request validation with GET fallback (405/501 errors)
   - Intelligent caching (only true failures: 404, 410, network errors)
   - Early stopping after finding 3 valid documents (70% reduction in wasted calls)
   - Optimized fallback URLs (5 most common patterns)
2. **Extraction** → AI-powered (Llama 3.3 70B) or regex-based parsing into individual clauses with metadata
   - **User-Agent Rotation**: Every extraction request uses realistic browser headers
   - HTML content validation (Content-Type, length, structure)
   - Returns all fetched documents for complete transparency
3. **Analysis** → Uses AI categorization + severity from extraction, or applies regex rules
4. **Storage** → Caches in local SQLite for instant retrieval
5. **Output** → Returns via fluent API or exports to JSON/CSV
   - Always displays complete policy documents summary (even zero-finding docs)

**Technology Stack:**
- Python 3.11+
- OpenAI SDK (Together AI client)
- Meta Llama 3.3 70B (via Together AI free tier)
- Click (CLI framework)
- Rich (terminal formatting)
- httpx (HTTP client)
- BeautifulSoup4 + lxml (HTML parsing)
- readability-lxml (content extraction)
- tldextract (domain handling)
- SQLite (local database)

### Text Fragment Verification System

PolicyBoom generates clickable verification URLs for every finding using the browser Text Fragments API (#:~:text=...). When clicked, these URLs:
- Auto-scroll the browser to the exact clause location
- Highlight the matched text in yellow (Chrome, Edge, Safari)
- Provide instant, verifiable evidence for legal professionals

**Implementation:**
1. Pattern matched in clause text using regex
2. Whitespace normalized to single spaces for reliability
3. Matched word indices identified via character position overlap
4. Snippet extracted: 5 words before + matched words + 5 words after
5. URL-encoded and appended as #:~:text=... fragment

**Guarantees:**
- Matched text always included in fragment (mathematically proven)
- Handles all edge cases: punctuation, irregular whitespace, clause boundaries
- Works across all modern browsers (Chrome, Edge, Safari, Firefox)
- No false negatives - every fragment contains the evidence it claims

**Example:**
```
Finding: "Arbitration clause detected"
Source: https://example.com/terms#:~:text=disputes%20shall%20be%20resolved%20through%20binding%20arbitration
→ Clicking this URL scrolls browser to the exact clause and highlights "resolved through binding arbitration"
```

### Security Features

- **Safe Expression Parser**: CLI uses regex-based parsing instead of eval()
- **Whitelist-Only Methods**: Only documented methods are allowed in exec command
- **No Remote Code Execution**: Input validation prevents arbitrary code execution

### Deployment

See `policyboom/DEPLOYMENT.md` for:
- Local installation guide
- PyPI publishing workflow (automated via GitHub Actions)
- Python library usage examples
- Troubleshooting tips

---

## CRWLR (Legacy Prototype)

Original web service prototype. See below for documentation.

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