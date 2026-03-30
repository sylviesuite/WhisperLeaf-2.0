"""
Tools Registry (plugin layer) for WhisperLeaf.
Stable interface: register_tool, list_tools, call_tool.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

# Tool definition: name, description, input_schema (JSON-serializable dict), handler
# handler: async (payload: dict, context: dict) -> Any
ToolDefinition = Dict[str, Any]
_Tools: Dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    handler: Callable[[Dict[str, Any], Dict[str, Any]], Any],
) -> None:
    """Register a tool. handler may be async."""
    _Tools[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "handler": handler,
    }


def list_tools() -> List[Dict[str, Any]]:
    """Return public metadata for all registered tools (name, description, input_schema)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in _Tools.values()
    ]


async def call_tool(
    name: str,
    payload: Dict[str, Any],
    context: Dict[str, Any],
) -> Any:
    """Execute the handler for the given tool. Raises KeyError if tool unknown."""
    if name not in _Tools:
        raise KeyError(f"Unknown tool: {name}")
    handler = _Tools[name]["handler"]
    import asyncio
    if asyncio.iscoroutinefunction(handler):
        return await handler(payload, context)
    return handler(payload, context)
