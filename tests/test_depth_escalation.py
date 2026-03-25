"""Tests for explanation depth escalation (levels 1–4)."""

from src.core.depth_escalation import (
    build_depth_escalation_guidance,
    select_depth_escalation_level,
)
from src.core.mode_router import ResponseMode


def _conv():
    return ResponseMode.CONVERSATIONAL


def test_first_explanation_is_level_1():
    assert (
        select_depth_escalation_level(
            "What is a neuron?",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=False,
        )
        == 1
    )


def test_non_explanation_first_message_none():
    assert (
        select_depth_escalation_level(
            "Hello there",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=False,
        )
        is None
    )


def test_follow_up_how_is_level_2():
    assert (
        select_depth_escalation_level(
            "How does the signal travel?",
            topic_reset_detected=False,
            previous_assistant_turns=1,
            response_mode=_conv(),
            leaflink=False,
        )
        == 2
    )


def test_go_deeper_is_level_3_even_first_message():
    assert (
        select_depth_escalation_level(
            "Go deeper into how transformers work",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=False,
        )
        == 3
    )


def test_technical_detail_is_level_4():
    assert (
        select_depth_escalation_level(
            "Give me the full technical detail on attention masks",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=False,
        )
        == 4
    )


def test_topic_reset_de_escalates_to_1():
    assert (
        select_depth_escalation_level(
            "Why does that matter?",
            topic_reset_detected=True,
            previous_assistant_turns=3,
            response_mode=_conv(),
            leaflink=False,
        )
        == 1
    )


def test_fresh_simple_question_de_escalates():
    assert (
        select_depth_escalation_level(
            "What is Docker?",
            topic_reset_detected=False,
            previous_assistant_turns=2,
            response_mode=_conv(),
            leaflink=False,
        )
        == 1
    )


def test_practical_skips_escalation():
    assert (
        select_depth_escalation_level(
            "What should I do about this cough?",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=False,
        )
        is None
    )


def test_task_dev_skips():
    assert (
        select_depth_escalation_level(
            "What is a thread?",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=ResponseMode.TASK_DEV,
            leaflink=False,
        )
        is None
    )


def test_leaflink_skips():
    assert (
        select_depth_escalation_level(
            "What is a list?",
            topic_reset_detected=False,
            previous_assistant_turns=0,
            response_mode=_conv(),
            leaflink=True,
        )
        is None
    )


def test_level_1_guidance_mentions_invitation():
    g = build_depth_escalation_guidance(1)
    assert "Level 1" in g or "level 1" in g.lower()
    assert "invitation" in g.lower()


def test_level_2_guidance_no_invitation():
    g = build_depth_escalation_guidance(2)
    assert "Level 2" in g or "level 2" in g.lower()
    assert "Do not" in g or "do not" in g.lower()


def test_elaborate_more_level_3_not_2():
    assert (
        select_depth_escalation_level(
            "Can you elaborate more on that part?",
            topic_reset_detected=False,
            previous_assistant_turns=1,
            response_mode=_conv(),
            leaflink=False,
        )
        == 3
    )
