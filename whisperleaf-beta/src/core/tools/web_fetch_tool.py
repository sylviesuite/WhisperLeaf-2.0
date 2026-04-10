"""
web.fetch tool: fetch a URL or run a DuckDuckGo HTML search and return plain text.
All processing is local. The network request is user-initiated and goes to the
target server directly — no data is forwarded to any external AI service.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# Max chars to return as context (keeps the LLM prompt manageable)
WEB_CONTEXT_MAX_CHARS = 6_000
DDGO_SEARCH_URL = "https://html.duckduckgo.com/html/"
DEFAULT_TIMEOUT = 15.0

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


async def _fetch_ddgo_search(query: str) -> str:
    """
    Fetch DuckDuckGo HTML search results for a query and return plain-text snippets.
    No JS required; returns the top result titles + snippets.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise RuntimeError("beautifulsoup4 is not installed.")

    params = urlencode({"q": query, "kl": "us-en"})
    url = f"{DDGO_SEARCH_URL}?{params}"
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    from ..url_ingest import _build_ssl_context
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True, verify=_build_ssl_context()) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    results = []
    for r in soup.select(".result"):
        title_el = r.select_one(".result__title")
        snippet_el = r.select_one(".result__snippet")
        url_el = r.select_one(".result__url")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        result_url = url_el.get_text(strip=True) if url_el else ""
        if title or snippet:
            line = f"[{title}]" if title else ""
            if result_url:
                line += f" ({result_url})"
            if snippet:
                line += f"\n{snippet}"
            results.append(line.strip())
        if len(results) >= 8:
            break

    if not results:
        return "No results found."
    return "\n\n".join(results)


async def _web_fetch_handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for web.fetch tool.
    Accepts either:
      - {"url": "https://..."} → fetch and extract plain text from that URL
      - {"query": "some search terms"} → DuckDuckGo HTML search, return snippets
    Returns {"text": str, "title": str, "source": str, "is_search": bool}
    """
    from ..url_ingest import fetch_url_text_async, validate_public_http_url

    url = (payload.get("url") or "").strip()
    query = (payload.get("query") or "").strip()

    if url:
        ok, err = validate_public_http_url(url)
        if not ok:
            raise ValueError(err)
        plain, title = await fetch_url_text_async(url)
        if len(plain) > WEB_CONTEXT_MAX_CHARS:
            plain = plain[:WEB_CONTEXT_MAX_CHARS] + "\n\n[Content truncated for context.]"
        return {"text": plain, "title": title or url, "source": url, "is_search": False}

    if query:
        text = await _fetch_ddgo_search(query)
        if len(text) > WEB_CONTEXT_MAX_CHARS:
            text = text[:WEB_CONTEXT_MAX_CHARS] + "\n\n[Results truncated for context.]"
        return {"text": text, "title": f'Search: {query}', "source": DDGO_SEARCH_URL, "is_search": True}

    raise ValueError("Provide either a 'url' or a 'query'.")


def register_web_fetch_tool() -> None:
    """Register web.fetch with the tools registry. Call once at app startup."""
    from ..tools_registry import register_tool

    register_tool(
        "web.fetch",
        (
            "Fetch a web page by URL and extract plain text, or run a DuckDuckGo search "
            "and return result snippets. All processing is local."
        ),
        {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full http(s) URL to fetch",
                },
                "query": {
                    "type": "string",
                    "description": "Search query to run via DuckDuckGo HTML search",
                },
            },
        },
        _web_fetch_handler,
    )
