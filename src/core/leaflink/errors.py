"""
LeafLink-specific exceptions (kept separate to avoid import cycles).

All inbound device checks should use ``PairingRegistry.require_paired()`` which raises this.
"""


class UnpairedDeviceError(Exception):
    """Raised when an operation requires an active paired device_id and the device is missing or inactive."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"device is not paired or inactive: {device_id!r}")
