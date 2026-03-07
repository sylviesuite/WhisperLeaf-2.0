"""
Chat engine: generates replies via Ollama LLM when available, with deterministic fallback.
Uses system prompt + retrieved memories as context + user message.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .memory_models import MemoryEntry
from . import llm_client

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_SYSTEM_PROMPT_CACHE: Dict[str, str] = {}

_FALLBACK_SYSTEM_PROMPT = (
    "You are WhisperLeaf. You are grounded, reflective, and steady. "
    "Your purpose is to help the user think more clearly. When appropriate, reframe assumptions."
)


def _load_system_prompt(mode: str = "system") -> str:
    """Load system prompt from prompts/{mode}.md. Falls back to _FALLBACK_SYSTEM_PROMPT if file missing."""
    if mode in _SYSTEM_PROMPT_CACHE:
        return _SYSTEM_PROMPT_CACHE[mode]
    path = _PROMPTS_DIR / f"{mode}.md"
    try:
        text = path.read_text(encoding="utf-8").strip()
        _SYSTEM_PROMPT_CACHE[mode] = text
        return text
    except Exception:
        _SYSTEM_PROMPT_CACHE[mode] = _FALLBACK_SYSTEM_PROMPT
        return _FALLBACK_SYSTEM_PROMPT


def _format_memory_context(memory_results: List[Tuple[MemoryEntry, float]]) -> str:
    """Format retrieved memories as a short context string for the LLM."""
    if not memory_results:
        return ""
    lines = []
    for mem, _ in memory_results[:5]:
        snippet = (mem.content or mem.title or "").strip()
        if len(snippet) > 200:
            snippet = snippet[:200].rstrip() + "..."
        if snippet:
            lines.append(f"- {snippet}")
    if not lines:
        return ""
    return "Context (relevant memories):\n\n" + "\n".join(lines)


def _deterministic_reply(message: str, memory_results: List[Tuple[MemoryEntry, float]]) -> str:
    """Fallback reply when Ollama is unavailable: references memories in a fixed format."""
    if not memory_results:
        return (
            "Thanks for sharing. I don't have any stored memories to reference yet, "
            "but I'm here to listen."
        )
    parts = ["Based on what you shared and what I remember:\n\n"]
    for i, (mem, score) in enumerate(memory_results[:3], 1):
        snippet = (mem.content or mem.title or "")[:120]
        if len((mem.content or mem.title or "")) > 120:
            snippet = snippet.rstrip() + "..."
        mood = getattr(mem.emotional_context, "primary_mood", None) or ""
        ref = f"• {mem.title or 'A memory'}"
        if mood:
            ref += f" (mood: {mood})"
        if snippet:
            ref += f": {snippet}"
        parts.append(ref)
        if i < min(3, len(memory_results)):
            parts.append("\n")
    return "".join(parts)


def generate_reply(message: str, memory_results: List[Tuple[MemoryEntry, float]], mode: str = "system") -> str:
    """
    Produce a reply using Ollama LLM when available; otherwise use deterministic fallback.
    memory_results: list of (MemoryEntry, similarity_score) from MemorySearch.semantic_search.
    mode: system prompt mode (e.g. "system", "builder"); loads from prompts/{mode}.md.
    """
    system_prompt = _load_system_prompt(mode)
    context = _format_memory_context(memory_results)
    user_content = (context + "\n\nUser: " + message) if context else message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    llm_reply = llm_client.chat(messages)
    if llm_reply:
        return llm_reply
    return _deterministic_reply(message, memory_results)
