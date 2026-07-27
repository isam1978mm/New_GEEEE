"""Extract McMaster Street MGP as-built cover drawings.

One-off evidence utility. It downloads/reads the official NYSDEC Construction
Completion Report Appendices A-G, locates Appendix A and as-built drawing pages,
renders a bounded set at high resolution, and exports page text/word/drawing
metadata for manual depth-zone and 20 m pixel-support review. It does not call
Earth Engine, create calibration rows, train a model, or enable depth output.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

KEYWORDS = (
    "appendix a",
    "as-built",
    "as built",
    "cover thickness",
    "soil cover",
    "geotextile",
    "demarcation",
    "phase 1",
    "phase 3",
    "final grade",
    "excavation",
    "backfill",
    "survey",
    "northing",
    "easting",
    "coordinate",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def contact_sheet(paths: list[Path], destination: Path) -> None:
    if not paths:
        return
    width = 360
    margin = 16
    label = 28
    cols = 3
    thumbs: list[tuple[Path, Image.Image]] = []
    max_h = 0
    for path in paths:
        image = Image.open(path).convert("RGB")
        ratio = width / image.width
        thumb = image.resize((width, max(1, int(image.height * ratio))))
        thumbs.append((path, thumb))
        max_h = max(max_h, thumb.height)
    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new(
        "RGB",
        (margin + cols * (width + margin), margin + rows * (max_h + label + margin)),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (path, thumb) in enumerate(thumbs):
        row, col = divmod(index, cols)
        x = margin + col * (width + margin)
        y = margin + row * (max_h + label + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_h + 4), path.stem, fill="black")
    canvas.save(destination, quality=86)


def serializable_drawings(page: fitz.Page) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for drawing in page.get_drawings():
        item: dict[str, object] = {}
        for key, value in drawing.items():
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
            else:
                item[key] = value
        output.append(item)
    return output


def main() -> int:
    source_value = os.environ.get("MCMASTER_APPENDICES_PDF")
    if not source_value:
        raise RuntimeError("MCMASTER_APPENDICES_PDF is required")
    source = Path(source_value)
    if not source.exists():
        raise RuntimeError(f"Source PDF not found: {source}")

    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "mcmaster_asbuilt_cover_drawings"
    renders = output / "renders"
    words_dir = output / "words"
    drawings_dir = output / "drawings"
    for directory in (output, renders, words_dir, drawings_dir):
        directory.mkdir(parents=True, exist_ok=True)

    document = fitz.open(source)
    pages: list[dict[str, object]] = []
    matched: set[int] = set()
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        text = normalize(page.get_text("text"))
        lower = text.lower()
        matches = [term for term in KEYWORDS if term in lower]
        pages.append(
            {
                "page_number_1_based": page_number + 1,
                "matches": matches,
                "text_excerpt": text[:8000],
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
                "rotation": page.rotation,
                "image_count": len(page.get_images(full=True)),
                "drawing_count": len(page.get_drawings()),
            }
        )
        if matches:
            matched.add(page_number)

    # Appendix A is expected at the front of the combined A-G file. Preserve the
    # first 70 pages even when scanned text is absent, then add all matched pages
    # and immediate neighbors. Bound output at 100 pages.
    selected: set[int] = set(range(min(70, document.page_count)))
    for page_number in matched:
        selected.update(
            candidate
            for candidate in (page_number - 1, page_number, page_number + 1)
            if 0 <= candidate < document.page_count
        )
    ranked = sorted(
        selected,
        key=lambda number: (
            0 if number < 70 else 1,
            -len(pages[number]["matches"]),
            number,
        ),
    )[:100]
    ranked.sort()

    rendered: list[Path] = []
    for page_number in ranked:
        page = document.load_page(page_number)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4), alpha=False)
        render_path = renders / f"page_{page_number + 1:04d}.png"
        pixmap.save(render_path)
        rendered.append(render_path)
        (words_dir / f"page_{page_number + 1:04d}.json").write_text(
            json.dumps(page.get_text("words"), indent=2), encoding="utf-8"
        )
        (drawings_dir / f"page_{page_number + 1:04d}.json").write_text(
            json.dumps(serializable_drawings(page), indent=2, default=str), encoding="utf-8"
        )

    document.close()
    (output / "page_index.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")
    contact_sheet(rendered, output / "contact_sheet.jpg")
    report = {
        "status": "MCMASTER_ASBUILT_DRAWINGS_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "source": "NYSDEC 2019 Construction Completion Report Appendices A-G",
        "pdf_bytes": source.stat().st_size,
        "page_count": len(pages),
        "matched_page_count": len(matched),
        "rendered_page_count": len(rendered),
        "rendered_pages_1_based": [number + 1 for number in ranked],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_COVER_DEPTH_ZONES_UNCERTAINTY_AND_20M_SUPPORT_ARE_REVIEWED",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# McMaster Street as-built drawing extraction\n\n"
        "Review the contact sheet and full renders for final soil-cover thickness, "
        "geotextile limits, Phase 1/Phase 3 boundaries, utilities, storm sewer, building, "
        "railroad and parking exclusions. Do not create execution geometry unless two "
        "same-surface non-overlapping depth zones each contain a clean 20 m interior after "
        "all uncertainty margins. No Earth Engine query is authorized.\n",
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
