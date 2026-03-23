"""LeafLink CLI / viewer behavior — no WhisperLeaf memory/chat/search imports."""

import tempfile
from pathlib import Path

from src.core.leaflink.inbox import LeafLinkInbox
from src.core.leaflink.promote import LeafLinkPromoter
from src.core.leaflink.schemas import LeafLinkItemState, LeafLinkItemType, new_leaflink_item
from src.core.leaflink.viewer import (
    DestructiveActionNotConfirmed,
    LeafLinkViewer,
    main,
    placeholder_summarize,
)


def _viewer_with_items() -> LeafLinkViewer:
    inbox = LeafLinkInbox()
    item = new_leaflink_item(
        device_id="d1",
        item_type=LeafLinkItemType.NOTE,
        title="T1",
        content_text="First. Second sentence. Third!",
        metadata={"k": "v"},
    )
    inbox.add_item(item)
    promoter = LeafLinkPromoter(inbox)
    return LeafLinkViewer(inbox=inbox, promoter=promoter)


def test_viewer_lists_items() -> None:
    v = _viewer_with_items()
    items = v.list_items()
    assert len(items) == 1
    table = v.format_list_table(items)
    assert items[0].item_id in table
    assert "note" in table


def test_viewer_opens_item_details() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    detail = v.format_item_detail(v.get_item(iid))  # type: ignore[arg-type]
    assert iid in detail
    assert "First." in detail
    assert '"k"' in detail or "k" in detail


def test_summarize_preview_only_no_state_change() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    before = v.get_item(iid)
    assert before is not None and before.state == LeafLinkItemState.RECEIVED
    text = v.summarize_preview(iid)
    assert "PLACEHOLDER PREVIEW" in text
    assert "First." in placeholder_summarize(before.content_text)
    after = v.get_item(iid)
    assert after is not None
    assert after.state == LeafLinkItemState.RECEIVED
    assert after.metadata == before.metadata


def test_review_changes_state() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    u = v.review(iid)
    assert u.state == LeafLinkItemState.REVIEWED
    assert u.reviewed_at is not None


def test_promotions_use_promoter_path() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    v.review(iid)
    r = v.promote_to_chat(iid)
    assert r.success is True
    assert v.get_item(iid) and v.get_item(iid).state == LeafLinkItemState.PROMOTED_TO_CHAT


def test_archive_delete_require_confirmation() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    try:
        v.archive(iid, confirmed=False)
        raise AssertionError("expected DestructiveActionNotConfirmed")
    except DestructiveActionNotConfirmed as e:
        assert e.action == "archive"
    try:
        v.delete(iid, confirmed=False)
        raise AssertionError("expected DestructiveActionNotConfirmed")
    except DestructiveActionNotConfirmed as e:
        assert e.action == "delete"


def test_archive_with_confirmed_works() -> None:
    v = _viewer_with_items()
    iid = v.list_items()[0].item_id
    a = v.archive(iid, confirmed=True)
    assert a.state == LeafLinkItemState.ARCHIVED


def test_cli_main_list_runs() -> None:
    with tempfile.TemporaryDirectory() as td:
        inbox_path = Path(td) / "inbox.json"
        inbox = LeafLinkInbox(persistence_path=inbox_path)
        inbox.add_item(
            new_leaflink_item(
                device_id="d",
                item_type=LeafLinkItemType.NOTE,
                content_text="x",
            )
        )
        import io

        out = io.StringIO()
        code = main(["--inbox", str(inbox_path), "list"], stdout=out)
        assert code == 0
        assert "item_id" in out.getvalue()


def test_viewer_no_import_of_whisperleaf_memory_stack() -> None:
    import src.core.leaflink.viewer as viewer_mod

    src = Path(viewer_mod.__file__).read_text(encoding="utf-8")
    assert "memory_manager" not in src
    assert "vector_store" not in src
    assert "chat_engine" not in src
