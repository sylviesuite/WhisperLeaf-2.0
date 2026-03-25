"""
Confidence calibration for tone: match certainty in wording without dominating the reply.

Prompt-only; pairs with depth escalation, honesty guidance, and Structure/Reflect modes.
"""

from __future__ import annotations

from typing import Literal, Optional

from .dual_mode import _hits_practical_action_first
from .mode_router import ResponseMode

ConfidenceLevel = Literal[1, 2, 3, 4]

_RISKY_OR_UNKNOWN_CUES: tuple[str, ...] = (
    "diagnose me",
    "diagnose this",
    "am i sick",
    "am i pregnant",
    "do i have cancer",
    "legal advice",
    "will i win in court",
    "guarantee me",
    "promise me that",
    "tell me exactly what will happen",
    "read my mind",
    "what am i thinking",
)

_USER_UNCERTAINTY_CUES: tuple[str, ...] = (
    "not sure",
    "i'm not sure",
    "i am not sure",
    "i don't know",
    "i dont know",
    "idk ",
    "no idea if",
    "unclear if",
    "could be wrong",
    "correct me if",
    "might be wrong",
    "guess what this",
    "wild guess",
)


def select_confidence_level(
    message: str,
    *,
    has_honesty_guidance: bool,
    is_simple_query: bool,
    response_mode: object,
    leaflink: bool,
) -> Optional[ConfidenceLevel]:
    """
    Choose 1–4 for conversational calibration, or None when this layer should not apply.
    """
    if response_mode in (ResponseMode.TASK_DEV, ResponseMode.CREATIVE):
        return None
    if leaflink:
        return None

    m = (message or "").strip().lower()

    if any(c in m for c in _RISKY_OR_UNKNOWN_CUES):
        return 4
    if has_honesty_guidance:
        return 3
    if any(c in m for c in _USER_UNCERTAINTY_CUES):
        return 3

    if is_simple_query:
        return 1
    if _hits_practical_action_first(m):
        return 2
    return 2


def build_confidence_guidance(level: ConfidenceLevel) -> str:
    """Compact calibration block—light touch, not corporate disclaimers."""
    tail = (
        "Keep this **subtle**: adjust wording in a sentence or two—do **not** stack hedges, "
        "do **not** sound legalistic, and do **not** let calibration dominate the answer. "
        "Stay calm, grounded, and human."
    )
    if level == 1:
        return (
            "**Confidence (Level 1 — high):** The ask is a clear, widely accepted kind of fact or definition. "
            "Answer **directly and calmly**; skip unnecessary qualifiers or throat-clearing.\n\n"
            + tail
        )
    if level == 2:
        return (
            "**Confidence (Level 2 — moderate):** Outcomes or details may **vary by context**. "
            "Use **light** qualification where honest (e.g. “usually”, “often”, “in most cases”)—"
            "**one** qualifier per idea, not a pile of them.\n\n"
            + tail
        )
    if level == 3:
        return (
            "**Confidence (Level 3 — low / limited):** You may be **missing context** or on shaky ground. "
            "Be **transparent** in plain language (“might”, “could”, “depends on…”) without sounding alarmed or corporate. "
            "Prefer honesty over sounding authoritative.\n\n"
            + tail
        )
    return (
        "**Confidence (Level 4 — unknown or risky):** **Do not speculate** on specifics that need facts you do not have. "
        "Stay **general**, offer safe framing, or ask **briefly** for what would clarify—no feigned certainty.\n\n"
        + tail
    )
