"""
Tests for memory injection guardrails (memory bleed prevention).

These tests are intentionally unit-level: they validate the pivot/new-topic detection
and relevance gating logic without depending on ChromaDB / Ollama / SSE streaming.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.memory_injection_guard import (
    build_memory_context_block,
    filter_relevant_memories,
)


def _cand(snippet: str, score: float | None = None):
    return {"snippet": snippet, "score": score}


def test_pivot_blocks_product_pricing_memories():
    previous_pricing = "WhisperLeaf pricing strategy details. Also includes TypeScript architecture notes."
    knitting_memory = "Knitting tip: a left-slanting decrease creates a left-leaning seam."

    user_message = "Let's pivot. How do I knit a left-slanting decrease?"

    candidates = [
        _cand(previous_pricing, score=0.95),
        _cand(knitting_memory, score=0.99),
    ]

    injected, _debug = filter_relevant_memories(user_message, candidates)
    block = build_memory_context_block(injected).lower()

    assert "pricing" not in block
    assert "typescript" not in block
    assert "architecture" not in block
    assert "whisperleaf" not in block

    # The knitting memory is the new-topic target.
    assert "left-slanting decrease" in block


def test_new_topic_blocks_code_related_memories():
    code_memory = "TypeScript helper functions and API route refactoring advice."
    user_message = "What is the capital of France?"

    injected, _debug = filter_relevant_memories(user_message, [_cand(code_memory, score=0.9)])
    block = build_memory_context_block(injected)

    assert injected == []
    assert block == ""


def test_blocked_category_excluded_without_explicit_recall():
    pricing_memory = "WhisperLeaf pricing plan tiers and subscription cost."
    user_message = "Tell me about knitting increases."

    injected, _debug = filter_relevant_memories(user_message, [_cand(pricing_memory, score=0.99)])
    block = build_memory_context_block(injected).lower()

    assert injected == []
    assert "pricing" not in block


def test_relevant_memory_allowed_when_overlap_is_strong():
    knitting_memory = "Knitting: remind me how a left-slanting increase works again."
    user_message = "Remind me how a left-slanting increase works again"

    injected, _debug = filter_relevant_memories(user_message, [_cand(knitting_memory, score=0.85)])
    block = build_memory_context_block(injected).lower()

    assert len(injected) == 1
    assert "left-slanting increase" in block


def test_explicit_recall_allows_blocked_categories():
    pricing_memory = "WhisperLeaf pricing strategy: subscription tiers and positioning."
    user_message = "Earlier you mentioned pricing for WhisperLeaf. What did you say?"

    injected, _debug = filter_relevant_memories(user_message, [_cand(pricing_memory, score=0.82)])
    block = build_memory_context_block(injected).lower()

    assert len(injected) == 1
    assert "pricing strategy" in block
    assert "whisperleaf" in block


def test_empty_memory_safe_when_no_candidates():
    user_message = "Anything else?"

    injected, debug = filter_relevant_memories(user_message, [])
    block = build_memory_context_block(injected)

    assert injected == []
    assert block == ""
    assert debug["memories_injected"] == 0

