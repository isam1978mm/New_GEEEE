"""Extract Plant Kraft AP-1 engineering-map pages from the official CCR removal PDF.

This one-off evidence-recovery utility accepts an already-downloaded official
Certification of CCR Removal PDF. It renders the likely engineering-map pages,
exports SVG/vector text, extracts embedded images, and writes page-level word and
drawing metadata. It does not call Earth Engine, create a calibration row, or
enable depth output.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Include surrounding pages because PDF page numbering and printed figure numbering
# do not necessarily align. Values are 1-based PDF page numbers.
SELECTED_PAGES_1_BASED = list(range(7, 15))


def serialize_drawing(drawing: dict) -> dict:
    result: dict[str, object] = {}
    for key, value in drawing.items():
        if key == "items":
            serialized_items: list[list[object]] = []
            for item in value:
                row: list[object] = []
                for part in item:
                    if isinstance(part, fitz.Point):
                        row.append([part.x, part.y])
                    elif isinstance(part, fitz.Rect):
                        row.append([part.x0, part.y0, part.x1, part.y1])
                    elif isinstance(part, fitz.Quad):
                        row.append([[point.x, point.y] for point in part])
                    else:
                        row.append(part)
                serialized_items.append(row)
            result[key] = serialized_items
        elif isinstance(value, fitz.Rect):
            result[key] = [value.x0, value.y0, value.x1, value.y1]
        elif isinstance(value, fitz.Point):
            result[key] = [value.x, value.y]
        elif isinstance(value, tuple):
            result[key] = list(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
    return result


def create_contact_sheet(page_files: list[tuple[int, Path]], destination: Path) -> None:
    if not page_files:
        return
    thumb_width = 440
    margin = 16
    label_height = 34
    columns = 2
    thumbs: list[tuple[int, Image.Image]] = []
    max_height = 0
    for page_number, path in page_files:
        image = Image.open(path).convert("RGB")
        ratio = thumb_width / image.width
        thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
        thumbs.append((page_number, thumb))
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
    for index, (page_number, thumb) in enumerate(thumbs):
        row, column = divmod(index, columns)
        x = margin + column * (thumb_width + margin)
        y = margin + row * (max_height + label_height + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_height + 6), f"PDF page {page_number}", fill="black")
    canvas.save(destination, quality=90)


def main() -> int:
    source_value = os.environ.get("PLANT_KRAFT_SOURCE_PDF")
    if not source_value:
        raise RuntimeError("PLANT_KRAFT_SOURCE_PDF is required")
    source_path = Path(source_value)
    if not source_path.exists():
        raise RuntimeError(f"Source PDF not found: {source_path}")

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "artifacts" / "plant_kraft_ap1_maps"
    renders_dir = output_dir / "renders"
    svg_dir = output_dir / "svg"
    metadata_dir = output_dir / "metadata"
    images_dir = output_dir / "embedded_images"
    for directory in (renders_dir, svg_dir, metadata_dir, images_dir):
        directory.mkdir(parents=True, exist_ok=True)

    document = fitz.open(source_path)
    page_reports: list[dict[str, object]] = []
    rendered_pages: list[tuple[int, Path]] = []
    seen_image_xrefs: set[int] = set()
    try:
        for page_number_1_based in SELECTED_PAGES_1_BASED:
            if page_number_1_based > document.page_count:
                continue
            page_index = page_number_1_based - 1
            page = document.load_page(page_index)

            render_path = renders_dir / f"page_{page_number_1_based:03d}.png"
            pixmap = page.get_pixmap(matrix=fitz.Matrix(3.5, 3.5), alpha=False)
            pixmap.save(render_path)
            rendered_pages.append((page_number_1_based, render_path))

            svg_path = svg_dir / f"page_{page_number_1_based:03d}.svg"
            svg_path.write_text(
                page.get_svg_image(matrix=fitz.Matrix(1.0, 1.0), text_as_path=False),
                encoding="utf-8",
            )

            words = [
                {
                    "x0": item[0],
                    "y0": item[1],
                    "x1": item[2],
                    "y1": item[3],
                    "text": item[4],
                    "block_no": item[5],
                    "line_no": item[6],
                    "word_no": item[7],
                }
                for item in page.get_text("words", sort=True)
            ]
            blocks = [
                {
                    "x0": item[0],
                    "y0": item[1],
                    "x1": item[2],
                    "y1": item[3],
                    "text": item[4],
                    "block_no": item[5],
                    "block_type": item[6],
                }
                for item in page.get_text("blocks", sort=True)
            ]
            drawings = [serialize_drawing(drawing) for drawing in page.get_drawings()]

            extracted_images: list[dict[str, object]] = []
            for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                xref = int(image_info[0])
                if xref in seen_image_xrefs:
                    continue
                seen_image_xrefs.add(xref)
                payload = document.extract_image(xref)
                extension = payload.get("ext", "bin")
                image_path = images_dir / (
                    f"page_{page_number_1_based:03d}_img_{image_index:02d}_xref_{xref}.{extension}"
                )
                image_path.write_bytes(payload["image"])
                extracted_images.append(
                    {
                        "xref": xref,
                        "file": str(image_path.relative_to(output_dir)),
                        "width_px": payload.get("width"),
                        "height_px": payload.get("height"),
                        "extension": extension,
                    }
                )

            page_payload = {
                "page_number_1_based": page_number_1_based,
                "page_width_points": page.rect.width,
                "page_height_points": page.rect.height,
                "rotation": page.rotation,
                "raw_text": page.get_text("text", sort=True),
                "word_count": len(words),
                "block_count": len(blocks),
                "drawing_count": len(drawings),
                "words": words,
                "blocks": blocks,
                "drawings": drawings,
                "embedded_images": extracted_images,
                "render_file": str(render_path.relative_to(output_dir)),
                "svg_file": str(svg_path.relative_to(output_dir)),
            }
            metadata_path = metadata_dir / f"page_{page_number_1_based:03d}.json"
            metadata_path.write_text(json.dumps(page_payload, indent=2), encoding="utf-8")
            page_reports.append(
                {
                    "page_number_1_based": page_number_1_based,
                    "word_count": len(words),
                    "block_count": len(blocks),
                    "drawing_count": len(drawings),
                    "embedded_image_count": len(extracted_images),
                    "render_file": str(render_path.relative_to(output_dir)),
                    "svg_file": str(svg_path.relative_to(output_dir)),
                    "metadata_file": str(metadata_path.relative_to(output_dir)),
                }
            )

        contact_path = output_dir / "contact_sheet_pages_007_014.jpg"
        create_contact_sheet(rendered_pages, contact_path)
        report = {
            "status": "AP1_MAP_EXTRACTION_COMPLETE_MANUAL_GEOMETRY_REVIEW_REQUIRED",
            "source_file": source_path.name,
            "source_bytes": source_path.stat().st_size,
            "pdf_page_count": document.page_count,
            "selected_pages_1_based": SELECTED_PAGES_1_BASED,
            "pages": page_reports,
            "contact_sheet": contact_path.name,
            "earth_engine_query_executed": False,
            "calibration_record_created": False,
            "decision": "HOLD_UNTIL_EXCAVATION_LIMIT_AND_SURVEY_NOTES_ARE_REVIEWED",
        }
        (output_dir / "extraction_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        (output_dir / "README.md").write_text(
            "# Plant Kraft AP-1 map extraction\n\n"
            "Review the contact sheet, then pages 7-14 at full resolution. SVG and "
            "word/drawing metadata are included to support exact extraction of the "
            "post-excavation limit and survey notes. The source PDF is intentionally "
            "excluded. No Earth Engine query or calibration row is authorized.\n",
            encoding="utf-8",
        )
        print(json.dumps(report, indent=2))
    finally:
        document.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
