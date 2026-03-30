"""Allow: python -m src.core.leaflink [args]"""

from __future__ import annotations

import sys

from .viewer import main_argv

if __name__ == "__main__":
    raise SystemExit(main_argv())
