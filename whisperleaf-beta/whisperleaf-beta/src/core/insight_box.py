"""
InsightBox: minimal mode-aware framing guidance.

Mode changes framing, not system boundaries.
InsightBox is guidance, not automation.

This module must stay lightweight and safe:
- no memory/search/chat wiring
- no promotion or inbox logic
"""

from __future__ import annotations

from .mode_router import ResponseMode


def get_mode_label(response_mode: ResponseMode) -> str:
    """Human-readable label (optional internal/debug use)."""
    if response_mode is ResponseMode.CONVERSATIONAL:
        return "CONVERSATIONAL"
    if response_mode is ResponseMode.CREATIVE:
        return "CREATIVE"
    return "TASK_DEV"


def build_mode_guidance(response_mode: ResponseMode) -> str:
    """
    Return a small instruction block tailored to the response mode.

    The guidance is additive (short) and intentionally avoids hidden behavior.
    """
    if response_mode is ResponseMode.CONVERSATIONAL:
        return (
            "InsightBox (conversational): Answer naturally and helpfully. "
            "Avoid engineering/task-spec formatting unless the user explicitly requests it. "
            "Keep the tone human and unforced."
        )

    if response_mode is ResponseMode.CREATIVE:
        return (
            "InsightBox (creative): Produce the creative output directly. "
            "Do not turn the request into an engineering task spec or software-planning checklist. "
            "Feel free to be vivid, playful, rhythmic, and expressive."
        )

    # TASK_DEV
    return (
        "InsightBox (task_dev): Structured, implementation-oriented responses are allowed when appropriate. "
        "Be precise, explicit about steps, and keep output actionable for development (including files/tests when relevant)."
    )


__all__ = ["build_mode_guidance", "get_mode_label"]

