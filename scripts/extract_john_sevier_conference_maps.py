"""Render available John Sevier closure conference papers for geometry review.

The source PDFs are public World of Coal Ash conference papers. This script
accepts one or more already-downloaded PDF paths, extracts text, renders every
page, creates contact sheets, and writes a report. It does not call Earth Engine
or create a calibration row.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

SOURCES = [
    {
        "key": "woca_2013_bottom_ash_pond_outfall",
        "env": "JSF_WOCA_2013_PDF",
        "title": "Preparing for Closure of the John Sevier Fossil Plant",
        "url": "https://www.flyash.info/files/2013/090-vance-2013.pdf",
    },
    {
        "key": "woca_2015_dry_fly_ash_stack_sequence",
        "env": "JSF_WOCA_2015_PDF",
        "title": "John Sevier Dry Fly Ash Stack - Sequencing of CCR Waste Facility Closures",
        "url": "https://uknowledge.uky.edu/cgi/viewcontent.cgi?article=1739&context=woca",
    },
]

KEYWORDS = (
    "bottom ash pond",
    "closure",
    "final cover",
    "geomembrane",
    "excavat",
    "native",
    "configuration",
    "sequence",
    "outfall",
    "grading",
    "survey",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_contact_sheet(page_files: list[Path], destination: Path) -> None:
    if not page_files:
        return
    thumb_width = 420
    margin = 18
    label_height = 34
    columns = 2
    thumbs: list[tuple[Path, Image.Image]] = []
    max_height = 0
    for path in page_files:
        image = Image.open(path).convert("RGB")
        ratio = thumb_width / image.width
        thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
        thumbs.append((path, thumb))
        max_height = max(max_height, thumb.height)
    rows = (len(thumbs) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (
            margin + columns * (thumb_width + margin),
            margin + rows * (max_height + label_height + margin),
        ),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for idx, (path, thumb) in enumerate(thumbs):
        row, col = divmod(idx, columns)
        x = margin + col * (thumb_width + margin)
        y = margin + row * (max_height + label_height + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_height + 6), path.stem, fill="black")
    canvas.save(destination, quality=90)


def process_source(source: dict[str, str], output_root: Path) -> dict[str, object] | None:
    configured = os.environ.get(source["env"])
    if not configured:
        return None
    pdf_path = Path(configured)
    if not pdf_path.exists():
        raise RuntimeError(f"Source PDF not found: {pdf_path}")
    if pdf_path.stat().st_size < 1000:
        raise RuntimeError(f"Source PDF is unexpectedly small: {pdf_path}")

    source_dir = output_root / source["key"]
    pages_dir = source_dir / "rendered_pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    page_records: list[dict[str, object]] = []
    rendered_files: list[Path] = []
    try:
        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            text = normalize(page.get_text("text"))
            lowered = text.lower()
            matches = [keyword for keyword in KEYWORDS if keyword in lowered]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            page_path = pages_dir / f"page_{page_number + 1:03d}.png"
            pixmap.save(page_path)
            rendered_files.append(page_path)
            page_records.append(
                {
                    "page_number_1_based": page_number + 1,
                    "matches": matches,
                    "text_excerpt": text[:3000],
                    "rendered_file": str(page_path.relative_to(output_root)),
                    "width_px": pixmap.width,
                    "height_px": pixmap.height,
                }
            )
    finally:
        document.close()

    contact_sheet = source_dir / "contact_sheet.jpg"
    make_contact_sheet(rendered_files, contact_sheet)
    return {
        "key": source["key"],
        "title": source["title"],
        "source_url": source["url"],
        "pdf_bytes": pdf_path.stat().st_size,
        "page_count": len(page_records),
        "pages": page_records,
        "contact_sheet": str(contact_sheet.relative_to(output_root)),
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / "artifacts" / "john_sevier_conference_maps"
    output_root.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    unavailable: list[dict[str, str]] = []
    for source in SOURCES:
        if not os.environ.get(source["env"]):
            unavailable.append(
                {
                    "key": source["key"],
                    "title": source["title"],
                    "reason": "source PDF was not downloaded",
                }
            )
            continue
        record = process_source(source, output_root)
        if record is not None:
            records.append(record)

    if not records:
        raise RuntimeError("No conference paper PDF was available for extraction")

    report = {
        "status": "CONFERENCE_PAPERS_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "sources": records,
        "unavailable_sources": unavailable,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_MAPS_AND_CONSTRUCTION_DETAILS_ARE_REVIEWED",
    }
    (output_root / "extraction_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (output_root / "README.md").write_text(
        "# John Sevier conference-map extraction\n\n"
        "Review the available contact sheets and full rendered pages for closure "
        "sequencing, Bottom Ash Pond geometry, final-cover details, and permanent "
        "controls. These papers are supporting evidence only and do not authorize "
        "an Earth Engine query or calibration row.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
