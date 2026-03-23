"""
Local pairing registry for LeafLink V1.

No networking. In-memory default with optional JSON file persistence.

TODO: Add pairing secrets / QR flow when mobile client exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import UnpairedDeviceError
from .schemas import PairedDevice, new_paired_device, paired_device_from_dict, paired_device_to_dict


class PairingRegistry:
    """Stores paired devices locally. Thread-safe not guaranteed (V1 single-process)."""

    def __init__(self, persistence_path: Path | None = None) -> None:
        self._path: Path | None = persistence_path
        self._devices: dict[str, PairedDevice] = {}
        if self._path and self._path.exists():
            self._load()

    def _load(self) -> None:
        if not self._path or not self._path.exists():
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        devices = raw.get("devices", [])
        self._devices = {}
        for d in devices:
            pd = paired_device_from_dict(d)
            self._devices[pd.device_id] = pd

    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {"devices": [paired_device_to_dict(d) for d in self._devices.values()]}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def pair_device(
        self,
        device_id: str,
        device_name: str,
        public_label: str | None = None,
    ) -> PairedDevice:
        """Register or replace a device record."""
        dev = new_paired_device(device_id, device_name, public_label=public_label)
        self._devices[dev.device_id] = dev
        self._save()
        return dev

    def is_paired(self, device_id: str) -> bool:
        d = self._devices.get(device_id)
        return d is not None and d.is_active

    def require_paired(self, device_id: str) -> None:
        """
        Central gate for inbound LeafLink traffic: paired + active only.

        Raises UnpairedDeviceError if the device is not allowed to submit.
        """
        if not self.is_paired(device_id):
            raise UnpairedDeviceError(device_id)

    def get_device(self, device_id: str) -> PairedDevice | None:
        return self._devices.get(device_id)

    def revoke_device(self, device_id: str) -> None:
        """Remove a device from the registry."""
        self._devices.pop(device_id, None)
        self._save()

    def list_devices(self) -> list[PairedDevice]:
        return list(self._devices.values())
