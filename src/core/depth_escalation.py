"""
Depth escalation for explanations: simple by default, deeper only when the user signals it.

Prompt-only; pairs with depth_guidance and follow-up rules in main.py.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from .dual_mode import _hits_practical_action_first, hits_explanation_intent
from .mode_router import ResponseMode

DepthEscalationLevel = Literal[1, 2, 3, 4]

_LEVEL_4_CUES: tuple[str, ...] = (
    "rigorous proof",
    "peer reviewed",
    "peer-reviewed",
    "technical detail",
    "full technical",
    "in technical detail",
    "scientific detail",
    "from first principles",
    "formal treatment",
    "expert level",
    "graduate level",
    "low-level detail",
    "low level detail",
    "internals of",
    "exact mechanism",
    "mathematical detail",
    "like a textbook but technical",
    "for engineers",
    "for a scientist",
)

_LEVEL_3_CUES: tuple[str, ...] = (
    "go deeper",
    "go deep",
    "deeper on",
    "deeper into",
    "elaborate on",
    "explain more",
    "more detail",
    "more in depth",
    "in more depth",
    "elaborate more",
    "expand on",
    "expand this",
    "tell me more",
    "keep going",
    "continue explaining",
    "dive deeper",
    "unpack this",
    "unpack that",
)

# Follow-up curiosity (only after assistant has spoken at least once).
_LEVEL_2_CUES: tuple[str, ...] = (
    "how does ",
    "how do ",
    "why does ",
    "why do ",
    "why is ",
    "why are ",
    "what about ",
    "what if ",
    "can you clarify",
    "could you clarify",
    "and why",
    "how come",
    "elaborate",
)

_RE_FRESH_SIMPLE = re.compile(
    r"^(what is|what are|what was|define |tell me about |who is |what's |what’s )\s",
    re.IGNORECASE,
)


def _hits_level_4(m: str) -> bool:
    return any(c in m for c in _LEVEL_4_CUES)


def _hits_level_3(m: str) -> bool:
    # Check longer phrases before generic substrings (e.g. "elaborate more" before bare "elaborate").
    return any(c in m for c in _LEVEL_3_CUES)


def _hits_level_2_cues(m: str) -> bool:
    if _hits_level_3(m):
        return False
    if any(c in m for c in _LEVEL_2_CUES):
        return True
    s = m.strip()
    if re.match(r"^why[\s\?\.!]*$", s):
        return True
    if re.match(r"^how[\s\?\.!]*$", s):
        return True
    if s in ("really?", "like how?", "such as?", "example?"):
        return True
    return False


def _is_fresh_simple_question(m: str) -> bool:
    """New broad definitional question → de-escalate to level 1."""
    if len(m.split()) > 14:
        return False
    return bool(_RE_FRESH_SIMPLE.search(m.strip()))


def select_depth_escalation_level(
    message: str,
    *,
    topic_reset_detected: bool,
    previous_assistant_turns: int,
    response_mode: object,
    leaflink: bool,
) -> Optional[DepthEscalationLevel]:
    """
    Choose 1–4 for conversational explanation depth, or None when this layer should not apply.

    Rules: never jump to deep without user signal; practical/LeafLink/task/creative skip.
    """
    if response_mode in (ResponseMode.TASK_DEV, ResponseMode.CREATIVE):
        return None
    if leaflink:
        return None
    m = (message or "").strip().lower()
    if _hits_practical_action_first(m):
        return None

    if _hits_level_4(m):
        return 4
    if _hits_level_3(m):
        return 3

    if previous_assistant_turns == 0:
        if hits_explanation_intent(message):
            return 1
        return None

    if topic_reset_detected:
        return 1
    if _is_fresh_simple_question(m):
        return 1
    if _hits_level_2_cues(m):
        return 2
    return None


def build_depth_escalation_guidance(level: DepthEscalationLevel) -> str:
    """Single prompt block for the active depth level."""
    common = (
        "Avoid academic or textbook voice at every level—stay calm, grounded, and clear. "
        "Use short paragraphs and bullets when they help readability; avoid dense walls of text."
    )
    if level == 1:
        return (
            "**Depth escalation (Level 1 — Simple, default):** This is the first pass on an explanation-style topic. "
            "Give a **short, plain-language** core answer—**clarity over completeness**; do not front-load technical detail. "
            "**Never** assume the user wants expert depth yet. "
            "You may end with **at most one** short, optional, low-pressure invitation to go deeper—**no stacked options**.\n\n"
            + common
        )
    if level == 2:
        return (
            "**Depth escalation (Level 2 — Guided expansion):** The user followed up with curiosity (e.g. how/why). "
            "Expand **one layer** deeper than a Level‑1 skim—still conversational, not a lecture. "
            "**Do not** add an invitation to go deeper; they already engaged.\n\n"
            + common
        )
    if level == 3:
        return (
            "**Depth escalation (Level 3 — Deep dive):** The user explicitly asked for more depth. "
            "Provide a **more detailed** answer with **light terminology** where it helps understanding—still no textbook tone. "
            "Keep structure scannable (short sections or bullets); avoid long unbroken paragraphs. "
            "**Do not** add an invitation line.\n\n"
            + common
        )
    return (
        "**Depth escalation (Level 4 — Expert):** The user asked for technical or scientific precision. "
        "Use **precise terminology** and go deeper **while keeping structure readable** (short paragraphs, bullets when useful). "
        "Stay calm and grounded—not dense or condescending. **Do not** add an invitation line.\n\n"
        + common
    )
