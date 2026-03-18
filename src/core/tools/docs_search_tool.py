"""
docs.search tool: vector search over local indexed documents.
Returns list of {title, snippet, path} for Tool Bus dispatch.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Max results to return
DOCS_SEARCH_TOP_K = 10
# Max snippet length
SNIPPET_MAX_LEN = 300


def _run_docs_search(vector_store: Any, query: str, top_k: int = DOCS_SEARCH_TOP_K) -> List[Dict[str, Any]]:
    """
    Run vector search and normalize to [{title, snippet, path}].
    Never raises; returns [] on error or no match.
    """
    if not query or not (str(query).strip()):
        return []
    try:
        results = vector_store.search(
            query=str(query).strip(),
            n_results=top_k,
        )
    except Exception as e:
        logger.warning("docs.search failed: %s", e, exc_info=False)
        return []
    out: List[Dict[str, Any]] = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        # Normalize various possible shapes from vector store
        title = r.get("title") or r.get("metadata", {}).get("title") or r.get("document_id") or "Untitled"
        content = r.get("content") or r.get("snippet") or r.get("text") or ""
        snippet = (content[:SNIPPET_MAX_LEN] + ("..." if len(content) > SNIPPET_MAX_LEN else "")).strip()
        path = r.get("path") or r.get("document_id") or r.get("file_path") or ""
        out.append({"title": str(title), "snippet": snippet, "path": str(path)})
    return out


def make_docs_search_handler(vector_store: Any):
    """Returns a handler that uses the given VectorStore instance."""

    def handler(payload: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = (payload.get("query") or "").strip()
        top_k = min(int(payload.get("top_k", DOCS_SEARCH_TOP_K)), 20)
        return _run_docs_search(vector_store, query=query, top_k=top_k)

    return handler


def register_docs_search_tool(vector_store: Any) -> None:
    """Register docs.search with the tools registry. Call once at app startup."""
    from ..tools_registry import register_tool

    register_tool(
        "docs.search",
        "Search local indexed documents by semantic similarity. Returns list of {title, snippet, path}.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Max number of results", "default": DOCS_SEARCH_TOP_K},
            },
            "required": ["query"],
        },
        make_docs_search_handler(vector_store),
    )
