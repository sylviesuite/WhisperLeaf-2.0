"""
LeafLink V1 — private paired-device inbox with explicit promotion.

Public API for imports: pairing, inbox, receive, promote, schemas.
"""

from .errors import UnpairedDeviceError
from .inbox import LeafLinkInbox
from .pairing import PairingRegistry
from .promote import LeafLinkPromoter, PromotionResult
from .receiver import LeafLinkReceiver
from .schemas import (
    LeafLinkItem,
    LeafLinkItemState,
    LeafLinkItemType,
    PairedDevice,
    new_leaflink_item,
    new_paired_device,
    utc_now,
)
from .viewer import DestructiveActionNotConfirmed, LeafLinkViewer, main, main_argv, placeholder_summarize

__all__ = [
    "DestructiveActionNotConfirmed",
    "LeafLinkInbox",
    "LeafLinkItem",
    "LeafLinkItemState",
    "LeafLinkItemType",
    "LeafLinkPromoter",
    "LeafLinkReceiver",
    "LeafLinkViewer",
    "PairedDevice",
    "PairingRegistry",
    "PromotionResult",
    "UnpairedDeviceError",
    "main",
    "main_argv",
    "new_leaflink_item",
    "new_paired_device",
    "placeholder_summarize",
    "utc_now",
]
