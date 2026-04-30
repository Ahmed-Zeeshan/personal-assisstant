"""Web tools: search the web, fetch page content. Network-only — no path scoping needed."""
from __future__ import annotations

from urllib.parse import urlparse

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None  # type: ignore[assignment,misc]

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

try:
    import trafilatura
except ImportError:
    trafilatura = None  # type: ignore[assignment]


def web_search(*, query: str, count: int = 5) -> list[dict[str, str]]:
    """Search the web. Returns a list of {title, url, snippet}.

    Uses DuckDuckGo via duckduckgo-search. count is capped at 10.
    """
    if DDGS is None:
        raise ImportError("duckduckgo-search is not installed. Install with: pip install duckduckgo-search")
    n = max(1, min(int(count), 10))
    with DDGS() as d:
        raw = d.text(query, max_results=n)
    out: list[dict[str, str]] = []
    for r in raw or []:
        out.append({
            "title":   str(r.get("title", "")),
            "url":     str(r.get("href", "")),
            "snippet": str(r.get("body", "")),
        })
    return out


def web_fetch(*, url: str, max_chars: int = 8000) -> dict[str, str]:
    """Fetch a URL and return {url, title, text} of the readable main content."""
    if httpx is None:
        raise ImportError("httpx is not installed. Install with: pip install httpx")
    if trafilatura is None:
        raise ImportError("trafilatura is not installed. Install with: pip install trafilatura")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"web_fetch only supports http(s); got {parsed.scheme!r}")
    if not parsed.netloc:
        raise ValueError(f"web_fetch needs a hostname; got {url!r}")
    response = httpx.get(url, follow_redirects=True, timeout=15.0,
                         headers={"User-Agent": "voice-assistant/0.1"})
    response.raise_for_status()
    html = response.text
    text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    metadata = trafilatura.extract_metadata(html)
    title: str = (metadata.title if metadata and getattr(metadata, "title", None) else "") or ""
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    return {"url": url, "title": title, "text": text}


WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for up-to-date information. Use this when the user asks about current events, recent news, or facts you might not know.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "count": {"type": "integer", "description": "Number of results (1-10, default 5).", "default": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

WEB_FETCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch a URL and return its readable text. Use after web_search to read a specific result, or when the user gives you a URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Absolute http(s) URL."},
                "max_chars": {"type": "integer", "description": "Truncate text to this many characters (default 8000).", "default": 8000},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
}
