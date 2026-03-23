"""
LeafLink "Capture Mode": detection + prompt guidance for phone-captured paste.

Detection is marker-based today (matches chat UI insert format).
Future: client may send structured metadata (e.g. source=leaflink) or a classifier flag.
"""

from __future__ import annotations

# Prefixes emitted by templates/whisperleaf_chat.html buildSmartChatInsert()
_LEAFLINK_MARKERS: tuple[str, ...] = (
    "[LeafLink —",  # Unicode em dash (U+2014), primary
    "[LeafLink -",  # tolerant if copy/paste normalizes the dash
)


def is_leaflink_originated_message(message: str) -> bool:
    """
    True when the user message includes a LeafLink handoff block (UI paste format).

    Accepts:
    - message starting with a marker (after leading whitespace)
    - marker at the start of a new line (e.g. appended after prior chat text)
    """
    if not message or not message.strip():
        return False
    for mark in _LEAFLINK_MARKERS:
        if message.lstrip().startswith(mark):
            return True
        if f"\n{mark}" in message or "\r\n" + mark in message:
            return True
    return False


def build_capture_mode_guidance() -> str:
    """
    Instruction block appended to mode_guidance for LeafLink-originated turns.

    Capture Mode: Applied to LeafLink-originated content.
    """
    return (
        "Capture Mode (LeafLink handoff): The user message includes content sent from LeafLink "
        "(phone capture pasted into chat). Use this style for your reply.\n\n"
        "**Priority for this turn:** Capture Mode overrides conflicting instructions above "
        "(e.g. conversational 'mental model' or teaching tone; do not force a full engineering spec "
        "unless the pasted content is clearly code or build work — otherwise organize and improve the capture).\n\n"
        "Tone: Concise, practical, grounded. No philosophical framing, no 'mental model' language, "
        "no coaching or teaching voice unless the user explicitly asks to learn.\n\n"
        "Structure: Prefer bullet points or short grouped sections. Organize the captured material "
        "when it helps (e.g. categorize a grocery list, clean formatting, extract action items). "
        "Avoid long paragraphs.\n\n"
        "Behavior: Default to improving, organizing, or extracting value from the captured content. "
        "Do not over-expand, speculate, or add long explanations unless the user asks.\n\n"
        "Close: Optionally end with at most one short, concrete offer — e.g. "
        "'Want me to turn this into a checklist?' or 'Want quantities or categories adjusted?' "
        "Only if it fits; omit if redundant.\n\n"
        "Avoid in Capture Mode: abstract reasoning, teaching tone, unnecessary elaboration, and filler."
    )
