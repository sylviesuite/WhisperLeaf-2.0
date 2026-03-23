"""
LeafLink must not auto-integrate with memory, search, or chat.

Behavioral tests only — no imports from memory_injection_guard or vector store.
"""

from src.core.leaflink.inbox import LeafLinkInbox
from src.core.leaflink.pairing import PairingRegistry
from src.core.leaflink.errors import UnpairedDeviceError
from src.core.leaflink.receiver import LeafLinkReceiver
from src.core.leaflink.schemas import LeafLinkItemState, LeafLinkItemType


def test_unpaired_device_submission_rejected() -> None:
    reg = PairingRegistry()
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    try:
        recv.receive_item("unknown", LeafLinkItemType.NOTE, content_text="nope")
        raise AssertionError("expected UnpairedDeviceError")
    except UnpairedDeviceError as e:
        assert e.device_id == "unknown"


def test_received_item_stored_only_in_inbox() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.NOTE, content_text="store me")
    assert inbox.get_item(item.item_id) is not None
    assert inbox.get_item(item.item_id).content_text == "store me"


def test_received_item_not_auto_promoted_to_memory() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.NOTE, content_text="m")
    assert item.state != LeafLinkItemState.PROMOTED_TO_MEMORY


def test_received_item_not_auto_marked_searchable() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.QUICK_PROMPT, content_text="q")
    assert item.state != LeafLinkItemState.INDEXED_FOR_SEARCH


def test_received_item_not_auto_added_to_chat() -> None:
    reg = PairingRegistry()
    reg.pair_device("p1", "Phone")
    inbox = LeafLinkInbox()
    recv = LeafLinkReceiver(reg, inbox)
    item = recv.receive_item("p1", LeafLinkItemType.VOICE_MEMO_TRANSCRIPT, content_text="v")
    assert item.state != LeafLinkItemState.PROMOTED_TO_CHAT
