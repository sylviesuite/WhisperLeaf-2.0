"""One-off builder: templates -> whisperleaf-site static export."""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "whisperleaf-site"

CANONICAL_STATIC_OWL = "/static/assets/images/owl.png"
SITE_OWL = "assets/images/owl.png"
CANONICAL_SITE_OWL_SOURCE = ROOT / "public/icons/owl-512.png"


def extract_inline_block(html: str, tag: str) -> str:
    pattern = rf"<{tag}>\s*(.*?)\s*</{tag}>"
    match = re.search(pattern, html, re.DOTALL)
    assert match, f"Missing <{tag}> block"
    return match.group(1).strip()


def normalize_owl_paths(html: str) -> str:
    """Convert app/static owl references into the static site's local owl path."""
    html = html.replace(f'src="{CANONICAL_STATIC_OWL}"', f'src="{SITE_OWL}"')
    html = html.replace('src="/assets/images/owl.png"', f'src="{SITE_OWL}"')
    return html


def main() -> None:
    (SITE / "assets/css").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/js").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/images").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/docs").mkdir(parents=True, exist_ok=True)

    landing = (ROOT / "templates/landing.html").read_text(encoding="utf-8")
    trans = (ROOT / "templates/whisperleaf_transparency.html").read_text(encoding="utf-8")
    dl_page = (ROOT / "templates/download.html").read_text(encoding="utf-8")

    # Extract and write CSS
    landing_css = extract_inline_block(landing, "style")
    (SITE / "assets/css/landing.css").write_text(landing_css + "\n", encoding="utf-8")

    trans_css = extract_inline_block(trans, "style")
    (SITE / "assets/css/transparency.css").write_text(trans_css + "\n", encoding="utf-8")

    # Extract and write JS
    landing_js = extract_inline_block(landing, "script").replace(
        "window.location.href = '/download'",
        "window.location.href = 'download.html'",
    )
    (SITE / "assets/js/landing.js").write_text(landing_js + "\n", encoding="utf-8")

    # Build index.html
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
    idx = normalize_owl_paths(idx)
    idx = idx.replace('href="/transparency"', 'href="transparency.html"')
    idx = idx.replace('href="/download"', 'href="download.html"')
    idx = idx.replace('href="/downloads/WhisperLeaf-Beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    idx = idx.replace('href="/downloads/whisperleaf-beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    (SITE / "index.html").write_text(idx, encoding="utf-8")

    # Build transparency.html
    tr = re.sub(
        r"<style>\s*.*?\s*</style>",
        '<link rel="stylesheet" href="assets/css/transparency.css" />',
        trans,
        count=1,
        flags=re.DOTALL,
    )
    tr = tr.replace('href="/"', 'href="index.html"')
    tr = normalize_owl_paths(tr)
    tr = tr.replace('href="/transparency"', 'href="transparency.html"')
    tr = tr.replace('href="/chat"', 'href="index.html"')
    tr = tr.replace(
        'href="/benchmarks/whisperleaf_energy_methodology.md"',
        'href="assets/docs/whisperleaf_energy_methodology.md"',
    )
    (SITE / "transparency.html").write_text(tr, encoding="utf-8")

    # Build download.html
    dl_page = dl_page.replace('href="/assets/css/landing.css"', 'href="assets/css/landing.css"')
    dl_page = normalize_owl_paths(dl_page)
    dl_page = dl_page.replace('href="/transparency"', 'href="transparency.html"')
    dl_page = dl_page.replace('href="/#how-whisperleaf-works"', 'href="index.html#how-whisperleaf-works"')
    dl_page = dl_page.replace('href="/download"', 'href="download.html"')
    dl_page = dl_page.replace('href="/downloads/WhisperLeaf-Beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    dl_page = dl_page.replace('href="/downloads/whisperleaf-beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    dl_page = dl_page.replace('href="/"', 'href="index.html"')
    (SITE / "download.html").write_text(dl_page, encoding="utf-8")

    # Copy canonical owl into static site
    if CANONICAL_SITE_OWL_SOURCE.is_file():
        shutil.copy2(CANONICAL_SITE_OWL_SOURCE, SITE / "assets/images/owl.png")

    # Copy methodology doc if present
    md = ROOT / "benchmarks/whisperleaf_energy_methodology.md"
    if md.is_file():
        shutil.copy2(md, SITE / "assets/docs/whisperleaf_energy_methodology.md")

    # Copy downloads
    dl_dst = SITE / "downloads"
    dl_dst.mkdir(parents=True, exist_ok=True)
    dl_src = ROOT / "static" / "downloads"
    if dl_src.is_dir():
        for f in dl_src.iterdir():
            if f.is_file():
                shutil.copy2(f, dl_dst / f.name)

    # Canonical ZIP naming for case-sensitive hosts like Netlify
    zip_out = dl_dst / "WhisperLeaf-Beta.zip"
    root_zip = ROOT / "WhisperLeaf-Beta.zip"
    zip_bytes: bytes | None = None

    if root_zip.is_file():
        zip_bytes = root_zip.read_bytes()
    elif (dl_src / "WhisperLeaf-Beta.zip").is_file():
        zip_bytes = (dl_src / "WhisperLeaf-Beta.zip").read_bytes()
    elif (dl_src / "whisperleaf-beta.zip").is_file():
        zip_bytes = (dl_src / "whisperleaf-beta.zip").read_bytes()
    elif (dl_dst / "whisperleaf-beta.zip").is_file():
        zip_bytes = (dl_dst / "whisperleaf-beta.zip").read_bytes()
    elif zip_out.is_file():
        zip_bytes = zip_out.read_bytes()

    for p in sorted(dl_dst.glob("*.zip")):
        try:
            p.unlink()
        except OSError:
            pass

    if zip_bytes is not None:
        zip_out.write_bytes(zip_bytes)

    # Netlify pretty URL
    (SITE / "_redirects").write_text("/download /download.html 200\n", encoding="utf-8")

    if not zip_out.is_file():
        print("WARN: missing", zip_out, "(add WhisperLeaf-Beta.zip at repo root or static/downloads/)")

    print("OK:", SITE)


if __name__ == "__main__":
    main()
