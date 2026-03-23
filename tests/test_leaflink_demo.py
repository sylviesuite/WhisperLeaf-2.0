"""Smoke tests for the LeafLink demo runner."""

from __future__ import annotations

import io

from scripts.demo_leaflink import run_demo_flow
from src.core.leaflink.schemas import LeafLinkItemState


def test_demo_runs_without_exceptions() -> None:
    out = io.StringIO()
    result = run_demo_flow(out=out)
    assert result["promoted_success"] is True
    text = out.getvalue()
    assert "Paired device:" in text
    assert "Inbox contains 2 items" in text


def test_demo_item_state_progression() -> None:
    out = io.StringIO()
    result = run_demo_flow(out=out)
    received = result["received_items"]
    final_items = result["final_items"]
    text = out.getvalue().lower()
    assert len(received) == 2
    # Script output proves first observed state is RECEIVED before explicit promotion.
    assert "received item:" in text and "state=received" in text
    assert any(i.state == LeafLinkItemState.PROMOTED_TO_MEMORY for i in final_items)
    assert any(i.state == LeafLinkItemState.RECEIVED for i in final_items)

