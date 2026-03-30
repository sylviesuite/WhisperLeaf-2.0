"""
Tests for memory injection guardrails (memory bleed prevention).

These tests are intentionally unit-level: they validate relevance gating logic without
depending on ChromaDB / Ollama / SSE streaming.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.memory_injection_guard import (
    MEMORY_RELEVANCE_THRESHOLD,
    MEMORY_TOP_K,
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
    # Lexical overlap must be strong enough that combined relevance clears 0.75 at this semantic score.
    user_message = (
        "Earlier you mentioned WhisperLeaf pricing and subscription tiers. "
        "What did you say about WhisperLeaf pricing strategy?"
    )

    injected, _debug = filter_relevant_memories(user_message, [_cand(pricing_memory, score=0.96)])
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


def test_weak_combined_score_dropped():
    """Below MEMORY_RELEVANCE_THRESHOLD with no lexical tie → no injection."""
    mem = "Obscure fact about zeppelin maintenance schedules in the 1930s."
    user_message = "What is 2+2?"

    injected, _ = filter_relevant_memories(user_message, [_cand(mem, score=0.4)])
    assert injected == []


def test_strong_relevant_memory_passes():
    mem = "User prefers dark mode and large font in the WhisperLeaf UI."
    user_message = "Can you remind me what display preferences I set for WhisperLeaf?"

    injected, debug = filter_relevant_memories(user_message, [_cand(mem, score=0.92)])
    assert len(injected) == 1
    assert debug["memories_injected"] == 1
    assert "dark mode" in build_memory_context_block(injected).lower()


def test_unrelated_high_semantic_still_blocked_without_overlap():
    mem = "Detailed notes about Antarctic research station supply chains."
    user_message = "How do I bake sourdough at home?"

    injected, _ = filter_relevant_memories(user_message, [_cand(mem, score=0.99)])
    assert injected == []


def test_at_most_three_memories_injected():
    user_message = "WhisperLeaf setup preferences and workflow"
    candidates = [
        _cand("WhisperLeaf dark mode enabled for the UI.", score=0.96),
        _cand("WhisperLeaf keyboard shortcuts customized for workflow.", score=0.95),
        _cand("WhisperLeaf local model path is configured.", score=0.94),
        _cand("WhisperLeaf document folder watch enabled.", score=0.93),
        _cand("WhisperLeaf memory vault privacy set to local only.", score=0.92),
    ]

    injected, debug = filter_relevant_memories(user_message, candidates)
    assert len(injected) <= MEMORY_TOP_K
    assert debug["memory_top_k"] == MEMORY_TOP_K
    assert debug["memories_injected"] <= MEMORY_TOP_K


def test_injected_memories_sorted_by_relevance_descending():
    user_message = (
        "WhisperLeaf setup priority notes first second third priority WhisperLeaf notes"
    )
    candidates = [
        _cand("WhisperLeaf third priority note about setup.", score=0.97),
        _cand("WhisperLeaf first priority note about setup.", score=0.995),
        _cand("WhisperLeaf second priority note about setup.", score=0.98),
    ]

    injected, _ = filter_relevant_memories(user_message, candidates)
    scores = [float(c.get("_guard_relevance_score", 0.0)) for c in injected]
    assert scores == sorted(scores, reverse=True)
    assert injected[0]["snippet"].startswith("WhisperLeaf first priority")


def test_threshold_constant_documented():
    assert MEMORY_RELEVANCE_THRESHOLD == 0.75
    assert MEMORY_TOP_K == 3
