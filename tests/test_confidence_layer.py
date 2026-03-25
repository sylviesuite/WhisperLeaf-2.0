"""Tests for confidence layer selection and guidance."""

from src.core.confidence_layer import (
    build_confidence_guidance,
    select_confidence_level,
)
from src.core.mode_router import ResponseMode


def _conv():
    return ResponseMode.CONVERSATIONAL


def test_simple_query_level_1():
    assert (
        select_confidence_level(
            "what is photosynthesis",
            has_honesty_guidance=False,
            is_simple_query=True,
            response_mode=_conv(),
            leaflink=False,
        )
        == 1
    )


def test_default_moderate_level_2():
    assert (
        select_confidence_level(
            "Tell me about the history of jazz",
            has_honesty_guidance=False,
            is_simple_query=False,
            response_mode=_conv(),
            leaflink=False,
        )
        == 2
    )


def test_practical_level_2():
    assert (
        select_confidence_level(
            "What should I do about a leaky faucet?",
            has_honesty_guidance=False,
            is_simple_query=False,
            response_mode=_conv(),
            leaflink=False,
        )
        == 2
    )


def test_honesty_guidance_level_3():
    assert (
        select_confidence_level(
            "How were you trained?",
            has_honesty_guidance=True,
            is_simple_query=False,
            response_mode=_conv(),
            leaflink=False,
        )
        == 3
    )


def test_risky_level_4_over_honesty():
    assert (
        select_confidence_level(
            "Can you give me legal advice on this contract?",
            has_honesty_guidance=True,
            is_simple_query=False,
            response_mode=_conv(),
            leaflink=False,
        )
        == 4
    )


def test_user_uncertainty_level_3():
    assert (
        select_confidence_level(
            "I'm not sure what this error means",
            has_honesty_guidance=False,
            is_simple_query=False,
            response_mode=_conv(),
            leaflink=False,
        )
        == 3
    )


def test_task_dev_skips():
    assert (
        select_confidence_level(
            "what is a thread",
            has_honesty_guidance=False,
            is_simple_query=True,
            response_mode=ResponseMode.TASK_DEV,
            leaflink=False,
        )
        is None
    )


def test_leaflink_skips():
    assert (
        select_confidence_level(
            "what is a list",
            has_honesty_guidance=False,
            is_simple_query=True,
            response_mode=_conv(),
            leaflink=True,
        )
        is None
    )


def test_guidance_mentions_subtle():
    g = build_confidence_guidance(2)
    assert "moderate" in g.lower() or "Level 2" in g
    assert "subtle" in g.lower() or "light" in g.lower()
