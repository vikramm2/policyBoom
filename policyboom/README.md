# PolicyBoom 💥

> Enterprise legal risk intelligence CLI for analyzing Terms of Service and Privacy Policies

PolicyBoom automatically discovers, analyzes, and scores concerning legal clauses across multi-domain company policies using a fluent dot-notation API.

## Quick Start

```bash
# Install
pip install policyboom

# Scan a company's policies
policyboom exec "scan('slack.com').summarizeHigh()"

# Filter by category
policyboom exec "scan('stripe.com').summarizeHigh().category('arbitration')"

# Get all findings
policyboom exec "scan('example.com').summarizeAll()"
```

## Features

- 🌐 **Multi-Domain Scanning** - Discovers policies across root domain, subdomains, and product paths
- 🔍 **Clause-Level Analysis** - Extracts individual clauses with unique IDs and metadata
- ⚖️ **Severity Scoring** - Categorizes findings as High, Medium, or Low risk
- 🏷️ **Category Tagging** - Identifies arbitration waivers, data sale, tracking, COPPA violations, etc.
- 🔗 **Clickable Verification** - Source URLs with text fragments auto-scroll and highlight clauses in browser
- 📅 **Policy Dating** - Automatically extracts "last updated" dates from documents
- 💾 **Local Storage** - SQLite database for caching results (no cloud required)
- ✨ **Beautiful Output** - Rich terminal formatting with colors and tables
- 🔄 **Fluent API** - Chain commands with dot-notation for powerful queries

## Installation

```bash
pip install policyboom
```

## Usage

### CLI with Dot-Notation

The primary interface uses a fluent camelCase API:

```bash
# Basic scan
policyboom exec "scan('company.com').summarizeHigh()"

# Filter by severity and category
policyboom exec "scan('slack.com').summarizeMedium().category('dataSharing')"

# Get metadata with policy URLs and dates
policyboom exec "scan('stripe.com').summarizeAll().metadata()"

# Get full evidence for legal documentation
policyboom exec "scan('example.com').summarizeHigh().withEvidence()"

# Get detailed findings with all metadata
policyboom exec "scan('slack.com').summarizeAll().detailed()"
```

### As a Python Library

```python
from policyboom import scan

# Scan and analyze
result = scan("slack.com").summarizeHigh().category("arbitration")

# Access findings
for finding in result.findings:
    print(f"{finding.severity}: {finding.text}")
    
# Export results
result.export("output.json", format="json")
```

## Categories

PolicyBoom identifies these concerning clause types:

- `arbitration` - Forced arbitration / class action waivers
- `dataSale` - Third-party data selling
- `tracking` - Advertising and behavioral tracking
- `location` - Location data collection
- `retention` - Data retention policies
- `childrenData` - Children's data handling (COPPA)

## Commands

```bash
# Get help
policyboom --help

# Run interactive guide
policyboom guide

# View examples
policyboom examples

# Export scan results
policyboom export <scan_id> --format json
```

## Development

```bash
# Clone repository
git clone https://github.com/policyboom/policyboom
cd policyboom

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://policyboom.dev
- Issues: https://github.com/policyboom/policyboom/issues
- Discussions: https://github.com/policyboom/policyboom/discussions
