"""Identify and screen EPA SEMS document 313667.

One-off evidence scout. It downloads the official final engineering report,
extracts metadata and all page text, and renders pages relevant to site identity,
excavation/backfill depths, as-built geometry, consolidation areas, survey
accuracy, final surface materials, vegetation, infrastructure, and long-term use.
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

DOC_ID = "313667"
URLS = (
    f"https://semspub.epa.gov/work/05/{DOC_ID}.pdf",
    f"https://semspub.epa.gov/src/document/05/{DOC_ID}",
)
KEYWORDS = (
    "superfund",
    "site name",
    "final engineering report",
    "remedial action",
    "excavation",
    "average excavation depth",
    "as-built",
    "as built",
    "record drawing",
    "survey",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "consolidation area",
    "former residential",
    "north branch ravine",
    "vermilion river",
    "backfill",
    "topsoil",
    "hydroseed",
    "vegetation",
    "final grade",
    "cap",
    "cover thickness",
    "depth",
    "redevelopment",
    "operation and maintenance",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def download(destination: Path) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
        "Referer": "https://cumulis.epa.gov/",
    }
    errors: list[str] = []
    for url in URLS:
        try:
            response = requests.get(url, headers=headers, timeout=600, allow_redirects=True)
            response.raise_for_status()
            body = response.content
            if not body.startswith(b"%PDF-"):
                raise RuntimeError(f"not a PDF: {response.headers.get('content-type')}")
            destination.write_bytes(body)
            return response.url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            destination.unlink(missing_ok=True)
    raise RuntimeError("; ".join(errors))


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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "semspub_313667_scout"
    render_dir = output / "renders"
    output.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(f"/tmp/{DOC_ID}.pdf")
    source_url = download(pdf_path)

    document = fitz.open(pdf_path)
    metadata = document.metadata
    page_records: list[dict[str, object]] = []
    matched: set[int] = set()
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        text = normalize(page.get_text("text"))
        lower = text.lower()
        matches = [keyword for keyword in KEYWORDS if keyword in lower]
        page_records.append(
            {
                "page_number_1_based": page_number + 1,
                "matches": matches,
                "text_excerpt": text[:12000],
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
                "rotation": page.rotation,
            }
        )
        if matches:
            matched.add(page_number)

    selected: set[int] = set(range(min(8, document.page_count)))
    for page_number in matched:
        selected.update(
            number
            for number in (page_number - 1, page_number, page_number + 1)
            if 0 <= number < document.page_count
        )
    ranked = sorted(
        selected,
        key=lambda number: (-len(page_records[number]["matches"]), number),
    )[:80]
    ranked.sort()

    rendered: list[Path] = []
    for page_number in ranked:
        page = document.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        path = render_dir / f"page_{page_number + 1:04d}.png"
        pix.save(path)
        rendered.append(path)
    document.close()
    pdf_path.unlink(missing_ok=True)

    report = {
        "status": "SEMSSPUB_313667_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "doc_id": DOC_ID,
        "source_url": source_url,
        "pdf_metadata": metadata,
        "page_count": len(page_records),
        "matched_page_count": len(matched),
        "rendered_pages_1_based": [number + 1 for number in ranked],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_SITE_IDENTITY_SURFACE_DEPTH_GEOMETRY_AND_STABILITY_REVIEW",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "page_index.json").write_text(json.dumps(page_records, indent=2), encoding="utf-8")
    make_contact_sheet(rendered, output / "contact_sheet.jpg")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
