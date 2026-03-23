"""Explicit promotion API and REVIEWED gate."""

from src.core.leaflink.inbox import LeafLinkInbox
from src.core.leaflink.pairing import PairingRegistry
from src.core.leaflink.promote import LeafLinkPromoter
from src.core.leaflink.receiver import LeafLinkReceiver
from src.core.leaflink.schemas import LeafLinkItemState, LeafLinkItemType


def _reviewed_note() -> tuple[LeafLinkInbox, str]:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.NOTE, title="t", content_text="body")
    inbox.mark_reviewed(item.item_id)
    return inbox, item.item_id


def test_explicit_promote_to_chat_works() -> None:
    inbox, iid = _reviewed_note()
    prom = LeafLinkPromoter(inbox)
    res = prom.promote_to_chat(iid)
    assert res.success is True
    assert res.item is not None
    assert res.item.state == LeafLinkItemState.PROMOTED_TO_CHAT


def test_explicit_promote_to_memory_works() -> None:
    inbox, iid = _reviewed_note()
    prom = LeafLinkPromoter(inbox)
    res = prom.promote_to_memory(iid)
    assert res.success is True
    assert res.item is not None
    assert res.item.state == LeafLinkItemState.PROMOTED_TO_MEMORY


def test_explicit_mark_searchable_works() -> None:
    inbox, iid = _reviewed_note()
    prom = LeafLinkPromoter(inbox)
    res = prom.mark_searchable(iid)
    assert res.success is True
    assert res.item is not None
    assert res.item.state == LeafLinkItemState.INDEXED_FOR_SEARCH


def test_promotion_changes_state_only_through_explicit_call() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.NOTE, content_text="x")
    assert item.state == LeafLinkItemState.RECEIVED
    # No promoter called — state unchanged
    assert inbox.get_item(item.item_id).state == LeafLinkItemState.RECEIVED


def test_review_required_before_promotion() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.NOTE, content_text="no review")
    prom = LeafLinkPromoter(inbox)
    res = prom.promote_to_chat(item.item_id)
    assert res.success is False
    assert "REVIEWED" in res.message
    assert inbox.get_item(item.item_id).state == LeafLinkItemState.RECEIVED
