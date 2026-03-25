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

    Capture Mode: Applied to LeafLink-originated content only (see main.py).
    """
    # Capture Mode v2: Strict concise output enforcement (prompt-only; no post-processing).
    # Future: may pair with max_tokens, response_format / JSON schema, or a second pass for compression.
    return (
        "Capture Mode v2 (LeafLink handoff): The pasted message is a capture from LeafLink. "
        "Respond like a **tool** (direct output), not a coach or consultant. "
        "**This turn only** — ignore conflicting guidance above about long explanations, teaching tone, or exploratory depth.\n\n"
        "**Length & shape:** Target **4–8 short lines** total in most cases (or the same density as tight bullets). "
        "Use grouped bullets or 2–3 very short sections. **No long paragraphs**; break dense text into lists or labels.\n\n"
        "**Banned phrasing (do not use):** "
        "\"This ensures\", \"This means\", \"At a practical level\", \"Here's a breakdown\", "
        "\"In summary\", \"It's worth noting\", or similar meta-explanation. "
        "Do not narrate what you are doing — **show the result**.\n\n"
        "**Default structure:** "
        "(1) Optional one-line title or label only if useful. "
        "(2) **Structured output first** — organized / reformatted / extracted content (e.g. categorized grocery list, "
        "cleaned list, idea → short bullets). "
        "(3) At most **one** optional closing line: a single short assist question "
        "(e.g. \"Want this as a checklist?\", \"Want this saved or expanded?\") — omit if redundant.\n\n"
        "**Verbosity guard:** If a draft would exceed roughly **100–120 words**, **rewrite shorter** before sending: "
        "remove explanation and coaching; keep only actionable, structured output plus at most one optional question.\n\n"
        "**Vocabulary:** Prefer *organize, reformat, extract, clean, summarize, categorize, list*. "
        "Avoid abstract nouns like *mental model*, *framework*, *approach* unless the user's text already uses them.\n\n"
        "**Transformation priority:** Always **do** the organize / reformat / extract in the reply itself. "
        "Do **not** explain what could be done instead of doing it.\n\n"
        "**Still avoid:** speculative essays, abstract reasoning, filler, and multiple follow-up questions."
    )
