"""Extract Berks Landfill closeout and five-year-review cap evidence.

One-off research utility. It downloads EPA's Preliminary Close Out Report and
selected Five-Year Review reports, indexes their text, and renders pages relevant
to final cap construction, repair limits, post-repair thickness measurements,
as-built surveys, vegetation, erosion, settlement, and later modifications.
It does not call Earth Engine, create calibration rows, train a model, or enable
depth output.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import requests
from PIL import Image, ImageDraw

SOURCES = (
    ("pcor_2000", "463581", "Preliminary Close Out Report"),
    ("fyr_2005", "2046292", "First Five-Year Review"),
    ("fyr_2010", "2118062", "Second Five-Year Review"),
    ("fyr_2020", "2302594", "Fourth Five-Year Review"),
    ("fyr_2025", "2448884", "Fifth Five-Year Review"),
)
KEYWORDS = (
    "remedial action report",
    "construction completion",
    "construction report",
    "as-built",
    "as built",
    "record drawing",
    "final survey",
    "survey",
    "cap thickness",
    "cover thickness",
    "soil cover",
    "cap repair",
    "cover repair",
    "one foot",
    "1 foot",
    "12 inches",
    "two feet",
    "2 feet",
    "24 inches",
    "eastern landfill",
    "western landfill",
    "minimum thickness",
    "test pit",
    "probe",
    "boring",
    "topsoil",
    "seed",
    "vegetation",
    "erosion",
    "settlement",
    "subsidence",
    "operation and maintenance",
    "institutional control",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_contact_sheet(paths: list[Path], destination: Path) -> None:
    if not paths:
        return
    thumb_w = 420
    margin = 18
    label_h = 32
    cols = 2
    thumbs: list[tuple[Path, Image.Image]] = []
    max_h = 0
    for path in paths:
        image = Image.open(path).convert("RGB")
        ratio = thumb_w / image.width
        thumb = image.resize((thumb_w, max(1, int(image.height * ratio))))
        thumbs.append((path, thumb))
        max_h = max(max_h, thumb.height)
    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new(
        "RGB",
        (margin + cols * (thumb_w + margin), margin + rows * (max_h + label_h + margin)),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (path, thumb) in enumerate(thumbs):
        row, col = divmod(index, cols)
        x = margin + col * (thumb_w + margin)
        y = margin + row * (max_h + label_h + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_h + 5), path.stem, fill="black")
    canvas.save(destination, quality=88)


def download(doc_id: str, destination: Path) -> str:
    urls = (
        f"https://semspub.epa.gov/work/03/{doc_id}.pdf",
        f"https://semspub.epa.gov/src/document/03/{doc_id}",
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
        "Referer": "https://cumulis.epa.gov/",
    }
    errors: list[str] = []
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=300, allow_redirects=True)
            response.raise_for_status()
            body = response.content
            if not body.startswith(b"%PDF-"):
                raise RuntimeError(f"response is not PDF: {response.headers.get('content-type')}")
            destination.write_bytes(body)
            return response.url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            destination.unlink(missing_ok=True)
    raise RuntimeError("; ".join(errors))


def process(source_key: str, doc_id: str, title: str, output: Path) -> dict[str, object]:
    source_dir = output / source_key
    render_dir = source_dir / "renders"
    source_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(f"/tmp/berks_{doc_id}.pdf")
    source_url = download(doc_id, pdf_path)
    document = fitz.open(pdf_path)
    page_records: list[dict[str, object]] = []
    matched: set[int] = set()
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        text = normalize(page.get_text("text"))
        lower = text.lower()
        matches = [term for term in KEYWORDS if term in lower]
        page_records.append(
            {
                "page_number_1_based": page_number + 1,
                "matches": matches,
                "text_excerpt": text[:9000],
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
                "rotation": page.rotation,
            }
        )
        if matches:
            matched.add(page_number)

    selected: set[int] = set()
    if document.page_count <= 12:
        selected.update(range(document.page_count))
    for page_number in matched:
        selected.update(
            number
            for number in (page_number - 1, page_number, page_number + 1)
            if 0 <= number < document.page_count
        )
    ranked = sorted(
        selected,
        key=lambda number: (-len(page_records[number]["matches"]), number),
    )[:55]
    ranked.sort()
    rendered: list[Path] = []
    for page_number in ranked:
        page = document.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        path = render_dir / f"page_{page_number + 1:03d}.png"
        pix.save(path)
        rendered.append(path)
    document.close()
    pdf_path.unlink(missing_ok=True)
    (source_dir / "page_index.json").write_text(json.dumps(page_records, indent=2), encoding="utf-8")
    make_contact_sheet(rendered, source_dir / "contact_sheet.jpg")
    return {
        "key": source_key,
        "doc_id": doc_id,
        "title": title,
        "source_url": source_url,
        "page_count": len(page_records),
        "matched_page_count": len(matched),
        "rendered_pages_1_based": [number + 1 for number in ranked],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "berks_landfill_closeout_reviews"
    output.mkdir(parents=True, exist_ok=True)
    records = [process(*source, output) for source in SOURCES]
    report = {
        "status": "BERKS_CLOSEOUT_AND_REVIEWS_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "sources": records,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_FINAL_POST_REPAIR_DEPTH_GEOMETRY_AND_UNCERTAINTY_REVIEW",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
