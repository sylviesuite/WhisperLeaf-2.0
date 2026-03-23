"""Response mode routing and anti-scaffolding hints."""

from src.core.mode_router import (
    ResponseMode,
    anti_engineering_scaffolding_instruction,
    conversational_posture,
    detect_mode,
    engineering_scaffolding_allowed,
    explain_mode_choice,
    parse_mode_override,
)


def test_haiku_scott_family_nola_is_creative() -> None:
    q = "write a fun haiku about the Scott family gathering in NOLA"
    assert detect_mode(q) == ResponseMode.CREATIVE
    assert "haiku" in explain_mode_choice(q)


def test_poem_new_orleans_is_creative() -> None:
    q = "i want to write a poem about new orleans today"
    assert detect_mode(q) == ResponseMode.CREATIVE


def test_whisperleaf_math_question_is_conversational() -> None:
    q = "Does WhisperLeaf do math well?"
    assert detect_mode(q) == ResponseMode.CONVERSATIONAL
    assert conversational_posture(q) == "learning"


def test_leaflink_endpoint_is_task_dev() -> None:
    q = "create a paired-device receive endpoint for LeafLink"
    assert detect_mode(q) == ResponseMode.TASK_DEV


def test_modify_main_add_tests_is_task_dev() -> None:
    q = "modify src/core/main.py and add tests"
    assert detect_mode(q) == ResponseMode.TASK_DEV


def test_creative_prompt_layers_exclude_engineering_spec_enforcement() -> None:
    """Conversational/creative shaping must not ask for Objective/Requirements/Tests blocks."""
    anti = anti_engineering_scaffolding_instruction()
    creative_shaping = (
        "Mode shaping: creative request. Produce the creative output directly. "
        + anti
    )
    conversational_shaping = (
        "Mode shaping: conversational answer. Be natural. "
        + anti
    )
    forbidden = "Structure enforcement: include Objective"
    assert forbidden not in creative_shaping
    assert forbidden not in conversational_shaping
    assert "Do NOT structure your reply as an engineering task spec" in creative_shaping


def test_task_dev_allows_scaffolding_flag() -> None:
    assert engineering_scaffolding_allowed(ResponseMode.TASK_DEV) is True
    assert engineering_scaffolding_allowed(ResponseMode.CREATIVE) is False
    assert engineering_scaffolding_allowed(ResponseMode.CONVERSATIONAL) is False


def test_task_dev_explain_mentions_match() -> None:
    q = "implement the handler"
    assert detect_mode(q) == ResponseMode.TASK_DEV
    assert "task_dev" in explain_mode_choice(q)


def test_manual_override_creative_forced() -> None:
    mode, cleaned = parse_mode_override("/creative write a fun haiku about NOLA")
    assert mode == ResponseMode.CREATIVE
    assert cleaned == "write a fun haiku about NOLA"


def test_manual_override_chat_forced() -> None:
    mode, cleaned = parse_mode_override("/chat does WhisperLeaf do math well?")
    assert mode == ResponseMode.CONVERSATIONAL
    assert cleaned == "does WhisperLeaf do math well?"


def test_manual_override_dev_forced() -> None:
    mode, cleaned = parse_mode_override("/dev modify src/core/main.py and add tests")
    assert mode == ResponseMode.TASK_DEV
    assert cleaned == "modify src/core/main.py and add tests"


def test_unknown_prefix_does_not_force_mode() -> None:
    mode, cleaned = parse_mode_override("/weird write a poem")
    assert mode is None
    assert cleaned == "/weird write a poem"


def test_no_prefix_uses_auto_mode() -> None:
    mode, cleaned = parse_mode_override("write a poem")
    assert mode is None
    assert cleaned == "write a poem"
    assert detect_mode(cleaned) == ResponseMode.CREATIVE


def test_manual_override_beats_heuristics() -> None:
    text = "/chat write a poem about New Orleans"
    mode, cleaned = parse_mode_override(text)
    assert mode == ResponseMode.CONVERSATIONAL
    assert detect_mode(cleaned) == ResponseMode.CREATIVE
    # Effective mode should stay CONVERSATIONAL when override exists.
    effective = mode or detect_mode(cleaned)
    assert effective == ResponseMode.CONVERSATIONAL
