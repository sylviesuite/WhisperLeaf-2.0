"""
Explicit promotion out of the LeafLink inbox.

Architecture: receive -> inbox -> explicit promotion only. No automatic side effects.

State transitions and adapter hooks only — **no** imports from memory_manager, vector_store,
chat routes, or memory_injection_guard in V1.

TODO: Replace adapter bodies with real WhisperLeaf integrations (explicit user action only).
"""

from __future__ import annotations

from dataclasses import dataclass

from .inbox import LeafLinkInbox
from .schemas import LeafLinkItem, LeafLinkItemState, utc_now


@dataclass(frozen=True)
class PromotionResult:
    """Outcome of a promotion attempt."""

    success: bool
    message: str
    item_id: str
    item: LeafLinkItem | None


class LeafLinkPromoter:
    """
    Promotes inbox items only after explicit calls.

    V1: requires ``REVIEWED`` state before any promotion (user has acknowledged the item).
    """

    def __init__(self, inbox: LeafLinkInbox) -> None:
        self._inbox = inbox

    def _require_reviewed(self, item: LeafLinkItem) -> PromotionResult | None:
        if item.state != LeafLinkItemState.REVIEWED:
            return PromotionResult(
                success=False,
                message="promotion requires item in REVIEWED state",
                item_id=item.item_id,
                item=item,
            )
        return None

    def promote_to_chat(self, item_id: str) -> PromotionResult:
        item = self._inbox.get_item(item_id)
        if item is None:
            return PromotionResult(success=False, message="item not found", item_id=item_id, item=None)
        blocked = self._require_reviewed(item)
        if blocked:
            return blocked
        self._send_to_chat_adapter(item)
        item.state = LeafLinkItemState.PROMOTED_TO_CHAT
        item.promoted_at = utc_now()
        self._inbox.add_item(item)
        return PromotionResult(success=True, message="promoted_to_chat", item_id=item_id, item=item)

    def promote_to_memory(self, item_id: str) -> PromotionResult:
        item = self._inbox.get_item(item_id)
        if item is None:
            return PromotionResult(success=False, message="item not found", item_id=item_id, item=None)
        blocked = self._require_reviewed(item)
        if blocked:
            return blocked
        self._store_in_memory_adapter(item)
        item.state = LeafLinkItemState.PROMOTED_TO_MEMORY
        item.promoted_at = utc_now()
        self._inbox.add_item(item)
        return PromotionResult(success=True, message="promoted_to_memory", item_id=item_id, item=item)

    def mark_searchable(self, item_id: str) -> PromotionResult:
        item = self._inbox.get_item(item_id)
        if item is None:
            return PromotionResult(success=False, message="item not found", item_id=item_id, item=None)
        blocked = self._require_reviewed(item)
        if blocked:
            return blocked
        self._index_for_search_adapter(item)
        item.state = LeafLinkItemState.INDEXED_FOR_SEARCH
        item.promoted_at = utc_now()
        self._inbox.add_item(item)
        return PromotionResult(success=True, message="indexed_for_search", item_id=item_id, item=item)

    def _send_to_chat_adapter(self, item: LeafLinkItem) -> None:
        # TODO(adapter): Wire to chat UI / API after promotion — e.g. pre-fill composer or POST /api/chat.
        # Intentionally no import from main.py or chat_engine here in V1.
        _ = item

    def _store_in_memory_adapter(self, item: LeafLinkItem) -> None:
        # TODO(adapter): Call save_memory() or equivalent from memory layer — only after this promotion path.
        # Intentionally no import from memory_manager / memory module here in V1.
        _ = item

    def _index_for_search_adapter(self, item: LeafLinkItem) -> None:
        # TODO(adapter): Call document_processor + vector_store ingest — only after explicit mark_searchable.
        # Intentionally no import from vector_store here in V1.
        _ = item
