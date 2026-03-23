"""Pairing registry behavior."""

import tempfile
from pathlib import Path

from src.core.leaflink.errors import UnpairedDeviceError
from src.core.leaflink.pairing import PairingRegistry


def test_device_can_be_paired() -> None:
    reg = PairingRegistry()
    dev = reg.pair_device("phone-1", "Steve's Phone", public_label="Pixel")
    assert dev.device_id == "phone-1"
    assert dev.device_name == "Steve's Phone"
    assert dev.public_label == "Pixel"
    assert dev.is_active is True


def test_paired_device_is_recognized() -> None:
    reg = PairingRegistry()
    reg.pair_device("d1", "Device One")
    assert reg.is_paired("d1") is True
    assert reg.get_device("d1") is not None


def test_revoked_device_no_longer_accepted() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "pair.json"
        reg = PairingRegistry(persistence_path=p)
        reg.pair_device("gone", "Will Revoke")
        assert reg.is_paired("gone") is True
        reg.revoke_device("gone")
        assert reg.is_paired("gone") is False
        assert reg.get_device("gone") is None


def test_require_paired_raises_centrally() -> None:
    reg = PairingRegistry()
    reg.pair_device("ok", "OK Device")
    reg.require_paired("ok")  # no raise
    try:
        reg.require_paired("nope")
        raise AssertionError("expected UnpairedDeviceError")
    except UnpairedDeviceError as exc:
        assert exc.device_id == "nope"
