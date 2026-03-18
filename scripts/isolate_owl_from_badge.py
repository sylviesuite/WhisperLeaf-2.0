"""
Isolate the WhisperLeaf owl from the embedded dark circular badge.

The source asset (owl.png) contains: owl artwork + dark circular badge.
This script produces owl_only.png: owl artwork only, with the dark badge
replaced by transparency. Use owl_only.png inside the CSS circle (white
ring + dark fill) to avoid a badge-inside-a-badge look.

Usage:
  pip install Pillow
  python scripts/isolate_owl_from_badge.py
"""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow required: pip install Pillow")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "static" / "owl.png"
OUT = PROJECT_ROOT / "static" / "owl_only.png"

# Pixels darker than this (max of R,G,B) are treated as badge and made transparent.
# Keeps white/light owl; removes dark circle. Tune if needed (80–140).
DARK_THRESHOLD = 110


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source image not found: {SRC}")

    img = Image.open(SRC)
    img = img.convert("RGBA")
    data = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            # Dark badge pixels -> full transparency
            if max(r, g, b) < DARK_THRESHOLD:
                data[x, y] = (r, g, b, 0)
            # Optional: already very transparent stays transparent
            elif a < 8:
                data[x, y] = (r, g, b, 0)

    img.save(OUT, "PNG")
    print(f"Saved owl-only asset: {OUT}")


if __name__ == "__main__":
    main()
