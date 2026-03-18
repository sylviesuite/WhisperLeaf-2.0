"""
system.status tool: return structured diagnostics (model, counts, uptime).
Must never fail; returns safe fallback values.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def _format_uptime(seconds: float) -> str:
    """Format seconds as human-readable uptime string."""
    if seconds < 0:
        return "0s"
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    h, rem = divmod(s, 3600)
    return f"{h}h {rem // 60}m" if rem else f"{h}h"


def _run_system_status(
    model_name: str,
    get_memory_count: Callable[[], int],
    get_docs_count: Callable[[], int],
    get_tools_count: Callable[[], int],
    start_time: float,
) -> Dict[str, Any]:
    """
    Build status dict. All callables must be safe (no raise).
    """
    try:
        memory_indexed = int(get_memory_count()) if callable(get_memory_count) else 0
    except Exception:
        memory_indexed = 0
    try:
        docs_indexed = int(get_docs_count()) if callable(get_docs_count) else 0
    except Exception:
        docs_indexed = 0
    try:
        tools_available = int(get_tools_count()) if callable(get_tools_count) else 0
    except Exception:
        tools_available = 0
    try:
        uptime = _format_uptime(time.time() - start_time)
    except Exception:
        uptime = "0s"
    return {
        "model": str(model_name) if model_name else "unknown",
        "memory_indexed": memory_indexed,
        "docs_indexed": docs_indexed,
        "tools_available": tools_available,
        "uptime": uptime,
    }


def make_system_status_handler(
    model_name: str,
    get_memory_count: Callable[[], int],
    get_docs_count: Callable[[], int],
    get_tools_count: Callable[[], int],
    start_time: float,
):
    """Returns a handler that uses the given dependencies."""

    def handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return _run_system_status(
                model_name=model_name,
                get_memory_count=get_memory_count,
                get_docs_count=get_docs_count,
                get_tools_count=get_tools_count,
                start_time=start_time,
            )
        except Exception as e:
            logger.warning("system.status failed: %s", e, exc_info=False)
            return {
                "model": str(model_name) if model_name else "unknown",
                "memory_indexed": 0,
                "docs_indexed": 0,
                "tools_available": 0,
                "uptime": "0s",
            }

    return handler


def register_system_status_tool(
    model_name: str,
    get_memory_count: Callable[[], int],
    get_docs_count: Callable[[], int],
    get_tools_count: Callable[[], int],
    start_time: float,
) -> None:
    """Register system.status with the tools registry. Call once at app startup."""
    from ..tools_registry import register_tool

    register_tool(
        "system.status",
        "Return system diagnostics: model, memory_indexed, docs_indexed, tools_available, uptime.",
        {"type": "object", "properties": {}, "required": []},
        make_system_status_handler(
            model_name=model_name,
            get_memory_count=get_memory_count,
            get_docs_count=get_docs_count,
            get_tools_count=get_tools_count,
            start_time=start_time,
        ),
    )
