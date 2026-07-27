"""Extract Consolidated Iron Final Engineering Report and Site Management Plan.

This one-off utility processes New York DEC's official 2012 Final Engineering
Report and 2014 Final Site Management Plan. It indexes all pages and renders
survey/as-built, geotextile, final-grade, excavation-depth, surface-restoration,
accuracy, institutional-control, and later-modification evidence. It also exports
word coordinates, vector drawing metadata, and SVG for selected pages. It does
not call Earth Engine, create calibration rows, train a model, or enable depth
output.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

SOURCES = (
    {
        "key": "fer_2012",
        "env": "CONSOLIDATED_IRON_FER_PDF",
        "title": "Final Engineering Report",
        "source_url": "https://extapps.dec.ny.gov/data/DecDocs/336055/Report.HW.336055.2012-03-15.FER.pdf",
    },
    {
        "key": "smp_2014",
        "env": "CONSOLIDATED_IRON_SMP_PDF",
        "title": "Final Site Management Plan",
        "source_url": "https://extapps.dec.ny.gov/data/DecDocs/336055/Work%20Plan.HW.336055.2014-06-27.Final%20Site%20Management%20Plan.pdf",
    },
)

KEYWORDS = (
    "as-built",
    "as built",
    "record drawing",
    "final engineering report",
    "final site management plan",
    "licensed surveyor",
    "surveyed",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "coordinate system",
    "state plane",
    "nad83",
    "navd88",
    "northing",
    "easting",
    "final grade",
    "final surface",
    "surface elevation",
    "geotextile",
    "demarcation layer",
    "demarcation fabric",
    "bottom of excavation",
    "excavation bottom",
    "excavation depth",
    "depth of excavation",
    "six feet",
    "6 feet",
    "50-foot grid",
    "50 foot grid",
    "topsoil",
    "hydroseed",
    "vegetation",
    "restoration",
    "site modification",
    "environmental easement",
    "institutional control",
    "cover system",
    "engineering control",
    "figure",
    "drawing",
    "appendix",
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


def process_source(source: dict[str, str], output: Path) -> dict[str, object]:
    configured = os.environ.get(source["env"])
    if not configured:
        raise RuntimeError(f"Missing environment variable {source['env']}")
    pdf_path = Path(configured)
    if not pdf_path.exists():
        raise RuntimeError(f"Source file not found: {pdf_path}")

    source_dir = output / source["key"]
    render_dir = source_dir / "renders"
    svg_dir = source_dir / "svg"
    words_dir = source_dir / "words"
    drawings_dir = source_dir / "drawings"
    for directory in (render_dir, svg_dir, words_dir, drawings_dir):
        directory.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    page_records: list[dict[str, object]] = []
    matched: set[int] = set()
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        text = normalize(page.get_text("text"))
        lower = text.lower()
        matches = [term for term in KEYWORDS if term in lower]
        record = {
            "page_number_1_based": page_number + 1,
            "matches": matches,
            "text_excerpt": text[:8000],
            "page_width_pt": page.rect.width,
            "page_height_pt": page.rect.height,
            "rotation": page.rotation,
        }
        page_records.append(record)
        if matches:
            matched.add(page_number)

    # Include neighbors for title blocks, legends, continuation tables, and oversized drawings.
    candidates: set[int] = set()
    for page_number in matched:
        candidates.update(
            number
            for number in (page_number - 2, page_number - 1, page_number, page_number + 1, page_number + 2)
            if 0 <= number < document.page_count
        )

    # Prioritize high-value exact terms and later pages, which often contain appendices/drawings.
    priority_terms = {
        "as-built",
        "as built",
        "record drawing",
        "final grade",
        "geotextile",
        "bottom of excavation",
        "excavation depth",
        "northing",
        "easting",
        "coordinate system",
        "survey accuracy",
    }
    ranked = sorted(
        candidates,
        key=lambda number: (
            -sum(5 if term in priority_terms else 1 for term in page_records[number]["matches"]),
            -number,
        ),
    )[:110]
    ranked.sort()

    rendered: list[Path] = []
    for page_number in ranked:
        page = document.load_page(page_number)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.35, 2.35), alpha=False)
        render_path = render_dir / f"page_{page_number + 1:04d}.png"
        pixmap.save(render_path)
        rendered.append(render_path)

        words = page.get_text("words")
        (words_dir / f"page_{page_number + 1:04d}.json").write_text(
            json.dumps(words, indent=2), encoding="utf-8"
        )
        drawings = page.get_drawings()
        serializable_drawings = []
        for drawing in drawings:
            item = dict(drawing)
            for key, value in list(item.items()):
                if isinstance(value, fitz.Rect):
                    item[key] = [value.x0, value.y0, value.x1, value.y1]
                elif isinstance(value, fitz.Point):
                    item[key] = [value.x, value.y]
                elif key == "items":
                    converted = []
                    for entry in value:
                        row = []
                        for part in entry:
                            if isinstance(part, fitz.Rect):
                                row.append([part.x0, part.y0, part.x1, part.y1])
                            elif isinstance(part, fitz.Point):
                                row.append([part.x, part.y])
                            else:
                                row.append(part)
                        converted.append(row)
                    item[key] = converted
            serializable_drawings.append(item)
        (drawings_dir / f"page_{page_number + 1:04d}.json").write_text(
            json.dumps(serializable_drawings, indent=2, default=str), encoding="utf-8"
        )
        try:
            (svg_dir / f"page_{page_number + 1:04d}.svg").write_text(
                page.get_svg_image(text_as_path=False), encoding="utf-8"
            )
        except Exception as exc:
            (svg_dir / f"page_{page_number + 1:04d}.error.txt").write_text(str(exc), encoding="utf-8")

    document.close()
    (source_dir / "page_index.json").write_text(json.dumps(page_records, indent=2), encoding="utf-8")
    make_contact_sheet(rendered, source_dir / "contact_sheet.jpg")
    return {
        "key": source["key"],
        "title": source["title"],
        "source_url": source["source_url"],
        "pdf_bytes": pdf_path.stat().st_size,
        "page_count": len(page_records),
        "matched_page_count": len(matched),
        "rendered_page_count": len(rendered),
        "rendered_pages_1_based": [number + 1 for number in ranked],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "consolidated_iron_dec_reports"
    output.mkdir(parents=True, exist_ok=True)
    records = [process_source(source, output) for source in SOURCES]
    report = {
        "status": "CONSOLIDATED_IRON_DEC_REPORTS_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "sources": records,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_AS_BUILT_DEPTH_GEOMETRY_UNCERTAINTY_SURFACE_AND_STABILITY_REVIEW",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# Consolidated Iron DEC report extraction\n\n"
        "Review both contact sheets, page indexes, full renders, word coordinates, SVGs, and drawing metadata. "
        "The acceptance gates are actual surface-to-geotextile depth by location, exact surveyed shallow and "
        "deep zones, numerical uncertainty, identical final vegetation/topsoil, clean 20 m interiors, and a "
        "stable post-remedy observation period. This extraction does not authorize an Earth Engine query or "
        "calibration row.\n",
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
