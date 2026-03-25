"""Tests for LeafLink Capture Mode detection (marker-based)."""

from src.core.capture_mode import build_capture_mode_guidance, is_leaflink_originated_message


def test_detects_leaflink_at_start():
    assert is_leaflink_originated_message("[LeafLink — Grocery]\nMilk, eggs")


def test_detects_leaflink_after_newline():
    assert is_leaflink_originated_message("prior line\n[LeafLink — Note]\nbody")


def test_detects_hyphen_marker_tolerant():
    assert is_leaflink_originated_message("[LeafLink - Note]\nbody")


def test_rejects_plain_chat():
    assert not is_leaflink_originated_message("Hello, how are you?")


def test_rejects_mid_string_marker_not_at_line_start():
    # Mid-sentence mention should not trigger (no newline before marker)
    assert not is_leaflink_originated_message('Say "[LeafLink — fake]" in a story')


def test_guidance_mentions_capture_mode():
    g = build_capture_mode_guidance()
    assert "Capture Mode v2" in g
    assert "LeafLink" in g
    assert "100" in g and "120" in g  # verbosity guard (words)
    assert "checklist" in g.lower()
    assert "tool" in g.lower()
