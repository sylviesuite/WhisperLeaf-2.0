"""
Memory injection guardrails to prevent "memory bleed" across topic pivots.

This is intentionally lightweight and rule-based for now:
- Detect explicit pivot/new-topic intent.
- Detect explicit "recall what you said earlier" intent.
- Apply conservative relevance gating to retrieved memories.
- Block known high-risk memory categories during normal chat unless explicitly requested.
- Prefer injecting none when relevance is uncertain.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# Conservative defaults. Memory is optional; relevance is mandatory.
MAX_INJECTED_MEMORIES_ABSOLUTE = 2
MAX_INJECTED_MEMORIES_NON_PIVOT_DEFAULT = 1
MAX_INJECTED_MEMORIES_PIVOT_DEFAULT = 0  # enforced by requiring HIGH relevance

# Relevance thresholds: conservative, 0–1.
# Normal: only inject when clearly relevant.
MIN_RELEVANCE_SCORE = 0.65
# High relevance used for allowing 2 memories.
HIGH_RELEVANCE_SCORE = 0.80
# When a topic reset/pivot is detected we use a stricter threshold than normal,
# but slightly lower than HIGH_RELEVANCE_SCORE so genuinely related memories
# still pass after keyword+semantic scoring.
# Pivot/new-topic: drop prior-topic memories unless extremely relevant.
PIVOT_RELEVANCE_THRESHOLD = 0.80
MIN_KEYWORD_OVERLAP = 0.12
# Explicit recall is user intent to pull prior context; allow a lower relevance bar
# while still requiring some connection to the request.
EXPLICIT_RECALL_MIN_SCORE = 0.35


_PIVOT_CUES = (
    "pivot",
    "new topic",
    "different topic",
    "switch topics",
    "switch gears",
    "forget that",
    "forget this",
    "let's talk about",
    "lets talk about",
    "let's change",
    "lets change",
    "new subject",
    "change the subject",
    "reset conversation",
)

_EXPLICIT_RECALL_CUES = (
    "earlier you",
    "previously",
    "you mentioned",
    "what did you say",
    "what was it you said",
    "remind me what you said",
    "recall",
    "do you remember",
    "tell me what you said",
)

# High-risk categories for normal chat. These are inferred from memory text/content.
# Blocked categories (normal chat): only allow on explicit recall.
_BLOCKED_CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "pricing": (
        "pricing",
        "price",
        "cost",
        "subscription",
        "plan",
        "tier",
    ),
    "product_strategy": (
        "product strategy",
        "strategy",
        "roadmap",
        "launch",
        "positioning",
        "go-to-market",
        "g2m",
        "take back control",
    ),
    "unrelated_code": (
        "typescript",
        "javascript",
        "python",
        "regex",
        "refactor",
        "implement",
        "write code",
        "code generation",
        "scripting",
        "function",
        "class",
        "api route",
        "component",
        "frontend",
    ),
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _keyword_overlap_ratio(user_message: str, snippet: str) -> float:
    user_tokens = set(_tokenize(user_message))
    mem_tokens = set(_tokenize(snippet))
    if not user_tokens or not mem_tokens:
        return 0.0
    overlap = user_tokens.intersection(mem_tokens)
    # Normalize by the smaller side to make short, direct matches count.
    denom = max(1, min(len(user_tokens), len(mem_tokens)))
    return len(overlap) / denom


def detect_explicit_memory_recall(user_message: str) -> bool:
    m = (user_message or "").lower()
    return any(cue in m for cue in _EXPLICIT_RECALL_CUES)


def detect_topic_reset(user_message: str) -> bool:
    """
    Returns true when the user clearly signals a pivot/new topic.
    Also treats very short general-knowledge questions as likely resets.
    """
    m = (user_message or "").lower()
    if not m.strip():
        return False
    if detect_explicit_memory_recall(user_message):
        return False

    if any(cue in m for cue in _PIVOT_CUES):
        return True

    tokens = _tokenize(m)
    # Heuristic: short factual questions often represent fresh domains.
    if len(tokens) <= 9 and (
        "capital" in m
        or "population" in m
        or "who is" in m
        or "what is" in m
        or "where is" in m
        or "distance" in m
    ):
        return True

    return False


def infer_blocked_category(snippet: str) -> Optional[str]:
    s = (snippet or "").lower()
    for category, keywords in _BLOCKED_CATEGORY_KEYWORDS.items():
        if any(kw in s for kw in keywords):
            return category
    return None


def _memory_relevance_score(user_message: str, candidate: Dict[str, Any]) -> float:
    """
    Combines semantic score (if provided) and cheap keyword overlap.
    If semantic score is absent, keyword overlap dominates.
    """
    snippet = (candidate.get("snippet") or "").strip()
    overlap = _keyword_overlap_ratio(user_message, snippet)
    sem = candidate.get("score", None)
    if isinstance(sem, (int, float)) and sem > 0:
        # Semantic score usually already lives in ~[0,1]; keep it dominant but not exclusive.
        score = (0.65 * float(sem)) + (0.35 * overlap)
    else:
        score = overlap
    # Clamp to [0,1] so thresholds are meaningful.
    if score < 0:
        return 0.0
    if score > 1:
        return 1.0
    return float(score)


def filter_relevant_memories(
    user_message: str,
    retrieved_candidates: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filters retrieved memories to prevent unrelated topic bleed.

    Fail-safe rule: if relevance is uncertain, inject none.
    """
    pivot_reset = detect_topic_reset(user_message)
    explicit_recall = detect_explicit_memory_recall(user_message)

    retrieved_n = len(retrieved_candidates or [])
    rejected_reasons: List[Dict[str, Any]] = []
    kept: List[Dict[str, Any]] = []

    pivot_mode = bool(pivot_reset and not explicit_recall)

    # Score + gate candidates.
    for cand in retrieved_candidates or []:
        snippet = (cand.get("snippet") or "").strip()
        if not snippet:
            continue

        blocked_category = infer_blocked_category(snippet)
        overlap = _keyword_overlap_ratio(user_message, snippet)
        score = _memory_relevance_score(user_message, cand)

        # In pivot mode, apply thresholds against the raw semantic score when present.
        # This prevents "combined score" (semantic+keyword blend) from over-filtering
        # genuinely on-topic memories that are slightly below the old pivot bar.
        sem_score: Optional[float] = None
        try:
            if cand.get("score") is not None:
                sem_score = float(cand.get("score"))
        except (TypeError, ValueError):
            sem_score = None

        if blocked_category and not explicit_recall:
            rejected_reasons.append(
                {
                    "snippet_preview": snippet[:60],
                    "reason": "blocked_category",
                    "category": blocked_category,
                }
            )
            continue

        # Guardrail: keyword overlap must be non-trivial for safe injection.
        # If the memory looks like the right domain, overlap will be > MIN_KEYWORD_OVERLAP.
        overlap_guard_score = score
        if pivot_mode and sem_score is not None:
            overlap_guard_score = sem_score
        min_guard = EXPLICIT_RECALL_MIN_SCORE if explicit_recall else MIN_RELEVANCE_SCORE
        if overlap < MIN_KEYWORD_OVERLAP and overlap_guard_score < min_guard:
            rejected_reasons.append(
                {
                    "snippet_preview": snippet[:60],
                    "reason": "low_similarity",
                    "overlap": round(overlap, 4),
                    "score": round(score, 4),
                }
            )
            continue

        # Pivot/new-topic: default to 0 unless highly relevant.
        if pivot_mode:
            # Pivot means reset of unrelated context, but does not mean "drop all memory".
            # Only keep memories that are very strongly on-topic.
            pivot_guard_score = score
            if sem_score is not None:
                pivot_guard_score = sem_score
            if pivot_guard_score < PIVOT_RELEVANCE_THRESHOLD:
                rejected_reasons.append(
                    {
                        "snippet_preview": snippet[:60],
                        "reason": "pivot_guard",
                        "score": round(pivot_guard_score, 4),
                        "threshold": PIVOT_RELEVANCE_THRESHOLD,
                    }
                )
                continue

        # Non-pivot normal chat: require at least minimum relevance.
        if not pivot_mode and not explicit_recall:
            if score < MIN_RELEVANCE_SCORE:
                rejected_reasons.append(
                    {
                        "snippet_preview": snippet[:60],
                        "reason": "low_similarity",
                        "score": round(score, 4),
                    }
                )
                continue
        # Explicit recall: allow lower threshold (user is explicitly asking for prior content)
        if explicit_recall and not pivot_mode:
            if score < EXPLICIT_RECALL_MIN_SCORE and overlap < MIN_KEYWORD_OVERLAP:
                rejected_reasons.append(
                    {
                        "snippet_preview": snippet[:60],
                        "reason": "low_similarity",
                        "score": round(score, 4),
                        "threshold": EXPLICIT_RECALL_MIN_SCORE,
                    }
                )
                continue

        cand_copy = dict(cand)
        # Sorting/capping should use the same scoring basis as pivot thresholds.
        guard_score = score
        if pivot_mode and sem_score is not None:
            guard_score = sem_score
        cand_copy["_guard_relevance_score"] = guard_score
        kept.append(cand_copy)

    # If nothing is confidently relevant, inject none.
    if not kept:
        debug = {
            "topic_reset_detected": pivot_reset,
            "explicit_recall_detected": explicit_recall,
            "memories_retrieved": retrieved_n,
            "memories_injected": 0,
            "rejected_memory_reasons": rejected_reasons,
        }
        return [], debug

    kept.sort(key=lambda c: float(c.get("_guard_relevance_score", 0.0)), reverse=True)
    best_score = float(kept[0].get("_guard_relevance_score", 0.0))

    if pivot_reset and not explicit_recall:
        # Pivot means reset: inject only the most relevant ones.
        # Allow up to 2 if the best candidate is *very* strong.
        max_inject = 2 if best_score >= (PIVOT_RELEVANCE_THRESHOLD + 0.10) else 1
    else:
        # Prefer fewer memories; only inject 2 when relevance is clearly strong.
        max_inject = (
            MAX_INJECTED_MEMORIES_ABSOLUTE
            if best_score >= HIGH_RELEVANCE_SCORE
            else MAX_INJECTED_MEMORIES_NON_PIVOT_DEFAULT
        )

    injected = kept[:max_inject]

    debug = {
        "topic_reset_detected": pivot_reset,
        "explicit_recall_detected": explicit_recall,
        "memories_retrieved": retrieved_n,
        "memories_injected": len(injected),
        "rejected_memory_reasons": rejected_reasons,
        "best_relevance_score": round(best_score, 4),
        "max_inject": max_inject,
        "pivot_relevance_threshold": PIVOT_RELEVANCE_THRESHOLD if pivot_reset else None,
    }
    return injected, debug


def build_memory_context_block(
    injected_candidates: List[Dict[str, Any]],
) -> str:
    """
    Build the exact prompt block used for memory injection.
    Includes a guard section to keep the model from drifting to unrelated topics.
    """
    if not injected_candidates:
        return ""
    lines = []
    for c in injected_candidates:
        snippet = (c.get("snippet") or "").strip()
        if snippet:
            lines.append("- " + snippet)

    if not lines:
        return ""

    guard = (
        "Only use the following memory entries if they are directly relevant to the current request. "
        "Do not introduce unrelated prior topics unless the user explicitly asks.\n\n"
    )
    return guard + "RELEVANT MEMORY:\n" + "\n".join(lines)

