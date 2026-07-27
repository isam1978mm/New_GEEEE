"""Extract Fletcher's Paint Works OU1 final remedial-action evidence.

One-off research utility. It downloads EPA SEMS document 100008978, indexes the
PDF, and renders pages relevant to cover construction, excavation boundaries,
survey controls, as-built drawings, surface restoration, and thickness QA.
It does not call Earth Engine, create calibration rows, train a model, or enable
app depth output.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import requests
from PIL import Image, ImageDraw

URLS = (
    "https://semspub.epa.gov/work/01/100008978.pdf",
    "https://semspub.epa.gov/src/document/01/100008978",
)
KEYWORDS = (
    "40-inch",
    "40 inch",
    "low-permeability cover",
    "final cover",
    "cover system",
    "cover thickness",
    "topsoil",
    "sand layer",
    "elm street",
    "mill street",
    "as-built",
    "as built",
    "record drawing",
    "survey",
    "northing",
    "easting",
    "coordinate",
    "excavation limit",
    "limits of excavation",
    "final grade",
    "vegetat",
    "amphitheater",
    "parking",
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def download_pdf(destination: Path) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
        "Referer": "https://cumulis.epa.gov/",
    }
    errors: list[str] = []
    for url in URLS:
        try:
            with requests.get(url, headers=headers, timeout=180, stream=True, allow_redirects=True) as response:
                response.raise_for_status()
                with destination.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            if destination.stat().st_size < 100_000:
                raise RuntimeError(f"downloaded file too small: {destination.stat().st_size}")
            with destination.open("rb") as handle:
                if handle.read(5) != b"%PDF-":
                    raise RuntimeError("downloaded response is not a PDF")
            return url
        except Exception as exc:  # bounded fallback
            errors.append(f"{url}: {exc}")
            destination.unlink(missing_ok=True)
    raise RuntimeError("; ".join(errors))


def make_contact_sheet(paths: list[Path], destination: Path) -> None:
    if not paths:
        return
    thumb_w = 420
    margin = 18
    label_h = 30
    cols = 2
    thumbs: list[tuple[Path, Image.Image]] = []
    max_h = 0
    for path in paths:
        img = Image.open(path).convert("RGB")
        ratio = thumb_w / img.width
        thumb = img.resize((thumb_w, max(1, int(img.height * ratio))))
        thumbs.append((path, thumb))
        max_h = max(max_h, thumb.height)
    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new("RGB", (margin + cols * (thumb_w + margin), margin + rows * (max_h + label_h + margin)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (path, thumb) in enumerate(thumbs):
        row, col = divmod(i, cols)
        x = margin + col * (thumb_w + margin)
        y = margin + row * (max_h + label_h + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_h + 5), path.stem, fill="black")
    canvas.save(destination, quality=88)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "fletcher_ou1_final_report"
    renders = output / "renders"
    output.mkdir(parents=True, exist_ok=True)
    renders.mkdir(parents=True, exist_ok=True)
    source = Path("/tmp/fletcher_ou1_final_report.pdf")

    source_url = download_pdf(source)
    doc = fitz.open(source)
    page_index: list[dict[str, object]] = []
    selected: set[int] = set()
    for page_number in range(doc.page_count):
        page = doc.load_page(page_number)
        text = norm(page.get_text("text"))
        lower = text.lower()
        matches = [term for term in KEYWORDS if term in lower]
        page_index.append({
            "page_number_1_based": page_number + 1,
            "matches": matches,
            "text_excerpt": text[:5000],
        })
        if matches:
            selected.add(page_number)

    # Include neighboring pages for drawing titles, legends, and survey notes.
    expanded: set[int] = set()
    for number in selected:
        expanded.update(n for n in (number - 1, number, number + 1) if 0 <= n < doc.page_count)
    # Bound artifact size while preserving all high-value matches.
    ranked = sorted(
        expanded,
        key=lambda n: (-len(page_index[n]["matches"]), n),
    )[:80]
    ranked.sort()

    rendered: list[Path] = []
    for page_number in ranked:
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        path = renders / f"page_{page_number + 1:04d}.png"
        pix.save(path)
        rendered.append(path)
    doc.close()

    report = {
        "status": "FLETCHER_OU1_REPORT_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "source_url": source_url,
        "document_id": "100008978",
        "pdf_bytes": source.stat().st_size,
        "page_count": len(page_index),
        "selected_page_count": len(rendered),
        "selected_pages_1_based": [n + 1 for n in ranked],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_GEOMETRY_SURFACE_AND_UNCERTAINTY_REVIEW",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "page_index.json").write_text(json.dumps(page_index, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# Fletcher OU1 evidence extraction\n\n"
        "Review the contact sheet and rendered pages for exact Elm Street cover limits, "
        "Mill Street excavation/restoration limits, survey control and accuracy, cover-thickness "
        "verification, grass-only interior space, roads, parking, amphitheater structures, and utilities. "
        "The extraction does not authorize an Earth Engine query or calibration row.\n",
        encoding="utf-8",
    )
    make_contact_sheet(rendered, output / "contact_sheet.jpg")
    source.unlink(missing_ok=True)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
