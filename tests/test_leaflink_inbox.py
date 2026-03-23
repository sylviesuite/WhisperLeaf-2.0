"""Inbox storage and state transitions."""

import tempfile
from pathlib import Path

from src.core.leaflink.inbox import LeafLinkInbox
from src.core.leaflink.schemas import LeafLinkItemState, LeafLinkItemType, new_leaflink_item


def test_inbox_stores_received_item() -> None:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(
        device_id="d1",
        item_type=LeafLinkItemType.NOTE,
        content_text="hello",
        state=LeafLinkItemState.RECEIVED,
    )
    out = inbox.add_item(item)
    assert out.item_id == item.item_id
    assert inbox.get_item(item.item_id) is not None


def test_item_lands_in_received_state() -> None:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(device_id="d1", item_type=LeafLinkItemType.QUICK_PROMPT, content_text="x")
    inbox.add_item(item)
    got = inbox.get_item(item.item_id)
    assert got is not None
    assert got.state == LeafLinkItemState.RECEIVED


def test_item_can_be_reviewed() -> None:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(device_id="d1", item_type=LeafLinkItemType.NOTE, content_text="a")
    inbox.add_item(item)
    updated = inbox.mark_reviewed(item.item_id)
    assert updated.state == LeafLinkItemState.REVIEWED
    assert updated.reviewed_at is not None


def test_item_can_be_archived() -> None:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(device_id="d1", item_type=LeafLinkItemType.NOTE, content_text="a")
    inbox.add_item(item)
    arch = inbox.archive_item(item.item_id)
    assert arch.state == LeafLinkItemState.ARCHIVED


def test_item_can_be_deleted() -> None:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(device_id="d1", item_type=LeafLinkItemType.NOTE, content_text="a")
    inbox.add_item(item)
    deleted = inbox.delete_item(item.item_id)
    assert deleted.state == LeafLinkItemState.DELETED


def test_file_persistence_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "inbox.json"
        inbox = LeafLinkInbox(persistence_path=path)
        item = new_leaflink_item(device_id="d1", item_type=LeafLinkItemType.NOTE, content_text="persist")
        inbox.add_item(item)
        inbox2 = LeafLinkInbox(persistence_path=path)
        assert inbox2.get_item(item.item_id) is not None
        assert inbox2.get_item(item.item_id).content_text == "persist"
