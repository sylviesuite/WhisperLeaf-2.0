"""
User-triggered URL fetch: download HTML and extract readable plain text only.
No background calls; no analytics. Dedup keys are stored only in the local index.
"""

from __future__ import annotations

import re
from html import unescape
from typing import Tuple
from urllib.parse import urlparse, urlunparse

import httpx

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 400_000
DEFAULT_TIMEOUT = 20.0

_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
    }
)


def validate_public_http_url(url: str) -> Tuple[bool, str]:
    """Return (ok, error_message). Only http(s), no file/javascript, block obvious loopback names."""
    raw = (url or "").strip()
    if not raw:
        return False, "Please paste a link first."
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return False, "That does not look like a web link. Use http or https."
    if not parsed.netloc:
        return False, "That link does not look complete. Check and try again."
    host = parsed.hostname
    if not host:
        return False, "That link does not look complete. Check and try again."
    h = host.lower()
    if h in _BLOCKED_HOSTS or h.endswith(".localhost"):
        return False, "This app cannot fetch that address."
    return True, ""


def normalize_url_for_dedup(url: str) -> str:
    """Stable key for same-session duplicate checks (local index only)."""
    raw = (url or "").strip()
    p = urlparse(raw)
    scheme = (p.scheme or "https").lower()
    netloc = (p.netloc or "").lower()
    if not netloc:
        return raw.lower()
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    query = p.query
    rebuilt = urlunparse((scheme, netloc, path, "", query, ""))
    return rebuilt


def build_display_label(page_title: str, url: str) -> str:
    """Short label for lists: title when helpful, else host + path snippet."""
    t = (page_title or "").strip()
    if t and len(t) <= 120:
        return t
    try:
        p = urlparse((url or "").strip())
        host = p.netloc or ""
        path = p.path or ""
        if not host:
            u = (url or "").strip()
            return (u[:72] + "…") if len(u) > 72 else u
        if path and path != "/":
            path_disp = path if len(path) <= 48 else (path[:45] + "…")
            return f"{host}{path_disp}"
        return host
    except Exception:
        u = (url or "").strip()
        return (u[:72] + "…") if len(u) > 72 else u


def _strip_noise_soup(soup: "BeautifulSoup") -> None:
    for tag in soup(["script", "style", "noscript", "template", "svg", "iframe", "form"]):
        tag.decompose()
    structural = (
        "nav",
        "header",
        "footer",
        "aside",
        '[role="navigation"]',
        '[role="banner"]',
        '[role="contentinfo"]',
        '[role="complementary"]',
    )
    for sel in structural:
        for t in soup.select(sel):
            t.decompose()
    # Cookie bars, promos, common boilerplate (best-effort; local parse only)
    noise_selectors = (
        '[class*="cookie"]',
        '[id*="cookie"]',
        '[class*="consent"]',
        '[id*="consent"]',
        '[class*="gdpr"]',
        '[class*="newsletter"]',
        '[class*="subscribe-box"]',
        '[class*="social-share"]',
        '[id*="ad-"]',
        '[class*="advertisement"]',
    )
    for sel in noise_selectors:
        try:
            for t in soup.select(sel):
                t.decompose()
        except Exception:
            pass


def _collapse_short_repeated_runs(text: str) -> str:
    """Drop consecutive duplicate short lines (common footer noise)."""
    lines = text.split("\n")
    out: list[str] = []
    prev = None
    for ln in lines:
        s = ln.strip()
        if s and s == prev and len(s) < 48:
            continue
        out.append(ln)
        prev = s if s else prev
    return "\n".join(out)


def html_to_readable_text(html: bytes, content_type: str | None = None) -> Tuple[str, str]:
    """
    Parse HTML and return (plain_text, suggested_title).
    """
    if not BeautifulSoup:
        raise RuntimeError("HTML parsing is not available.")

    charset = "utf-8"
    if content_type and "charset=" in content_type.lower():
        m = re.search(r"charset=([\w-]+)", content_type, re.I)
        if m:
            charset = m.group(1).strip() or charset

    try:
        text_bytes = html.decode(charset, errors="replace")
    except LookupError:
        text_bytes = html.decode("utf-8", errors="replace")

    soup = BeautifulSoup(text_bytes, "html.parser")
    title = ""
    if soup.title and soup.title.string:
        title = unescape(soup.title.string.strip())

    _strip_noise_soup(soup)

    main = soup.find(attrs={"itemprop": "articleBody"})
    if not main:
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.find("body")
            or soup
        )
    parts = main.get_text(separator="\n", strip=True)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in parts.splitlines()]
    lines = [ln for ln in lines if ln]
    plain = "\n".join(lines)
    plain = _collapse_short_repeated_runs(plain)
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()

    if len(plain) > MAX_TEXT_CHARS:
        plain = plain[:MAX_TEXT_CHARS] + "\n\n[Content shortened for size.]"

    return plain, title


async def fetch_url_text_async(url: str) -> Tuple[str, str]:
    """
    Fetch URL (user-initiated only) and return (plain_text, page_title).
    Raises ValueError with a short user-facing message on failure.
    """
    ok, err = validate_public_http_url(url)
    if not ok:
        raise ValueError(err)

    headers = {
        "User-Agent": "WhisperLeaf/1.0 (local document fetch; user-requested)",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            async with client.stream("GET", url.strip(), headers=headers) as response:
                response.raise_for_status()
                ctype = response.headers.get("content-type", "")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        raise ValueError("That page is too large to add here.")
                    chunks.append(chunk)
                raw = b"".join(chunks)
    except httpx.TimeoutException:
        raise ValueError("That took too long. Try again, or try a simpler page.")
    except httpx.HTTPStatusError:
        raise ValueError("Could not fetch this page.")
    except httpx.RequestError:
        raise ValueError("Could not reach that address. Check the link and try again.")

    if not raw:
        raise ValueError("Could not fetch this page.")

    if "html" not in ctype.lower() and not raw.lstrip().startswith((b"<", b"\xef\xbb\xbf<")):
        try:
            text = raw.decode("utf-8", errors="replace").strip()
        except Exception:
            text = ""
        if not text:
            raise ValueError("That does not look like a web page. Try an article or doc link.")
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS]
        return text, ""

    if not BeautifulSoup:
        raise ValueError("Could not fetch this page.")

    try:
        plain, title = html_to_readable_text(raw, ctype)
    except Exception:
        raise ValueError("Could not read the main content from this page.")

    if not plain.strip():
        raise ValueError("No readable text was found on this page.")

    return plain, title
