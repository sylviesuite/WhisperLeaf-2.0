"""
LeafLink V1 data shapes.

Design principle: LeafLink can submit, but it cannot decide.

TODO: Wire serialization to a single schema version field when evolving the on-disk format.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    """Timezone-aware UTC "now" for LeafLink records."""
    return datetime.now(timezone.utc)


class LeafLinkItemType(str, Enum):
    NOTE = "note"
    VOICE_MEMO_TRANSCRIPT = "voice_memo_transcript"
    PHOTO_DOC = "photo_doc"
    QUICK_PROMPT = "quick_prompt"


class LeafLinkItemState(str, Enum):
    RECEIVED = "received"
    REVIEWED = "reviewed"
    PROMOTED_TO_CHAT = "promoted_to_chat"
    PROMOTED_TO_MEMORY = "promoted_to_memory"
    INDEXED_FOR_SEARCH = "indexed_for_search"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class PairedDevice:
    """A locally registered paired device (phone, etc.)."""

    device_id: str
    device_name: str
    public_label: str | None
    is_active: bool
    created_at: datetime


@dataclass
class LeafLinkItem:
    """A single item in the LeafLink inbox."""

    item_id: str
    device_id: str
    item_type: LeafLinkItemType
    title: str | None
    content_text: str | None
    source_path: str | None
    metadata: dict[str, Any]
    state: LeafLinkItemState
    created_at: datetime
    reviewed_at: datetime | None = None
    promoted_at: datetime | None = None


def new_paired_device(
    device_id: str,
    device_name: str,
    public_label: str | None = None,
    *,
    is_active: bool = True,
    created_at: datetime | None = None,
) -> PairedDevice:
    """Construct a PairedDevice with validation."""
    did = (device_id or "").strip()
    if not did:
        raise ValueError("device_id must be non-empty")
    name = (device_name or "").strip()
    if not name:
        raise ValueError("device_name must be non-empty")
    return PairedDevice(
        device_id=did,
        device_name=name,
        public_label=(public_label.strip() if public_label else None) or None,
        is_active=is_active,
        created_at=created_at or utc_now(),
    )


def new_leaflink_item(
    *,
    device_id: str,
    item_type: LeafLinkItemType,
    title: str | None = None,
    content_text: str | None = None,
    source_path: str | None = None,
    metadata: dict[str, Any] | None = None,
    state: LeafLinkItemState = LeafLinkItemState.RECEIVED,
    item_id: str | None = None,
    created_at: datetime | None = None,
) -> LeafLinkItem:
    """Create a new inbox item; default state is RECEIVED."""
    did = (device_id or "").strip()
    if not did:
        raise ValueError("device_id must be non-empty")
    iid = (item_id or "").strip() or str(uuid.uuid4())
    meta = dict(metadata) if metadata else {}
    return LeafLinkItem(
        item_id=iid,
        device_id=did,
        item_type=item_type,
        title=title.strip() if title else None,
        content_text=content_text,
        source_path=source_path.strip() if source_path else None,
        metadata=meta,
        state=state,
        created_at=created_at or utc_now(),
        reviewed_at=None,
        promoted_at=None,
    )


# --- JSON helpers (local persistence only) ---


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def paired_device_to_dict(d: PairedDevice) -> dict[str, Any]:
    return {
        "device_id": d.device_id,
        "device_name": d.device_name,
        "public_label": d.public_label,
        "is_active": d.is_active,
        "created_at": _iso(d.created_at),
    }


def paired_device_from_dict(data: dict[str, Any]) -> PairedDevice:
    return PairedDevice(
        device_id=str(data["device_id"]),
        device_name=str(data["device_name"]),
        public_label=data.get("public_label"),
        is_active=bool(data.get("is_active", True)),
        created_at=_parse_dt(str(data["created_at"])),
    )


def leaflink_item_to_dict(item: LeafLinkItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "device_id": item.device_id,
        "item_type": item.item_type.value,
        "title": item.title,
        "content_text": item.content_text,
        "source_path": item.source_path,
        "metadata": item.metadata,
        "state": item.state.value,
        "created_at": _iso(item.created_at),
        "reviewed_at": _iso(item.reviewed_at) if item.reviewed_at else None,
        "promoted_at": _iso(item.promoted_at) if item.promoted_at else None,
    }


def leaflink_item_from_dict(data: dict[str, Any]) -> LeafLinkItem:
    return LeafLinkItem(
        item_id=str(data["item_id"]),
        device_id=str(data["device_id"]),
        item_type=LeafLinkItemType(str(data["item_type"])),
        title=data.get("title"),
        content_text=data.get("content_text"),
        source_path=data.get("source_path"),
        metadata=dict(data.get("metadata") or {}),
        state=LeafLinkItemState(str(data["state"])),
        created_at=_parse_dt(str(data["created_at"])),
        reviewed_at=_parse_dt(str(data["reviewed_at"])) if data.get("reviewed_at") else None,
        promoted_at=_parse_dt(str(data["promoted_at"])) if data.get("promoted_at") else None,
    )
