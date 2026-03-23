#!/usr/bin/env python3
"""
Run LeafLink unit tests without requiring pytest.

Usage (from repo root):
  python scripts/run_leaflink_tests.py

With pytest installed, prefer:
  python -m pytest tests/test_leaflink_*.py -q
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = (
    "tests.test_leaflink_pairing",
    "tests.test_leaflink_inbox",
    "tests.test_leaflink_privacy_boundary",
    "tests.test_leaflink_promotion_flow",
    "tests.test_leaflink_viewer",
)


def main() -> int:
    failed: list[str] = []
    for modname in MODULES:
        mod = importlib.import_module(modname)
        for name in sorted(dir(mod)):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                fn()
            except Exception as e:  # noqa: BLE001 — surface any test failure
                failed.append(f"{modname}.{name}: {e!r}")
    if failed:
        print("FAILED:", len(failed))
        for line in failed:
            print(" ", line)
        return 1
    print("LeafLink tests OK (%d modules)" % len(MODULES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
