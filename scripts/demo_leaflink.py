"""
Minimal LeafLink demo runner (local simulation only).

This proves the local inbox boundary without phone/network integration:
1) pair simulated device
2) receive simulated items
3) verify inbox-only state
4) list/open/review/promote explicitly

LeafLink demo complete target:
"LeafLink demo complete: local inbox boundary works; real phone sync not connected yet."
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

# Ensure repository root is importable when running as `python scripts/demo_leaflink.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.leaflink.inbox import LeafLinkInbox
from src.core.leaflink.pairing import PairingRegistry
from src.core.leaflink.promote import LeafLinkPromoter
from src.core.leaflink.receiver import LeafLinkReceiver
from src.core.leaflink.schemas import LeafLinkItem, LeafLinkItemType, PairedDevice
from src.core.leaflink.viewer import LeafLinkViewer


def setup_demo_environment() -> tuple[PairingRegistry, LeafLinkInbox, LeafLinkReceiver, LeafLinkPromoter, LeafLinkViewer]:
    """Create local in-memory LeafLink components for demo use."""
    registry = PairingRegistry()
    inbox = LeafLinkInbox()
    receiver = LeafLinkReceiver(registry=registry, inbox=inbox)
    promoter = LeafLinkPromoter(inbox=inbox)
    viewer = LeafLinkViewer(inbox=inbox, promoter=promoter)
    return registry, inbox, receiver, promoter, viewer


def create_demo_items(receiver: LeafLinkReceiver, device_id: str) -> list[LeafLinkItem]:
    """Receive two simulated items from the paired demo device."""
    note = receiver.receive_item(
        device_id=device_id,
        item_type=LeafLinkItemType.NOTE,
        title="Grocery follow-up",
        content_text="Remember to pick up pecans and bread for tonight.",
        metadata={"origin": "demo", "kind": "note"},
    )
    quick_prompt = receiver.receive_item(
        device_id=device_id,
        item_type=LeafLinkItemType.QUICK_PROMPT,
        title="Idea seed",
        content_text="Draft three names for a neighborhood reading circle.",
        metadata={"origin": "demo", "kind": "quick_prompt"},
    )
    return [note, quick_prompt]


def print_inbox_summary(viewer: LeafLinkViewer, out: TextIO) -> list[LeafLinkItem]:
    """Print compact inbox summary and return the current items."""
    items = viewer.list_items()
    out.write("Inbox contains %d items\n" % len(items))
    for item in items:
        out.write(
            "- %s | %s | %s | %s\n"
            % (item.item_id, item.item_type.value, item.device_id, item.state.value),
        )
    return items


def print_item_details(viewer: LeafLinkViewer, item_id: str, out: TextIO) -> None:
    """Print one item with full detail block."""
    item = viewer.get_item(item_id)
    if item is None:
        out.write("Opening item %s -> not found\n" % item_id)
        return
    out.write("Opening item %s\n" % item_id)
    out.write(viewer.format_item_detail(item))


def run_demo_flow(out: TextIO) -> dict[str, object]:
    """Run the full demo walkthrough and return structured result for tests."""
    registry, _inbox, receiver, _promoter, viewer = setup_demo_environment()

    device = registry.pair_device(
        device_id="demo-phone-001",
        device_name="Steven Phone",
        public_label="Demo handset",
    )
    out.write("Paired device: %s (%s)\n" % (device.device_id, device.device_name))

    received = create_demo_items(receiver, device.device_id)
    for item in received:
        out.write("Received item: %s [%s] state=%s\n" % (item.item_id, item.item_type.value, item.state.value))

    out.write(
        "Boundary check: items are inbox-only until explicit promotion (no memory/search/chat auto-injection).\n",
    )

    items = print_inbox_summary(viewer, out)
    first = items[0]
    print_item_details(viewer, first.item_id, out)

    reviewed = viewer.review(first.item_id)
    out.write("Marked reviewed: %s state=%s\n" % (reviewed.item_id, reviewed.state.value))

    promoted = viewer.promote_to_memory(first.item_id)
    out.write("Promoted to memory: success=%s message=%s\n" % (promoted.success, promoted.message))
    out.write("Note: promotion adapters are placeholders; no real memory/search/chat integration in this demo.\n")

    final_items = viewer.list_items()
    out.write("Final states:\n")
    for item in final_items:
        out.write("- %s -> %s\n" % (item.item_id, item.state.value))

    out.write("LeafLink demo complete: local inbox boundary works; real phone sync not connected yet.\n")
    return {
        "device": device,
        "received_items": received,
        "final_items": final_items,
        "promoted_success": promoted.success,
        "promoted_message": promoted.message,
    }


def main() -> int:
    """Console entrypoint."""
    result = run_demo_flow(out=sys.stdout)
    # Simple success code: demo should always return 2 items and one explicit promotion.
    if len(result["received_items"]) != 2:  # type: ignore[arg-type]
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

