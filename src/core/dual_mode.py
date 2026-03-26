"""
Dual Mode System: Structure vs Reflect — response-shape hints for the chat prompt.

Structure Mode aligns with Capture Mode v2 for LeafLink; a variant applies to other turns
(e.g. document bullets). Reflect Mode allows narrative and interpretation without fluff.

Future expansion: Builder Mode, Research Mode, or client-selected response_shape flags.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, Optional

from .capture_mode import build_capture_mode_guidance

# Word-boundary match for common med/product terms (avoids "pillar" matching "pill").
_RE_PRACTICAL_MED_TERMS = re.compile(
    r"\b(pills?|tablets?|capsules?|medications?|antibiotics?|supplements?)\b",
    re.IGNORECASE,
)

ResponseShapeMode = Literal["structure", "reflect"]


def _hits_practical_action_first(m: str) -> bool:
    """
    Health, tools, decisions, steps, recommendations: force action-first Structure Mode.

    Evaluated before reflect defaults so e.g. 'explain which medication…' stays structured.
    """
    phrases = (
        "what should i",
        "what should we",
        "what do i do",
        "what can i do",
        "how should i",
        "what would you do",
        "recommend",
        "recommendation",
        " step by step",
        "step-by-step",
        "steps to ",
        " what steps",
        "what steps ",
        "first step",
        "which tool",
        "what tool",
        "how do i use",
        "how to use",
        "how do i fix",
        "how to fix",
        "medication",
        "medications",
        "medicine",
        "prescription",
        "antibiotic",
        "dosage",
        "supplement",
        "supplements",
        "over-the-counter",
        "over the counter",
        " side effect",
        " side effects",
    )
    if any(p in m for p in phrases):
        return True
    return bool(_RE_PRACTICAL_MED_TERMS.search(m))


# Wording that signals “tell me about this” (Reflect) — also used for explanation follow-up hints in main.py.
_REFLECT_BASE: tuple[str, ...] = (
    "explain",
    "reflect",
    "interpret",
    "what does this mean",
    "nuance",
    "nuances",
    "subtext",
    "implication",
    "implications",
    "deeper meaning",
    "meaning of",
)
_EXPLANATION_INTENT_PHRASES: tuple[str, ...] = (
    "what is ",
    "what are ",
    "what was ",
    "how does ",
    "how did ",
    "can you explain",
    "tell me about ",
    "what does ",
    "why does ",
    "why is ",
)


def hits_explanation_intent(message: str) -> bool:
    """
    True for informational / explanatory questions, excluding practical-action-first turns.

    Used to tune follow-up guidance (simple answer + optional depth invitation).
    """
    m = (message or "").strip().lower()
    if _hits_practical_action_first(m):
        return False
    if any(p in m for p in _EXPLANATION_INTENT_PHRASES):
        return True
    return any(k in m for k in _REFLECT_BASE)


def select_response_shape_mode(
    message: str,
    *,
    is_leaflink: bool,
    has_document_context: bool,
) -> Optional[ResponseShapeMode]:
    """
    Choose structure vs reflect, or None when no dual-mode overlay should apply.

    Rules:
    - LeafLink → always structure.
    - Practical / health / tools / “what should I do” → always structure (before reflect defaults).
    - Document context → default reflect unless structure is forced by wording or practical triggers.
    - Explicit structure/reflect keywords apply when no higher-priority rule matched.
    """
    m = (message or "").strip().lower()

    if is_leaflink:
        return "structure"
    if _hits_practical_action_first(m):
        return "structure"

    structure_kw = (
        "summarize",
        "summary",
        "tldr",
        "tl;dr",
        "bullet",
        "bullets",
        "bullet point",
        "bullet-point",
        "in bullets",
        "as bullets",
        "as a list",
        "list the",
        "list out",
        "checklist",
        "outline",
    )
    reflect_kw = _REFLECT_BASE + _EXPLANATION_INTENT_PHRASES

    def _hits(kws: tuple[str, ...]) -> bool:
        return any(k in m for k in kws)

    s_hit = _hits(structure_kw)
    r_hit = _hits(reflect_kw)

    if s_hit and r_hit:
        # e.g. "explain in bullets" → prefer structure when list/bullet intent is explicit.
        # Omit bare "summary" here so definitional questions like "what is a summary" stay reflect, not action-first structure.
        if any(
            k in m
            for k in (
                "bullet",
                "bullets",
                "list",
                "outline",
                "summarize",
                "checklist",
                "tldr",
                "tl;dr",
            )
        ):
            return "structure"
        return "reflect"
    if s_hit:
        return "structure"
    if r_hit:
        return "reflect"

    if has_document_context:
        return "reflect"
    return None


def _structure_mode_non_leaflink_guidance() -> str:
    """Structure shaping when not a LeafLink capture (e.g. document bullets, practical how-to)."""
    return (
        "Structure Mode: Deliver a concise, **action-first** answer for this turn—like a calm, knowledgeable person, not an essay.\n\n"
        "**Openings:** Start with usable guidance in the **first sentence**. Do **not** open with abstract or reflective framing "
        "(e.g. \"At a practical level…\", \"One pattern to keep in mind…\", \"It's worth considering that…\"). "
        "Prefer direct lines such as \"Main thing is…\", \"Start with…\", \"You can try…\". "
        "For **comparisons or which-to-choose**, lead with the **sharpest distinction or tradeoff**—not empty balance (“both have pros and cons”) unless that is truly the honest answer.\n\n"
        "**Shape:** Target **~4–6 short lines** or **3–5 sentences**, or tight bullets. "
        "Put **immediately usable options first**; use short bullets when listing choices; keep explanation brief and tied to action. "
        "Avoid long paragraphs and over-explaining.\n\n"
        "**Tone:** Calm, steady, non-alarmist; conversational, not corporate. **Suggest** (\"you can try\", \"I'd…\") not **command** (\"you should\", \"you must\").\n\n"
        "**Safety (only if relevant):** One natural escalation line if needed—e.g. \"If it gets worse…\", \"If it hangs around a few days…\". "
        "Do **not** use liability-heavy boilerplate (e.g. \"consult a healthcare professional\", \"it is essential…\").\n\n"
        "**Accuracy:** Stick to common, widely accepted options; avoid fringe or weakly supported specifics. "
        "If uncertain, stay general and brief rather than guessing.\n\n"
        "**Anti-patterns:** No generic disclaimers up front, no \"advisor essay\" before the answer, no filler or stiff AI voice.\n\n"
        "**Verbosity guard:** If a draft would exceed roughly **100–120 words**, compress: drop filler, keep actionable structure.\n\n"
        "**Optional:** At most one short follow-up offer (not multiple questions)."
    )


def _reflect_mode_guidance() -> str:
    """Reflective shaping: narrative and interpretation allowed, still disciplined."""
    return (
        "Reflect Mode: For this turn, you may use **interpretive depth** when it helps—after a clear simple layer.\n\n"
        "**Explanations (“what is…”, “how does…”, “explain…”):** Lead with a **short, plain-language** core answer—"
        "**clarity over completeness**; do not front-load textbook or academic phrasing unless the user asked for it. "
        "Then, if useful, add detail in a second beat (short paragraph or a few bullets).\n\n"
        "**Depth invitation (Level 1 only):** When **Depth escalation** in this prompt is **Level 1** (or absent) and a simple answer suffices, "
        "you may end with **at most one** short, low-pressure line inviting the user to go further—e.g. "
        "\"I can go deeper into how it works if you want.\" / \"I can break down the parts one by one if that's useful.\" / "
        "\"I can go deeper into the science or keep it plain-language.\" "
        "If escalation is **Level 2+**, **do not** add that invitation. "
        "It should feel like an **invitation**, not a script; **do not** stack multiple questions or follow-ups.\n\n"
        "**Shape:** Short paragraphs and narrative are allowed when they improve clarity. "
        "Use bullets only when they genuinely help (e.g. distinct takeaways); do not force rigid bullets.\n\n"
        "**Tone:** Calm, clear, respectful. Preserve meaning and tone of source material when answering about documents. "
        "You may discuss themes, implications, and subtext where appropriate.\n\n"
        "**Discipline:** Avoid unnecessary fluff, stacked hedging, and filler. "
        "Skip coachy meta-phrases like \"This means…\" unless the user explicitly asked for a plain restatement.\n\n"
        "**Note:** Skip the depth-invitation line when the user asked for immediate practical steps or urgent guidance—"
        "answer directly first."
    )


def build_dual_mode_guidance(mode: ResponseShapeMode, context: Dict[str, Any]) -> str:
    """
    Build prompt fragment for the selected shape mode.

    ``context`` may include:
    - ``leaflink`` (bool): when True and mode is ``structure``, reuse Capture Mode v2 text.
    """
    # Dual Mode System: Structure vs Reflect (prompt-only).
    # Future: Builder Mode, Research Mode, client `response_shape` enum, token limits.
    if mode == "structure":
        if context.get("leaflink"):
            return build_capture_mode_guidance()
        return _structure_mode_non_leaflink_guidance()
    return _reflect_mode_guidance()
