"""Unit tests for InsightBox mode-aware guidance."""

from __future__ import annotations

from pathlib import Path

from src.core.insight_box import build_mode_guidance
from src.core.mode_router import ResponseMode


def test_conversational_guidance_discourages_task_spec() -> None:
    g = build_mode_guidance(ResponseMode.CONVERSATIONAL).lower()
    assert "conversational" in g
    assert "task-spec" in g or "task spec" in g
    assert "objective" not in g
    assert "requirements" not in g
    assert "files" not in g
    assert "tests" not in g


def test_creative_guidance_discourages_engineering_spec() -> None:
    g = build_mode_guidance(ResponseMode.CREATIVE).lower()
    assert "creative" in g
    # Should explicitly discourage planning/spec docs.
    assert "task spec" in g or "engineering task spec" in g
    # Should not suggest engineering scaffolding language by default.
    assert "objective" not in g
    assert "requirements" not in g
    assert "files" not in g
    assert "tests" not in g


def test_task_dev_guidance_allows_structured_output() -> None:
    g = build_mode_guidance(ResponseMode.TASK_DEV).lower()
    assert "task_dev" in g or "task_dev" in str(ResponseMode.TASK_DEV)
    assert "structured" in g
    assert "implementation" in g
    assert "steps" in g
    # Allowed when relevant.
    assert "files" in g
    assert "tests" in g


def test_prompt_assembly_includes_insightbox_guidance() -> None:
    # Lightweight check: main.py must reference the InsightBox guidance builder.
    main_path = Path(__file__).resolve().parents[1] / "src" / "core" / "main.py"
    src = main_path.read_text(encoding="utf-8")
    assert "insight_box_guidance = build_mode_guidance(response_mode)" in src


def test_mode_guidance_is_additive_only() -> None:
    # Creative and conversational modes should not contain structured engineering scaffolding instructions.
    conv = build_mode_guidance(ResponseMode.CONVERSATIONAL).lower()
    creative = build_mode_guidance(ResponseMode.CREATIVE).lower()
    assert "include objective" not in conv
    assert "include objective" not in creative

