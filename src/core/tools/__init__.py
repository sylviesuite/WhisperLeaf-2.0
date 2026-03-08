"""
Minimal Tool Bus and tools. Standard result contract and one wrapped tool: memory.search.
"""

from .bus import ToolBus, ToolResult
from .memory_search_tool import register_memory_search_tool

# Single bus instance for app use
tool_bus = ToolBus()

__all__ = ["ToolBus", "ToolResult", "tool_bus", "register_memory_search_tool"]
