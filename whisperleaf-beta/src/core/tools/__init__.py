"""
Minimal Tool Bus and tools. Standard result contract and wrapped tools: memory.search, docs.search, system.status.
"""

from .bus import ToolBus, ToolResult
from .memory_search_tool import register_memory_search_tool
from .docs_search_tool import register_docs_search_tool
from .system_status_tool import register_system_status_tool
from .web_fetch_tool import register_web_fetch_tool

# Single bus instance for app use
tool_bus = ToolBus()

__all__ = [
    "ToolBus",
    "ToolResult",
    "tool_bus",
    "register_memory_search_tool",
    "register_docs_search_tool",
    "register_system_status_tool",
    "register_web_fetch_tool",
]
