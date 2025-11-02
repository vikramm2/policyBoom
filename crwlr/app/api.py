import time
import os
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests

from .crawler import discover_policy_links, fetch, CRWLR_MAX_DOCS
from .extract import extract_main_content, sectionize
from .analyze import analyze_sections
from .storage import init_db, store_document, store_findings, get_cached_result


app = FastAPI(
    title="CRWLR - Terms & Privacy Policy Analyzer",
    description="Discovers and analyzes Terms of Service and Privacy Policy pages",
    version="0.1.0"
)

STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class Tag(BaseModel):
    id: str
    label: str
    severity: Literal["low", "medium", "high"]


class Finding(BaseModel):
    heading: str
    text: str
    snippet: str
    tags: list[Tag]


class Result(BaseModel):
    url: str
    title: str
    cached: bool | None = None
    findings: list[Finding]


class ErrorItem(BaseModel):
    url: str
    reason: Literal["timeout", "http_4xx", "http_5xx", "network", "parse"]


class AnalyzeResponse(BaseModel):
    seed: str
    policy_links: list[str]
    results: list[Result]
    errors: list[ErrorItem]
    skipped_due_to_robots: list[str] | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/analyze", response_model=AnalyzeResponse)
async def analyze(
    url: str = Query(..., description="Seed URL to analyze"),
    packs: str = Query("base", description="Comma-separated rule packs"),
    respect_robots: bool = Query(False, description="Respect robots.txt"),
    persist: bool = Query(False, description="Persist results to database"),
    audit: bool = Query(False, description="Enable audit logging")
):
    if persist:
        init_db()
    
    pack_list = [p.strip() for p in packs.split(',')]
    
    policy_links = discover_policy_links(url)
    
    results = []
    errors = []
    skipped_due_to_robots = []
    
    for link in policy_links[:CRWLR_MAX_DOCS]:
        if persist:
            cached = get_cached_result(link)
            if cached:
                results.append(cached)
                continue
        
        retry_delays = [0.5, 1.5]
        success = False
        
        for attempt in range(3):
            try:
                resp = fetch(link)
                
                soup = BeautifulSoup(resp.text, 'lxml')
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else link
                
                main_content = extract_main_content(resp.text)
                sections = sectionize(main_content)
                findings = analyze_sections(sections, pack_list)
                
                result = {
                    'url': link,
                    'title': title,
                    'cached': False,
                    'findings': findings
                }
                
                if persist:
                    store_document(link, title, len(resp.text))
                    store_findings(link, findings)
                
                results.append(result)
                success = True
                break
                
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                else:
                    errors.append({'url': link, 'reason': 'timeout'})
                    break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code >= 500:
                    errors.append({'url': link, 'reason': 'http_5xx'})
                else:
                    errors.append({'url': link, 'reason': 'http_4xx'})
                break
            except requests.exceptions.RequestException:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                else:
                    errors.append({'url': link, 'reason': 'network'})
                    break
            except Exception:
                errors.append({'url': link, 'reason': 'parse'})
                break
    
    return AnalyzeResponse(
        seed=url,
        policy_links=policy_links,
        results=results,
        errors=errors,
        skipped_due_to_robots=skipped_due_to_robots if respect_robots else None
    )
