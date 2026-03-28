"""One-off builder: templates -> whisperleaf-site static export."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "whisperleaf-site"


def main() -> None:
    (SITE / "assets/css").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/js").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/images").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/docs").mkdir(parents=True, exist_ok=True)

    landing = (ROOT / "templates/landing.html").read_text(encoding="utf-8")
    trans = (ROOT / "templates/whisperleaf_transparency.html").read_text(encoding="utf-8")

    m = re.search(r"<style>\s*(.*?)\s*</style>", landing, re.DOTALL)
    assert m
    (SITE / "assets/css/landing.css").write_text(m.group(1).strip() + "\n", encoding="utf-8")

    m2 = re.search(r"<style>\s*(.*?)\s*</style>", trans, re.DOTALL)
    assert m2
    (SITE / "assets/css/transparency.css").write_text(m2.group(1).strip() + "\n", encoding="utf-8")

    m3 = re.search(r"<script>\s*(.*?)\s*</script>\s*</body>", landing, re.DOTALL)
    assert m3
    js = m3.group(1).strip().replace(
        "window.location.href = '/downloads/whisperleaf-beta.zip'",
        "window.location.href = 'downloads/whisperleaf-beta.zip'",
    )
    (SITE / "assets/js/landing.js").write_text(js + "\n", encoding="utf-8")

    idx = re.sub(
        r"<style>\s*.*?\s*</style>",
        '<link rel="stylesheet" href="assets/css/landing.css" />',
        landing,
        count=1,
        flags=re.DOTALL,
    )
    idx = re.sub(
        r"<script>\s*.*?\s*</script>\s*</body>",
        '<script src="assets/js/landing.js" defer></script>\n</body>',
        idx,
        count=1,
        flags=re.DOTALL,
    )
    idx = idx.replace('href="/"', 'href="index.html"')
    idx = idx.replace('src="/static/owl.png"', 'src="assets/images/owl.png"')
    idx = idx.replace('href="/transparency"', 'href="transparency.html"')
    idx = idx.replace('href="/downloads/whisperleaf-beta.zip"', 'href="downloads/whisperleaf-beta.zip"')
    (SITE / "index.html").write_text(idx, encoding="utf-8")

    tr = re.sub(
        r"<style>\s*.*?\s*</style>",
        '<link rel="stylesheet" href="assets/css/transparency.css" />',
        trans,
        count=1,
        flags=re.DOTALL,
    )
    tr = tr.replace('href="/"', 'href="index.html"')
    tr = tr.replace('src="/static/owl.png"', 'src="assets/images/owl.png"')
    tr = tr.replace('href="/transparency"', 'href="transparency.html"')
    tr = tr.replace('href="/chat"', 'href="index.html"')
    tr = tr.replace(
        'href="/benchmarks/whisperleaf_energy_methodology.md"',
        'href="assets/docs/whisperleaf_energy_methodology.md"',
    )
    (SITE / "transparency.html").write_text(tr, encoding="utf-8")

    import shutil

    src_owl = ROOT / "public/icons/owl-512.png"
    if src_owl.is_file():
        shutil.copy2(src_owl, SITE / "assets/images/owl.png")
    md = ROOT / "benchmarks/whisperleaf_energy_methodology.md"
    if md.is_file():
        shutil.copy2(md, SITE / "assets/docs/whisperleaf_energy_methodology.md")

    dl_src = ROOT / "static" / "downloads"
    if dl_src.is_dir():
        dl_dst = SITE / "downloads"
        dl_dst.mkdir(parents=True, exist_ok=True)
        for f in dl_src.iterdir():
            if f.is_file():
                shutil.copy2(f, dl_dst / f.name)

    print("OK:", SITE)


if __name__ == "__main__":
    main()
