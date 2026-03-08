"""
memory.search tool: wraps existing memory search (semantic → keyword → recency).
First wrapped tool on the Tool Bus; keeps chat behavior unchanged while centralizing tool execution.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..memory import get_recent_memory_entries, search_memories_by_query
from ..memory_models import PrivacyLevel


def _run_memory_search(
    memory_search_instance: Any,
    query: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Same logic as chat's _build_memory_context: semantic search, then keyword, then recency.
    Returns snippets and entries_for_audit so the caller can format and record audit.
    """
    snippets: List[str] = []
    entries_for_audit: List[Dict[str, Any]] = []

    try:
        results = memory_search_instance.semantic_search(
            query=(query or "").strip(),
            limit=top_k,
            privacy_level=PrivacyLevel.PRIVATE,
        )
        if results:
            for entry, _ in results:
                content = (getattr(entry, "content", None) or "").strip()
                if content:
                    snippets.append(content[:400] + ("..." if len(content) > 400 else ""))
    except Exception:
        pass

    if not snippets:
        try:
            entries_for_audit = search_memories_by_query(
                (query or "").strip(), limit=top_k, exclude_blocked=True
            )
            if entries_for_audit:
                for e in entries_for_audit:
                    content = (e.get("content") or "").strip()
                    if content:
                        snippets.append(content[:400] + ("..." if len(content) > 400 else ""))
        except Exception:
            entries_for_audit = []

    if not snippets:
        entries_for_audit = get_recent_memory_entries(limit=top_k, exclude_blocked=True)
        snippets = [
            (e.get("content") or "").strip()[:400]
            + ("..." if len((e.get("content") or "")) > 400 else "")
            for e in entries_for_audit
            if (e.get("content") or "").strip()
        ]

    return {"snippets": snippets, "entries_for_audit": entries_for_audit}


def make_memory_search_handler(memory_search_instance: Any):
    """Returns a handler that uses the given MemorySearch instance (no context dependency)."""

    def handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        query = (payload.get("query") or "").strip()
        top_k = min(int(payload.get("top_k", 5)), 20)
        return _run_memory_search(memory_search_instance, query=query, top_k=top_k)

    return handler


def register_memory_search_tool(memory_search_instance: Any) -> None:
    """Register memory.search with the tools registry. Call once at app startup."""
    from ..tools_registry import register_tool

    register_tool(
        "memory.search",
        "Search memories by query (semantic then keyword then recency). Returns snippets and entries for audit.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Max number of results", "default": 5},
            },
            "required": ["query"],
        },
        make_memory_search_handler(memory_search_instance),
    )
