"""
Memory injection guardrails to prevent "memory bleed" across topic pivots.

Design goals (strict gate):
- Prefer conversation turns (recentTurns) over long-term memory: the model sees recent
  dialogue first; this module only admits a small set of *high-confidence* memories so
  stale or tangential vault entries cannot override the present topic.
- Long-term memory is used only when relevance is clear (see MEMORY_RELEVANCE_THRESHOLD).
  Weak or ambiguous matches are dropped entirely — no partial injection, no "helpful"
  half-related snippets that can steer the model off-topic.
- Topic mismatch (semantic score too low and/or lexical overlap too low vs the current
  user message) blocks injection: unrelated people, products, or themes in the vault
  must not surface unless they clearly match the request.

Implementation: rule-based, deterministic, maintainable thresholds.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# --- Strict retrieval / injection limits (single source of truth for chat) ---
# Memory search returns at most this many candidates; injection still applies thresholding.
MEMORY_TOP_K = 3
# Minimum blended relevance (semantic + lexical blend) to inject a memory.
MEMORY_RELEVANCE_THRESHOLD = 0.75
# Lexical overlap must be non-trivial so we do not inject on pure embedding noise.
MIN_KEYWORD_OVERLAP = 0.12
# When retriever semantic score is high but blended score is dragged down by vocabulary
# mismatch, allow a slightly lower overlap floor only if blended score is still plausibly related.
SEMANTIC_ASSISTED_OVERLAP_MIN = 0.06
SEMANTIC_ASSISTED_COMBINED_MIN = 0.62


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
    Combined relevance score in [0, 1]: semantic score (if provided) blended with
    keyword overlap. Used for sorting and threshold checks.
    """
    snippet = (candidate.get("snippet") or "").strip()
    overlap = _keyword_overlap_ratio(user_message, snippet)
    sem = candidate.get("score", None)
    if isinstance(sem, (int, float)) and sem > 0:
        score = (0.65 * float(sem)) + (0.35 * overlap)
    else:
        score = overlap
    return max(0.0, min(1.0, float(score)))


def _parse_semantic_score(candidate: Dict[str, Any]) -> Optional[float]:
    try:
        if candidate.get("score") is None:
            return None
        v = float(candidate.get("score"))
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _passes_relevance_gate(
    overlap: float,
    sem_score: Optional[float],
    combined_relevance: float,
) -> bool:
    """
    Inclusion decision: score first, then narrow semantic-assisted path.

    High-confidence memory should pass even if semantic match is imperfect to avoid
    over-filtering useful context — but only when blended score already cleared the bar,
    or when retriever score is high *and* there is still a minimal lexical tie + non-garbage blend.
    """
    if combined_relevance >= MEMORY_RELEVANCE_THRESHOLD:
        return True

    if sem_score is not None and sem_score >= MEMORY_RELEVANCE_THRESHOLD:
        if overlap >= MIN_KEYWORD_OVERLAP:
            return True
        if (
            overlap >= SEMANTIC_ASSISTED_OVERLAP_MIN
            and combined_relevance >= SEMANTIC_ASSISTED_COMBINED_MIN
        ):
            return True

    return False


def _topic_mismatch(
    overlap: float,
    sem_score: Optional[float],
    combined_relevance: float,
) -> bool:
    """True if this candidate should be rejected for topic / confidence reasons."""
    return not _passes_relevance_gate(overlap, sem_score, combined_relevance)


def filter_relevant_memories(
    user_message: str,
    retrieved_candidates: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter and cap long-term memories for injection.

    - Candidates are sorted by relevance_score (desc) before gating so the strongest
      evidence is evaluated first; at most MEMORY_TOP_K items can pass.
    - If nothing meets the bar, return [] (answer from current input + recentTurns only).
    """
    pivot_reset = detect_topic_reset(user_message)
    explicit_recall = detect_explicit_memory_recall(user_message)

    retrieved_n = len(retrieved_candidates or [])
    rejected_reasons: List[Dict[str, Any]] = []

    # Annotate and sort by relevance_score descending before applying rules.
    enriched: List[Dict[str, Any]] = []
    for cand in retrieved_candidates or []:
        snippet = (cand.get("snippet") or "").strip()
        if not snippet:
            continue
        rel = _memory_relevance_score(user_message, cand)
        row = dict(cand)
        row["_relevance_score"] = rel
        enriched.append(row)

    enriched.sort(key=lambda c: float(c.get("_relevance_score", 0.0)), reverse=True)

    kept: List[Dict[str, Any]] = []
    for cand in enriched:
        snippet = (cand.get("snippet") or "").strip()
        overlap = _keyword_overlap_ratio(user_message, snippet)
        relevance_score = float(cand.get("_relevance_score", 0.0))
        sem_score = _parse_semantic_score(cand)

        blocked_category = infer_blocked_category(snippet)
        # Risky categories stay out of normal turns; explicit recall is intentional retrieval.
        if blocked_category and not explicit_recall:
            rejected_reasons.append(
                {
                    "snippet_preview": snippet[:60],
                    "reason": "blocked_category",
                    "category": blocked_category,
                }
            )
            continue

        if _topic_mismatch(overlap, sem_score, relevance_score):
            rejected_reasons.append(
                {
                    "snippet_preview": snippet[:60],
                    "reason": "topic_mismatch_or_weak_memory",
                    "overlap": round(overlap, 4),
                    "semantic_score": None if sem_score is None else round(sem_score, 4),
                    "relevance_score": round(relevance_score, 4),
                    "threshold": MEMORY_RELEVANCE_THRESHOLD,
                }
            )
            continue

        out = dict(cand)
        out["_guard_relevance_score"] = relevance_score
        kept.append(out)
        if len(kept) >= MEMORY_TOP_K:
            break

    if not kept:
        debug = {
            "topic_reset_detected": pivot_reset,
            "explicit_recall_detected": explicit_recall,
            "memories_retrieved": retrieved_n,
            "memories_injected": 0,
            "rejected_memory_reasons": rejected_reasons,
            "memory_relevance_threshold": MEMORY_RELEVANCE_THRESHOLD,
            "memory_top_k": MEMORY_TOP_K,
        }
        return [], debug

    best_score = float(kept[0].get("_guard_relevance_score", 0.0))
    debug = {
        "topic_reset_detected": pivot_reset,
        "explicit_recall_detected": explicit_recall,
        "memories_retrieved": retrieved_n,
        "memories_injected": len(kept),
        "rejected_memory_reasons": rejected_reasons,
        "best_relevance_score": round(best_score, 4),
        "memory_relevance_threshold": MEMORY_RELEVANCE_THRESHOLD,
        "memory_top_k": MEMORY_TOP_K,
    }
    return kept, debug


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
