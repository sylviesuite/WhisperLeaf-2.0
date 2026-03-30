"""
Local LeafLink inbox — storage only.

- Persistence: optional JSON file on the **local filesystem** only (no cloud URLs, no vector DB).
- Does not index for search, does not import or call WhisperLeaf memory, chat, or vector_store.
- ``add_item`` is a low-level store; **inbound user/device data** should enter via
  ``LeafLinkReceiver.receive_item`` so pairing is enforced.

TODO: Optional SQLite backend for large inboxes (still local-only).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import (
    LeafLinkItem,
    LeafLinkItemState,
    leaflink_item_from_dict,
    leaflink_item_to_dict,
    utc_now,
)


class LeafLinkInbox:
    """Stores LeafLink items in memory with optional JSON persistence."""

    def __init__(self, persistence_path: Path | None = None) -> None:
        self._path: Path | None = persistence_path
        self._items: dict[str, LeafLinkItem] = {}
        if self._path and self._path.exists():
            self._load()

    def _load(self) -> None:
        if not self._path or not self._path.exists():
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        for row in raw.get("items", []):
            item = leaflink_item_from_dict(row)
            self._items[item.item_id] = item

    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {"items": [leaflink_item_to_dict(i) for i in self._items.values()]}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_item(self, item: LeafLinkItem) -> LeafLinkItem:
        """Insert or replace an item by id. Does not verify device pairing (use LeafLinkReceiver for ingest)."""
        self._items[item.item_id] = item
        self._save()
        return item

    def get_item(self, item_id: str) -> LeafLinkItem | None:
        return self._items.get(item_id)

    def list_items(self, state: LeafLinkItemState | None = None) -> list[LeafLinkItem]:
        items = list(self._items.values())
        if state is None:
            return sorted(items, key=lambda i: i.created_at, reverse=True)
        return sorted([i for i in items if i.state == state], key=lambda i: i.created_at, reverse=True)

    def mark_reviewed(self, item_id: str) -> LeafLinkItem:
        item = self._get_required(item_id)
        item.state = LeafLinkItemState.REVIEWED
        item.reviewed_at = utc_now()
        self._save()
        return item

    def archive_item(self, item_id: str) -> LeafLinkItem:
        item = self._get_required(item_id)
        item.state = LeafLinkItemState.ARCHIVED
        self._save()
        return item

    def delete_item(self, item_id: str) -> LeafLinkItem:
        item = self._get_required(item_id)
        item.state = LeafLinkItemState.DELETED
        self._save()
        return item

    def _get_required(self, item_id: str) -> LeafLinkItem:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"unknown item_id: {item_id!r}")
        return item
