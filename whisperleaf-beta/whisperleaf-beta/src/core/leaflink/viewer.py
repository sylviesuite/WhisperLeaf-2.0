"""
LeafLink Inbox Viewer — minimal CLI / library surface for human review.

LeafLink is a review surface first, not an automation path.

Flow: receive -> inbox -> explicit user actions here (review, promote, archive, delete).
Does not call WhisperLeaf memory, vector search, or chat APIs.

Usage (CLI, from repository root):

  python -m src.core.leaflink list
  python -m src.core.leaflink open <item_id>
  python -m src.core.leaflink review <item_id>
  python -m src.core.leaflink summarize <item_id>
  python -m src.core.leaflink promote-chat <item_id>
  python -m src.core.leaflink promote-memory <item_id>
  python -m src.core.leaflink mark-searchable <item_id>
  python -m src.core.leaflink archive <item_id> --yes
  python -m src.core.leaflink delete <item_id> --yes

Environment:
  LEAFLINK_INBOX  Optional path to inbox JSON file (default: data/leaflink_inbox.json under project root).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import TextIO

from .inbox import LeafLinkInbox
from .promote import LeafLinkPromoter, PromotionResult
from .schemas import LeafLinkItem, LeafLinkItemState


class DestructiveActionNotConfirmed(Exception):
    """Raised when archive/delete are invoked without explicit confirmation."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(
            f"confirmation required for '{action}'; pass confirmed=True or use --yes on the CLI",
        )


def placeholder_summarize(
    content_text: str | None,
    *,
    max_chars: int = 400,
    max_sentences: int = 3,
) -> str:
    """
    Placeholder “summary”: first few sentences or first N characters of content_text.

    Does not call an LLM. Does not persist. Safe to display as a preview only.

    TODO: Swap for on-device summary model or user-edited summary when product-ready.
    """
    if not content_text or not content_text.strip():
        return "(no content_text — nothing to preview)"
    text = content_text.strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunk = " ".join(parts[:max_sentences]).strip()
    if not chunk:
        chunk = text
    if len(chunk) > max_chars:
        chunk = chunk[:max_chars].rstrip() + "…"
    return chunk


def default_inbox_path() -> Path:
    """Resolve default JSON path next to WhisperLeaf data dir if unset."""
    env = os.environ.get("LEAFLINK_INBOX", "").strip()
    if env:
        return Path(env)
    # src/core/leaflink/viewer.py -> parents[2] == project root when running from checkout
    here = Path(__file__).resolve()
    project_root = here.parents[2]
    return project_root / "data" / "leaflink_inbox.json"


class LeafLinkViewer:
    """
    Thin wrapper over ``LeafLinkInbox`` + ``LeafLinkPromoter`` for listing and explicit actions.

    Promotions always go through ``LeafLinkPromoter``; destructive inbox ops require confirmation.
    """

    def __init__(self, inbox: LeafLinkInbox, promoter: LeafLinkPromoter) -> None:
        self._inbox = inbox
        self._promoter = promoter

    @classmethod
    def from_paths(cls, inbox_path: Path | None = None) -> LeafLinkViewer:
        """Build viewer with file-backed inbox (if path set) and matching promoter."""
        path = inbox_path or default_inbox_path()
        inbox = LeafLinkInbox(persistence_path=path)
        return cls(inbox=inbox, promoter=LeafLinkPromoter(inbox))

    def list_items(self, state: LeafLinkItemState | None = None) -> list[LeafLinkItem]:
        return self._inbox.list_items(state=state)

    def get_item(self, item_id: str) -> LeafLinkItem | None:
        return self._inbox.get_item(item_id)

    def format_list_table(self, items: list[LeafLinkItem] | None = None) -> str:
        """Human-readable list (for CLI / logs)."""
        rows = items if items is not None else self.list_items()
        if not rows:
            return "(no items)\n"
        lines = []
        for it in rows:
            title = (it.title or "").replace("\n", " ")[:60]
            lines.append(
                f"{it.item_id}\t{it.item_type.value}\t{title}\t{it.device_id}\t{it.state.value}\t{it.created_at.isoformat()}",
            )
        header = "item_id\titem_type\ttitle\tdevice_id\tstate\tcreated_at\n"
        return header + "\n".join(lines) + "\n"

    def format_item_detail(self, item: LeafLinkItem) -> str:
        """Full detail block for one item."""
        meta = json.dumps(item.metadata, indent=2, ensure_ascii=False) if item.metadata else "{}"
        parts = [
            f"item_id:     {item.item_id}",
            f"device_id:   {item.device_id}",
            f"item_type:   {item.item_type.value}",
            f"state:       {item.state.value}",
            f"title:       {item.title!r}",
            f"created_at:  {item.created_at.isoformat()}",
            f"reviewed_at: {item.reviewed_at.isoformat() if item.reviewed_at else '—'}",
            f"promoted_at: {item.promoted_at.isoformat() if item.promoted_at else '—'}",
            f"source_path: {item.source_path!r}",
            "metadata:",
            meta,
            "content_text:",
            item.content_text if item.content_text is not None else "(none)",
        ]
        return "\n".join(parts) + "\n"

    def review(self, item_id: str) -> LeafLinkItem:
        """Mark item reviewed (inbox API)."""
        return self._inbox.mark_reviewed(item_id)

    def summarize_preview(self, item_id: str) -> str:
        """
        Return placeholder preview text only. Does **not** change item state or persist summary.

        TODO: Optional path to save user-approved summary into metadata — not implemented in V1.
        """
        item = self._inbox.get_item(item_id)
        if item is None:
            return ""
        body = placeholder_summarize(item.content_text)
        return (
            "[PLACEHOLDER PREVIEW — not saved; not sent to memory/chat/search]\n\n" + body + "\n"
        )

    def promote_to_chat(self, item_id: str) -> PromotionResult:
        return self._promoter.promote_to_chat(item_id)

    def promote_to_memory(self, item_id: str) -> PromotionResult:
        return self._promoter.promote_to_memory(item_id)

    def mark_searchable(self, item_id: str) -> PromotionResult:
        return self._promoter.mark_searchable(item_id)

    def archive(self, item_id: str, *, confirmed: bool = False) -> LeafLinkItem:
        if not confirmed:
            raise DestructiveActionNotConfirmed("archive")
        return self._inbox.archive_item(item_id)

    def delete(self, item_id: str, *, confirmed: bool = False) -> LeafLinkItem:
        if not confirmed:
            raise DestructiveActionNotConfirmed("delete")
        return self._inbox.delete_item(item_id)


def _print(out: TextIO, text: str) -> None:
    out.write(text)
    if not text.endswith("\n"):
        out.write("\n")


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None) -> int:
    """CLI entry. Returns process exit code."""
    out = stdout or sys.stdout
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="leaflink", description="LeafLink inbox viewer (minimal CLI)")
    parser.add_argument(
        "--inbox",
        type=Path,
        default=None,
        help="Path to inbox JSON (default: $LEAFLINK_INBOX or data/leaflink_inbox.json)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List inbox items")

    p_open = sub.add_parser("open", help="Show one item")
    p_open.add_argument("item_id")

    p_rev = sub.add_parser("review", help="Mark item reviewed")
    p_rev.add_argument("item_id")

    p_sum = sub.add_parser("summarize", help="Print placeholder preview (does not save)")
    p_sum.add_argument("item_id")

    for name, help_ in (
        ("promote-chat", "Promote to chat (state only; uses LeafLinkPromoter)"),
        ("promote-memory", "Promote to memory (state only)"),
        ("mark-searchable", "Mark searchable (state only)"),
    ):
        p = sub.add_parser(name.replace("-", "_"), help=help_)
        p.add_argument("item_id")

    p_arc = sub.add_parser("archive", help="Archive item (requires --yes)")
    p_arc.add_argument("item_id")
    p_arc.add_argument("--yes", action="store_true", help="Confirm destructive action")

    p_del = sub.add_parser("delete", help="Soft-delete item (requires --yes)")
    p_del.add_argument("item_id")
    p_del.add_argument("--yes", action="store_true", help="Confirm destructive action")

    args = parser.parse_args(argv)
    viewer = LeafLinkViewer.from_paths(args.inbox)

    try:
        if args.cmd == "list":
            _print(out, viewer.format_list_table())
            return 0
        if args.cmd == "open":
            item = viewer.get_item(args.item_id)
            if item is None:
                _print(out, f"not found: {args.item_id!r}")
                return 1
            _print(out, viewer.format_item_detail(item))
            return 0
        if args.cmd == "review":
            item = viewer.review(args.item_id)
            _print(out, f"reviewed: {item.item_id} state={item.state.value}")
            return 0
        if args.cmd == "summarize":
            text = viewer.summarize_preview(args.item_id)
            if not text:
                _print(out, f"not found: {args.item_id!r}")
                return 1
            _print(out, text)
            return 0
        if args.cmd == "promote_chat":
            r = viewer.promote_to_chat(args.item_id)
            return _emit_promotion(out, r)
        if args.cmd == "promote_memory":
            r = viewer.promote_to_memory(args.item_id)
            return _emit_promotion(out, r)
        if args.cmd == "mark_searchable":
            r = viewer.mark_searchable(args.item_id)
            return _emit_promotion(out, r)
        if args.cmd == "archive":
            if not args.yes:
                _print(out, "error: archive requires --yes")
                return 2
            item = viewer.archive(args.item_id, confirmed=True)
            _print(out, f"archived: {item.item_id} state={item.state.value}")
            return 0
        if args.cmd == "delete":
            if not args.yes:
                _print(out, "error: delete requires --yes")
                return 2
            item = viewer.delete(args.item_id, confirmed=True)
            _print(out, f"deleted (soft): {item.item_id} state={item.state.value}")
            return 0
    except KeyError as e:
        _print(out, str(e))
        return 1
    except DestructiveActionNotConfirmed as e:
        _print(out, str(e))
        return 2

    _print(out, f"unknown command: {args.cmd!r}")
    return 1


def _emit_promotion(out: TextIO, r: PromotionResult) -> int:
    if r.success:
        _print(out, f"ok: {r.message} item_id={r.item_id}")
        return 0
    _print(out, f"failed: {r.message} item_id={r.item_id}")
    return 1


# Fix CLI: user asked for promote-chat with hyphen — argparse subparser used promote_chat
# We'll use a second parser pass or normalize argv. Easiest: document both; add alternate main
# that maps promote-chat -> promote_chat

def main_argv(argv: list[str] | None = None, *, stdout: TextIO | None = None) -> int:
    """Like main() but normalizes hyphenated subcommands (e.g. promote-chat -> promote_chat)."""
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        raw = ["--help"]
    aliases = {
        "promote-chat": "promote_chat",
        "promote-memory": "promote_memory",
        "mark-searchable": "mark_searchable",
    }
    # Subcommand is first arg unless global --inbox comes first (unlikely); handle first token only
    idx = 0
    if raw[0] == "--inbox" and len(raw) >= 3:
        idx = 2  # subcommand after --inbox path
    if idx < len(raw) and raw[idx] in aliases:
        raw[idx] = aliases[raw[idx]]
    return main(raw, stdout=stdout)
