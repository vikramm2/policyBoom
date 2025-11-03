#!/usr/bin/env python3
"""PolicyBoom CLI - Command-line interface for policy analysis."""

import ast
import re
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from policyboom import scan, __version__


console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__)
def main(ctx):
    """
    PolicyBoom - Enterprise Legal Risk Intelligence CLI
    
    Analyze Terms of Service and Privacy Policies with multi-domain scanning.
    
    Use dot-notation for powerful queries:
    
        policyboom exec "scan('slack.com').summarizeHigh()"
        policyboom exec "scan('stripe.com').summarizeHigh().category('arbitration')"
    """
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            "[bold cyan]PolicyBoom 💥[/bold cyan]\n\n"
            "Enterprise Legal Risk Intelligence CLI\n\n"
            "[dim]Use --help for commands[/dim]",
            border_style="cyan"
        ))


@main.command()
@click.argument('expression')
def exec(expression: str):
    """
    Execute a dot-notation scan expression.
    
    Examples:
    
        policyboom exec "scan('slack.com').summarizeHigh()"
        
        policyboom exec "scan('stripe.com').summarizeHigh().category('arbitration')"
        
        policyboom exec "scan('example.com').summarizeAll().metadata()"
    
    \b
    Available methods:
      .summarizeHigh()    - Filter to high severity findings
      .summarizeMedium()  - Filter to medium severity findings
      .summarizeLow()     - Filter to low severity findings
      .summarizeAll()     - Get all findings
      .category(name)     - Filter by category
      .metadata()         - Get scan metadata
      .findLinks()        - Include source links (default)
    
    \b
    Categories:
      arbitration, dataSale, tracking, location, retention, childrenData
    """
    try:
        console.print(f"\n[cyan]Executing:[/cyan] {expression}\n")
        
        result = _safe_eval_scan_expression(expression)
        
        if isinstance(result, dict):
            _print_metadata(result)
        else:
            console.print(result)
    
    except SyntaxError as e:
        console.print(f"[red]❌ Syntax error:[/red] {e}")
        console.print("[yellow]Make sure to use quotes properly:[/yellow]")
        console.print('  policyboom exec "scan(\'domain.com\').summarizeHigh()"')
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        console.print(f"[dim]{type(e).__name__}[/dim]")


@main.command()
def guide():
    """
    Interactive guide for first-time users.
    """
    guide_text = """
# PolicyBoom Quick Start Guide

## What is PolicyBoom?

PolicyBoom automatically discovers and analyzes legal policies (Terms of Service, Privacy Policies) 
from any company domain. It identifies concerning clauses and scores them by severity.

## Basic Usage

The primary command is `exec` which evaluates dot-notation expressions:

```bash
policyboom exec "scan('company.com').summarizeHigh()"
```

## Step-by-Step Example

1. **Scan a domain for high-severity issues:**
   ```bash
   policyboom exec "scan('slack.com').summarizeHigh()"
   ```

2. **Filter by specific category:**
   ```bash
   policyboom exec "scan('slack.com').summarizeHigh().category('arbitration')"
   ```

3. **Get all findings with metadata:**
   ```bash
   policyboom exec "scan('stripe.com').summarizeAll().metadata()"
   ```

4. **Export results:**
   ```bash
   policyboom export <scan_id> --format json
   ```

## Severity Levels

- **HIGH** - Immediate legal risk (forced arbitration, data sale, COPPA violations)
- **MEDIUM** - Compliance concerns (vague retention, tracking, location data)
- **LOW** - Best practice gaps (analytics, minor disclosures)

## Categories

- `arbitration` - Forced arbitration, class action waivers
- `dataSale` - Third-party data selling or sharing
- `tracking` - Cookies, pixels, behavioral tracking
- `location` - Location data collection
- `retention` - Data retention policies
- `childrenData` - Children's data (COPPA)

## Tips

- Always use quotes around the domain name
- Chain methods with dot-notation for filtering
- Results are cached locally in ~/.policyboom/scans.db
- Use `metadata()` to see summary statistics

For more help: `policyboom --help`
"""
    
    console.print(Markdown(guide_text))


@main.command()
def examples():
    """
    Show usage examples.
    """
    examples_text = """
# PolicyBoom Examples

## Basic Scans

**Scan for high-severity issues:**
```bash
policyboom exec "scan('slack.com').summarizeHigh()"
```

**Scan for all issues:**
```bash
policyboom exec "scan('stripe.com').summarizeAll()"
```

**Scan for medium-severity issues:**
```bash
policyboom exec "scan('example.com').summarizeMedium()"
```

## Filtered Scans

**Find arbitration clauses:**
```bash
policyboom exec "scan('company.com').summarizeHigh().category('arbitration')"
```

**Find data sale clauses:**
```bash
policyboom exec "scan('company.com').summarizeAll().category('dataSale')"
```

**Find tracking/analytics:**
```bash
policyboom exec "scan('company.com').summarizeMedium().category('tracking')"
```

## Metadata & Analysis

**Get scan metadata:**
```bash
policyboom exec "scan('company.com').summarizeAll().metadata()"
```

**Export results:**
```bash
policyboom export <scan_id> --format json
policyboom export <scan_id> --format csv
```

## Advanced Examples

**Compare severity levels:**
```bash
policyboom exec "scan('company.com').summarizeHigh().metadata()"
policyboom exec "scan('company.com').summarizeMedium().metadata()"
```

**Audit specific concerns:**
```bash
policyboom exec "scan('company.com').summarizeHigh().category('childrenData')"
```
"""
    
    console.print(Markdown(examples_text))


@main.command()
@click.argument('scan_id')
@click.option('--format', default='json', type=click.Choice(['json', 'csv']), help='Export format')
@click.option('--output', default=None, help='Output filename')
def export(scan_id: str, format: str, output: str):
    """
    Export scan results to file.
    
    Arguments:
        SCAN_ID - The ID of the scan to export
    
    Options:
        --format - json or csv (default: json)
        --output - Output filename (default: scan_<id>.<format>)
    """
    if output is None:
        output = f"scan_{scan_id[:8]}.{format}"
    
    try:
        from policyboom.database import Database
        db = Database()
        
        scan_obj = db.get_scan(scan_id)
        if not scan_obj:
            console.print(f"[red]❌ Scan not found:[/red] {scan_id}")
            return
        
        findings = db.get_findings(scan_id)
        
        if format == 'json':
            import json
            data = {
                'scan_id': scan_obj.id,
                'domain': scan_obj.domain,
                'created_at': scan_obj.created_at.isoformat(),
                'findings_count': len(findings),
                'findings': [
                    {
                        'clause_id': f.clause_id,
                        'category': f.category.value,
                        'severity': f.severity.value,
                        'section_title': f.section_title,
                        'snippet': f.snippet,
                        'document_url': f.document_url,
                    }
                    for f in findings
                ]
            }
            with open(output, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format == 'csv':
            import csv
            with open(output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Clause ID', 'Category', 'Severity', 'Section', 'Snippet', 'URL'])
                for finding in findings:
                    writer.writerow([
                        finding.clause_id,
                        finding.category.value,
                        finding.severity.value,
                        finding.section_title,
                        finding.snippet[:100],
                        finding.document_url,
                    ])
        
        console.print(f"[green]✅ Exported to:[/green] {output}")
        
        db.close()
    
    except Exception as e:
        console.print(f"[red]❌ Export failed:[/red] {e}")


def _safe_eval_scan_expression(expression: str):
    """
    Safely evaluate scan expression using simple parsing.
    Only allows scan() calls with method chaining.
    """
    if not expression.strip().startswith('scan('):
        raise ValueError("Expression must start with scan('domain.com')")
    
    domain_match = re.search(r"scan\(['\"]([^'\"]+)['\"]\)", expression)
    if not domain_match:
        raise ValueError("Could not extract domain from scan() call")
    
    domain = domain_match.group(1)
    
    result = scan(domain)
    
    chain = _extract_method_chain_from_expression(expression)
    
    for method_name, args in chain:
        if method_name == 'summarizeHigh':
            result = result.summarizeHigh()
        elif method_name == 'summarizeMedium':
            result = result.summarizeMedium()
        elif method_name == 'summarizeLow':
            result = result.summarizeLow()
        elif method_name == 'summarizeAll':
            result = result.summarizeAll()
        elif method_name == 'category':
            if args:
                result = result.category(args[0])
        elif method_name == 'metadata':
            return result.metadata()
        elif method_name == 'findLinks':
            result = result.findLinks()
        else:
            raise ValueError(f"Unknown method: {method_name}")
    
    return result


def _extract_method_chain_from_expression(expression: str) -> list[tuple[str, list]]:
    """Extract method chain from expression string."""
    import re
    
    methods = []
    
    pattern = r'\.(\w+)\(([^)]*)\)'
    matches = re.finditer(pattern, expression)
    
    for match in matches:
        method_name = match.group(1)
        args_str = match.group(2).strip()
        
        args = []
        if args_str:
            args_str = args_str.strip('\'"')
            args.append(args_str)
        
        methods.append((method_name, args))
    
    return methods


def _print_metadata(metadata: dict):
    """Print metadata in a formatted table."""
    console.print(f"\n[cyan]Scan Metadata:[/cyan]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Value")
    
    table.add_row("Scan ID", metadata.get('scan_id', 'N/A')[:16])
    table.add_row("Domain", metadata.get('domain', 'N/A'))
    table.add_row("Total Findings", str(metadata.get('total_findings', 0)))
    
    console.print(table)
    
    severity = metadata.get('severity_breakdown', {})
    if severity:
        console.print(f"\n[cyan]Severity Breakdown:[/cyan]")
        sev_table = Table(show_header=True, header_style="bold cyan")
        sev_table.add_column("Severity")
        sev_table.add_column("Count")
        
        for level, count in severity.items():
            sev_table.add_row(level.upper(), str(count))
        
        console.print(sev_table)
    
    categories = metadata.get('category_breakdown', {})
    if categories:
        console.print(f"\n[cyan]Category Breakdown:[/cyan]")
        cat_table = Table(show_header=True, header_style="bold cyan")
        cat_table.add_column("Category")
        cat_table.add_column("Count")
        
        for cat, count in categories.items():
            cat_table.add_row(cat, str(count))
        
        console.print(cat_table)
    
    console.print()


if __name__ == '__main__':
    main()
