"""
Dataset loader utilities for WhisperLeaf energy benchmarks.

This module focuses on a simple, deterministic way to load plain-text
benchmark documents for summarization workflows. It is intentionally
decoupled from any model or UI logic so it can be reused by multiple
benchmark scripts (for example, ``energy_summary_benchmark.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET_DIR = BENCHMARK_DIR / "dataset"


@dataclass
class DatasetDocument:
    """Represents a single benchmark document."""

    document_id: str
    filename: str
    text: str
    word_count: int


def _count_words(text: str) -> int:
    """Simple whitespace-based word count."""
    # Split on any whitespace; empty strings are ignored by split().
    return len(text.split())


def iter_dataset_documents() -> Iterable[DatasetDocument]:
    """
    Iterate over .txt documents in ``benchmarks/dataset`` in a deterministic order.

    - Only ``*.txt`` files are included.
    - Files are sorted lexicographically by name for stable ordering.
    - Each yielded item includes the full text and word count.
    - Logs filename and word count to stdout for traceability.
    """
    if not DATASET_DIR.exists():
        return []

    paths: List[Path] = sorted(DATASET_DIR.glob("*.txt"), key=lambda p: p.name)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        word_count = _count_words(text)
        document_id = path.stem
        print(f"[dataset] {path.name}: {word_count} words")
        yield DatasetDocument(
            document_id=document_id,
            filename=path.name,
            text=text,
            word_count=word_count,
        )


def load_dataset() -> List[DatasetDocument]:
    """
    Load all dataset documents into memory as a list.

    This is a convenience wrapper around ``iter_dataset_documents`` for
    benchmark scripts that prefer a materialized collection.
    """
    return list(iter_dataset_documents())

