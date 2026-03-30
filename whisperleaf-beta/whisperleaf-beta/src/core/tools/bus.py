"""
Minimal Tool Bus: runs tools from the registry and returns a normalized result.
Exists so WhisperLeaf can scale to future tools (docs.search, system.status, etc.)
without changing call sites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..tools_registry import call_tool


@dataclass
class ToolResult:
    """Standard result shape for tool execution."""
    ok: bool
    data: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ToolBus:
    """Resolves tools from the registry, runs them safely, returns ToolResult."""

    async def execute(
        self,
        tool_id: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        context = context or {}
        try:
            result = await call_tool(tool_id, payload, context)
            return ToolResult(ok=True, data=result, meta={}, error=None)
        except KeyError as e:
            return ToolResult(ok=False, data=None, meta={}, error=f"Tool not found: {e}")
        except Exception as e:
            return ToolResult(ok=False, data=None, meta={}, error=str(e))
