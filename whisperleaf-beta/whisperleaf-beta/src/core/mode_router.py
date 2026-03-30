"""
Lightweight response-mode routing before prompt assembly.

Creative and conversational requests should not be coerced into task-spec format.

TODO: Replace heuristics with intent classification or user-selected mode when available.
"""

from __future__ import annotations

from enum import Enum


class ResponseMode(str, Enum):
    """High-level response shape for the next model turn."""

    CONVERSATIONAL = "conversational"
    CREATIVE = "creative"
    TASK_DEV = "task_dev"


_MANUAL_OVERRIDE_PREFIXES: dict[str, ResponseMode] = {
    "/chat": ResponseMode.CONVERSATIONAL,
    "/creative": ResponseMode.CREATIVE,
    "/dev": ResponseMode.TASK_DEV,
}


def parse_mode_override(user_text: str) -> tuple[ResponseMode | None, str]:
    """
    Parse optional leading slash-override.

    Manual mode override beats heuristics.
    Returns: (forced_mode_or_none, cleaned_text_without_prefix)
    """
    text = (user_text or "")
    stripped = text.lstrip()
    if not stripped:
        return (None, "")

    token, sep, rest = stripped.partition(" ")
    mode = _MANUAL_OVERRIDE_PREFIXES.get(token.lower())
    if mode is None:
        return (None, text)
    cleaned = rest.strip() if sep else ""
    return (mode, cleaned)


# Strong engineering / implementation signals (checked first).
_TASK_DEV_PHRASES: tuple[str, ...] = (
    "write a function",
    "write function",
    "write a class",
    "write class",
    "write tests",
    "write test",
    "add tests",
    "add test",
    "add unit test",
    "create a file",
    "create file",
    "new file",
    "modify file",
    "edit file",
    "change file",
    "fix this code",
    "fix the code",
    "fix code",
    "cursor prompt",
    "run tests",
    "run pytest",
    "scaffold",
    "refactor",
    "implement",
    "patch ",
    "pull request",
    "pull request:",
    "add endpoint",
    "create endpoint",
    "receive endpoint",
    "api endpoint",
    "rest endpoint",
    "graphql",
    "migration",
    "dockerfile",
    "kubernetes",
    "ci/cd",
    "unittest",
    "pytest",
    "src/",
    "tests/",
    "bug in",
    "stack trace",
)

_TASK_DEV_TOKENS: frozenset[str] = frozenset(
    {
        "refactor",
        "scaffold",
        "implement",
        "debug",
        "endpoint",
        "schema",
        "patch",
        "kubernetes",
    }
)

# Creative / generative writing (after task-dev pass).
_CREATIVE_MARKERS: tuple[str, ...] = (
    "haiku",
    "poem",
    "poetry",
    "limerick",
    "sonnet",
    "verse",
    "ode",
    "ballad",
    "short story",
    "flash fiction",
    "fan fiction",
    "fiction",
    "novella",
    "novel",
    "story about",
    "tell me a story",
    "song lyrics",
    "lyrics for",
    "rewrite this poetically",
    "describe this scene",
    "write something funny",
    "something funny",
    "brainstorm names",
    "name ideas",
    "slogan",
    "tagline",
    "creative writing",
    "screenplay",
    "dialogue for",
    "monologue",
)


def detect_mode(user_text: str) -> ResponseMode:
    """
    Heuristic V1 router: TASK_DEV > CREATIVE > CONVERSATIONAL.

    Not ML — order and phrase lists matter; tune as false positives appear.
    """
    m = (user_text or "").strip().lower()
    if not m:
        return ResponseMode.CONVERSATIONAL

    if any(p in m for p in _TASK_DEV_PHRASES):
        return ResponseMode.TASK_DEV
    for tok in _TASK_DEV_TOKENS:
        if _word_boundary(m, tok):
            return ResponseMode.TASK_DEV
    # "build" often means software here; avoid matching "rebuild trust" via short window
    if m.startswith("build ") or " build " in m or "build a" in m or "build an" in m or "build the" in m:
        return ResponseMode.TASK_DEV
    if (m.startswith("create ") or " create " in m) and not any(
        x in m for x in ("story", "poem", "character", "world", "song", "scene")
    ):
        if any(x in m for x in ("file", "endpoint", "api", "app", "service", "class", "module", "project")):
            return ResponseMode.TASK_DEV

    if any(marker in m for marker in _CREATIVE_MARKERS):
        return ResponseMode.CREATIVE

    return ResponseMode.CONVERSATIONAL


def _word_boundary(text: str, token: str) -> bool:
    """True if token appears as a whole word in text."""
    start = 0
    while True:
        i = text.find(token, start)
        if i < 0:
            return False
        before_ok = i == 0 or not text[i - 1].isalnum()
        after_i = i + len(token)
        after_ok = after_i >= len(text) or not text[after_i].isalnum()
        if before_ok and after_ok:
            return True
        start = i + 1


def conversational_posture(user_text: str) -> str:
    """
    Strategy vs learning for non-task, non-creative messages.
    Returns: \"strategy\" | \"learning\"
    """
    m = (user_text or "").strip().lower()
    if not m:
        return "learning"

    strategy_cues = (
        "should i",
        "is this a good idea",
        "good idea",
        "best approach",
        "best way",
        "compare",
        "option",
        "tradeoff",
        "trade-offs",
        "pros and cons",
        "pros/cons",
        "which is better",
    )
    learning_cues = (
        "what is",
        "what are",
        "how does",
        "why",
        "explain",
        "help me understand",
    )

    if any(cue in m for cue in strategy_cues):
        return "strategy"
    if any(cue in m for cue in learning_cues):
        return "learning"
    return "learning"


def explain_mode_choice(user_text: str) -> str:
    """Short internal/debug reason (log/tests only; not for end users)."""
    manual_mode, cleaned = parse_mode_override(user_text)
    if manual_mode is not None:
        return f"manual:{manual_mode.value}"

    mode = detect_mode(cleaned)
    m = (cleaned or "").strip().lower()
    if not m:
        return "empty -> conversational/learning"

    if mode == ResponseMode.TASK_DEV:
        for p in _TASK_DEV_PHRASES:
            if p in m:
                return f"task_dev:phrase:{p!r}"
        for tok in sorted(_TASK_DEV_TOKENS):
            if _word_boundary(m, tok):
                return f"task_dev:token:{tok!r}"
        if "build" in m:
            return "task_dev:build-context"
        return "task_dev:create-context"

    if mode == ResponseMode.CREATIVE:
        for marker in _CREATIVE_MARKERS:
            if marker in m:
                return f"creative:marker:{marker!r}"
        return "creative"

    posture = conversational_posture(cleaned)
    return f"conversational:{posture}"


def engineering_scaffolding_allowed(mode: ResponseMode) -> bool:
    """True only when Objective/Requirements/Tests-style shaping is allowed."""
    return mode is ResponseMode.TASK_DEV


def anti_engineering_scaffolding_instruction() -> str:
    """Fragment for conversational/creative modes (no task-spec sections)."""
    return (
        "Do NOT structure your reply as an engineering task spec: no Objective, Requirements, "
        "Files/components to modify, or Tests sections unless the user explicitly asked for that format."
    )
