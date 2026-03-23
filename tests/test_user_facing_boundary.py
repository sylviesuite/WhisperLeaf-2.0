"""Tests for user-facing vs explicit-codebase query classification and leak heuristics."""

import src.core.main as main_mod

from src.core.main import (
    allows_internal_codebase_context,
    is_explicit_codebase_query,
    is_general_capability_meta_query,
    response_contains_internal_leak,
)


def test_can_you_write_code_not_explicit():
    assert is_explicit_codebase_query("Can you write code?") is False
    assert is_general_capability_meta_query("Can you write code?")


def test_memory_search_tool_question_is_explicit():
    assert is_explicit_codebase_query("how does WhisperLeaf memory_search_tool work?")


def test_show_architecture_is_explicit():
    assert is_explicit_codebase_query("show me your architecture")


def test_write_python_function_not_explicit():
    assert is_explicit_codebase_query("write a python function") is False


def test_explicit_triggers_from_spec():
    triggers_coverage = [
        "explain the whisperleaf codebase",
        "in this project where is auth",
        "describe your system",
        "how is whisperleaf built",
        "how does whisperleaf work",
        "show me your code",
        "something in your code",
        "your architecture overview",
        "your implementation of chat",
    ]
    for msg in triggers_coverage:
        assert is_explicit_codebase_query(msg), msg


def test_src_core_in_question_is_explicit():
    assert is_explicit_codebase_query("Where is pivot logic in src/core?")


def test_general_capability_meta_vs_explicit():
    assert is_general_capability_meta_query("what can you do")
    assert is_explicit_codebase_query("what can you do") is False


def test_response_leak_heuristic():
    assert response_contains_internal_leak("See src/core/main.py for details.")
    assert response_contains_internal_leak("The memory_search_tool returns candidates.")
    assert response_contains_internal_leak("Handled in memory_injection_guard.")
    assert response_contains_internal_leak("The system prompt says to be calm.") is True
    assert response_contains_internal_leak("def foo():\n    pass\n") is False
    assert response_contains_internal_leak("Use `hello.py` as a filename for your script.") is False


def test_developer_mode_allows_internal_without_explicit_ask():
    old = main_mod.DEVELOPER_MODE
    try:
        main_mod.DEVELOPER_MODE = True
        assert allows_internal_codebase_context("hello random") is True
        main_mod.DEVELOPER_MODE = False
        assert allows_internal_codebase_context("hello random") is False
        assert allows_internal_codebase_context("show me your architecture") is True
    finally:
        main_mod.DEVELOPER_MODE = old
