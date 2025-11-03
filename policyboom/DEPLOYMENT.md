# PolicyBoom Deployment Guide

## Local Installation & Usage

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation from Source

1. **Clone the repository**
```bash
git clone <your-repository-url>
cd policyboom
```

2. **Install in development mode**
```bash
pip install -e .
```

3. **Verify installation**
```bash
policyboom --version
policyboom --help
```

### Installation from PyPI (Once Published)

```bash
pip install policyboom
```

## Basic Usage

### CLI Commands

**Get help:**
```bash
policyboom --help
policyboom guide
policyboom examples
```

**Run a scan:**
```bash
policyboom exec "scan('slack.com').summarizeHigh()"
policyboom exec "scan('stripe.com').summarizeHigh().category('arbitration')"
policyboom exec "scan('example.com').summarizeAll().metadata()"
```

**Export results:**
```bash
policyboom export <scan_id> --format json
policyboom export <scan_id> --format csv --output myreport.csv
```

### Python Library Usage

```python
from policyboom import scan

# Run a scan
result = scan("slack.com").summarizeHigh()

# Access findings
for finding in result.findings:
    print(f"{finding.severity}: {finding.matched_pattern}")
    print(f"Section: {finding.section_title}")
    print(f"Snippet: {finding.snippet}\n")

# Get metadata
metadata = scan("stripe.com").summarizeAll().metadata()
print(f"Total findings: {metadata['total_findings']}")

# Export results
result.export("output.json", format="json")
```

## Database

PolicyBoom uses a local SQLite database to cache scan results. The database is stored at:
```
~/.policyboom/scans.db
```

This allows instant retrieval of previously scanned domains without re-crawling.

## Publishing to PyPI

### One-Time Setup

1. **Create PyPI account** at https://pypi.org

2. **Generate API token:**
   - Go to Account Settings → API Tokens
   - Create a new token with "Entire account" scope
   - Save the token securely (starts with `pypi-`)

3. **Add token to GitHub Secrets:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Create new secret named `PYPI_API_TOKEN`
   - Paste your PyPI API token

### Automated Publishing

The GitHub Actions workflow automatically publishes to PyPI when you create a release:

1. **Update version in pyproject.toml:**
```toml
[project]
version = "0.2.0"  # Increment version
```

2. **Commit and push changes:**
```bash
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push origin main
```

3. **Create a new release on GitHub:**
```bash
git tag v0.2.0
git push origin v0.2.0
```

Or use GitHub's web interface:
- Go to Releases → Draft a new release
- Tag: `v0.2.0`
- Title: `Release 0.2.0`
- Description: List of changes
- Click "Publish release"

4. **Automatic deployment:**
The GitHub Action will automatically build and publish to PyPI when the release is created.

### Manual Publishing

If you prefer to publish manually:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

You'll be prompted for your PyPI username (`__token__`) and API token.

### Test PyPI (Optional)

To test publishing before going to production PyPI:

```bash
twine upload --repository testpypi dist/*
```

Then install from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ policyboom
```

## Troubleshooting

### Python Version Issues
If you get errors about Python version, ensure you're using Python 3.11+:
```bash
python --version
```

### Missing Dependencies
If packages are missing, reinstall:
```bash
pip install -e ".[dev]"
```

### Database Errors
If you encounter database issues, you can reset the local database:
```bash
rm ~/.policyboom/scans.db
```

### Import Errors
Make sure you installed in editable mode and the package is on your Python path:
```bash
pip show policyboom
```

## Development

### Running Tests (Future)
```bash
pytest
```

### Code Formatting
```bash
black policyboom/
ruff check policyboom/
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/policyboom/policyboom/issues
- Documentation: https://policyboom.dev
