"""Tests for Dual Mode System (Structure vs Reflect) selection and guidance."""

from src.core.dual_mode import (
    build_dual_mode_guidance,
    hits_explanation_intent,
    select_response_shape_mode,
)


def test_leaflink_always_structure():
    assert (
        select_response_shape_mode(
            "hello",
            is_leaflink=True,
            has_document_context=False,
        )
        == "structure"
    )


def test_leaflink_overrides_explain_keyword():
    assert (
        select_response_shape_mode(
            "explain this note",
            is_leaflink=True,
            has_document_context=False,
        )
        == "structure"
    )


def test_document_defaults_reflect():
    assert (
        select_response_shape_mode(
            "what does the file say",
            is_leaflink=False,
            has_document_context=True,
        )
        == "reflect"
    )


def test_summarize_forces_structure_with_doc():
    assert (
        select_response_shape_mode(
            "Summarize in bullets",
            is_leaflink=False,
            has_document_context=True,
        )
        == "structure"
    )


def test_explain_forces_reflect_with_doc():
    assert (
        select_response_shape_mode(
            "Explain this document",
            is_leaflink=False,
            has_document_context=True,
        )
        == "reflect"
    )


def test_plain_chat_no_dual_mode():
    assert (
        select_response_shape_mode(
            "Hello there",
            is_leaflink=False,
            has_document_context=False,
        )
        is None
    )


def test_explain_keyword_reflect_without_doc():
    assert (
        select_response_shape_mode(
            "Explain recursion simply",
            is_leaflink=False,
            has_document_context=False,
        )
        == "reflect"
    )


def test_conflict_bullets_win_structure():
    assert (
        select_response_shape_mode(
            "Explain the main ideas in bullets",
            is_leaflink=False,
            has_document_context=True,
        )
        == "structure"
    )


def test_structure_guidance_reuses_capture_for_leaflink():
    g = build_dual_mode_guidance("structure", {"leaflink": True})
    assert "Capture Mode v2" in g
    assert "LeafLink" in g


def test_structure_guidance_non_leaflink():
    g = build_dual_mode_guidance("structure", {"leaflink": False})
    assert "Structure Mode" in g
    assert "Capture Mode" not in g


def test_reflect_guidance():
    g = build_dual_mode_guidance("reflect", {})
    assert "Reflect Mode" in g
    assert "paragraph" in g.lower() or "narrative" in g.lower()


def test_what_should_i_forces_structure():
    assert (
        select_response_shape_mode(
            "What should I do about this leak?",
            is_leaflink=False,
            has_document_context=False,
        )
        == "structure"
    )


def test_what_should_i_forces_structure_even_with_document_context():
    assert (
        select_response_shape_mode(
            "What should I do with this file?",
            is_leaflink=False,
            has_document_context=True,
        )
        == "structure"
    )


def test_medication_phrase_forces_structure():
    assert (
        select_response_shape_mode(
            "Is this dosage okay?",
            is_leaflink=False,
            has_document_context=True,
        )
        == "structure"
    )


def test_explain_medication_still_structure_over_reflect_keyword():
    assert (
        select_response_shape_mode(
            "Explain which medication might help my headache",
            is_leaflink=False,
            has_document_context=True,
        )
        == "structure"
    )


def test_structure_non_leaflink_includes_action_first():
    g = build_dual_mode_guidance("structure", {"leaflink": False})
    assert "action-first" in g.lower() or "Action-first" in g
    assert "Main thing is" in g or "Start with" in g


def test_what_is_reflect_without_doc():
    assert (
        select_response_shape_mode(
            "What is a hash table?",
            is_leaflink=False,
            has_document_context=False,
        )
        == "reflect"
    )


def test_hits_explanation_intent_true_for_what_is():
    assert hits_explanation_intent("What is Docker?")


def test_hits_explanation_intent_false_when_practical():
    assert not hits_explanation_intent("What is the dosage for this?")


def test_reflect_guidance_mentions_simple_first():
    g = build_dual_mode_guidance("reflect", {})
    assert "plain-language" in g.lower() or "short" in g.lower()
    assert "invitation" in g.lower() or "deeper" in g.lower()
