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
        "window.location.href = '/download'",
        "window.location.href = 'download.html'",
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
    idx = idx.replace('src="/static/assets/images/owl.png"', 'src="assets/images/owl.png"')
    idx = idx.replace('src="/assets/images/owl.png"', 'src="assets/images/owl.png"')
    idx = idx.replace('href="/transparency"', 'href="transparency.html"')
    idx = idx.replace('href="/download"', 'href="download.html"')
    idx = idx.replace('href="/downloads/WhisperLeaf-Beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    idx = idx.replace('href="/downloads/whisperleaf-beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    (SITE / "index.html").write_text(idx, encoding="utf-8")

    tr = re.sub(
        r"<style>\s*.*?\s*</style>",
        '<link rel="stylesheet" href="assets/css/transparency.css" />',
        trans,
        count=1,
        flags=re.DOTALL,
    )
    tr = tr.replace('href="/"', 'href="index.html"')
    tr = tr.replace('src="/assets/images/owl.png"', 'src="assets/images/owl.png"')
    tr = tr.replace('href="/transparency"', 'href="transparency.html"')
    tr = tr.replace('href="/chat"', 'href="index.html"')
    tr = tr.replace(
        'href="/benchmarks/whisperleaf_energy_methodology.md"',
        'href="assets/docs/whisperleaf_energy_methodology.md"',
    )
    (SITE / "transparency.html").write_text(tr, encoding="utf-8")

    dl_page = (ROOT / "templates/download.html").read_text(encoding="utf-8")
    dl_page = dl_page.replace('href="/assets/css/landing.css"', 'href="assets/css/landing.css"')
    dl_page = dl_page.replace('src="/static/assets/images/owl.png"', 'src="assets/images/owl.png"')
    dl_page = dl_page.replace('src="/assets/images/owl.png"', 'src="assets/images/owl.png"')
    dl_page = dl_page.replace('href="/transparency"', 'href="transparency.html"')
    dl_page = dl_page.replace('href="/#how-whisperleaf-works"', 'href="index.html#how-whisperleaf-works"')
    dl_page = dl_page.replace('href="/download"', 'href="download.html"')
    dl_page = dl_page.replace('href="/downloads/WhisperLeaf-Beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    dl_page = dl_page.replace('href="/downloads/whisperleaf-beta.zip"', 'href="downloads/WhisperLeaf-Beta.zip"')
    dl_page = dl_page.replace('href="/"', 'href="index.html"')
    (SITE / "download.html").write_text(dl_page, encoding="utf-8")

    import shutil

    src_owl = ROOT / "public/icons/owl-512.png"
    if src_owl.is_file():
        shutil.copy2(src_owl, SITE / "assets/images/owl.png")
    md = ROOT / "benchmarks/whisperleaf_energy_methodology.md"
    if md.is_file():
        shutil.copy2(md, SITE / "assets/docs/whisperleaf_energy_methodology.md")

    dl_dst = SITE / "downloads"
    dl_dst.mkdir(parents=True, exist_ok=True)
    dl_src = ROOT / "static" / "downloads"
    if dl_src.is_dir():
        for f in dl_src.iterdir():
            if f.is_file():
                shutil.copy2(f, dl_dst / f.name)

    zip_out = dl_dst / "WhisperLeaf-Beta.zip"
    root_zip = ROOT / "WhisperLeaf-Beta.zip"
    if root_zip.is_file():
        shutil.copy2(root_zip, zip_out)
    elif (dl_dst / "whisperleaf-beta.zip").is_file() and not zip_out.is_file():
        shutil.copy2(dl_dst / "whisperleaf-beta.zip", zip_out)

    # Netlify: pretty URL /download -> static file (avoids 404 on SPA-less export)
    (SITE / "_redirects").write_text("/download /download.html 200\n", encoding="utf-8")

    if not zip_out.is_file():
        print("WARN: missing", zip_out, "(add WhisperLeaf-Beta.zip at repo root or static/downloads/)")

    print("OK:", SITE)


if __name__ == "__main__":
    main()
