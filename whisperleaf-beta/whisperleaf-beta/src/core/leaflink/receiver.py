"""
Receive path for LeafLink — paired devices only, inbox storage only.

Inbound submissions must call ``receive_item`` (or ``PairingRegistry.require_paired`` before any
custom ingest). Do not push items into the inbox from network handlers without that check.

LeafLink can submit, but it cannot decide.

TODO: HTTP/WebSocket ingest layer calling receive_item() after transport auth.
"""

from __future__ import annotations

from typing import Any

from .errors import UnpairedDeviceError  # re-export for callers that import from receiver
from .inbox import LeafLinkInbox
from .pairing import PairingRegistry
from .schemas import LeafLinkItem, LeafLinkItemState, LeafLinkItemType, new_leaflink_item


class LeafLinkReceiver:
    """Accepts items only from paired devices; stores in the inbox only."""

    def __init__(self, registry: PairingRegistry, inbox: LeafLinkInbox) -> None:
        self._registry = registry
        self._inbox = inbox

    def receive_item(
        self,
        device_id: str,
        item_type: LeafLinkItemType,
        title: str | None = None,
        content_text: str | None = None,
        source_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LeafLinkItem:
        self._registry.require_paired(device_id)
        item = new_leaflink_item(
            device_id=device_id,
            item_type=item_type,
            title=title,
            content_text=content_text,
            source_path=source_path,
            metadata=metadata,
            state=LeafLinkItemState.RECEIVED,
        )
        return self._inbox.add_item(item)
