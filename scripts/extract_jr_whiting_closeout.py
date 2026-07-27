"""Extract survey evidence from the six J.R. Whiting Pond 1 & 2 closeout PDFs.

This one-off evidence-recovery utility scans already-downloaded official PDFs,
creates a page-level keyword index, renders likely survey/record-drawing pages,
and builds thumbnail contact sheets for every page. It does not call Earth
Engine, create calibration rows, or enable depth output.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw

KEYWORDS: dict[str, int] = {
    "rowe": 12,
    "survey": 8,
    "surveyed": 8,
    "record drawing": 12,
    "as-built": 12,
    "as built": 12,
    "topsoil": 10,
    "subgrade": 10,
    "cover thickness": 12,
    "thickness": 6,
    "control point": 10,
    "control points": 10,
    "benchmark": 10,
    "vertical accuracy": 16,
    "horizontal accuracy": 16,
    "accuracy": 9,
    "tolerance": 7,
    "ngvd": 10,
    "navd": 10,
    "datum": 7,
    "elevation": 5,
    "elevations": 5,
    "1000": 5,
    "1106": 5,
    "pond 1": 3,
    "pond 2": 3,
    "final cover": 7,
    "construction documentation": 4,
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def page_score(text: str) -> tuple[int, list[str]]:
    lowered = text.lower()
    matches: list[str] = []
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword in lowered:
            matches.append(keyword)
            score += weight
    return score, matches


def render_page(page: fitz.Page, destination: Path, scale: float = 1.7) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    pixmap.save(destination)
    return {
        "file": str(destination),
        "width_px": pixmap.width,
        "height_px": pixmap.height,
    }


def build_contact_sheets(document: fitz.Document, output_dir: Path, stem: str) -> list[str]:
    sheets_dir = output_dir / "contact_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    per_sheet = 24
    columns = 4
    thumb_width = 260
    margin = 12
    label_height = 28
    output_files: list[str] = []

    for start in range(0, document.page_count, per_sheet):
        thumbs: list[tuple[int, Image.Image]] = []
        max_height = 0
        for page_number in range(start, min(document.page_count, start + per_sheet)):
            page = document.load_page(page_number)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.42, 0.42), alpha=False)
            mode = "RGB"
            image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
            ratio = thumb_width / image.width
            thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
            thumbs.append((page_number + 1, thumb))
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
        for index, (page_number_1_based, thumb) in enumerate(thumbs):
            row, column = divmod(index, columns)
            x = margin + column * (thumb_width + margin)
            y = margin + row * (max_height + label_height + margin)
            canvas.paste(thumb, (x, y))
            draw.text((x, y + max_height + 5), f"PDF page {page_number_1_based}", fill="black")

        destination = sheets_dir / f"{stem}_pages_{start + 1:04d}_{min(document.page_count, start + per_sheet):04d}.jpg"
        canvas.save(destination, quality=88)
        output_files.append(str(destination.relative_to(output_dir)))
    return output_files


def process_pdf(pdf_path: Path, output_root: Path) -> dict[str, object]:
    stem = pdf_path.stem
    report_dir = output_root / stem
    report_dir.mkdir(parents=True, exist_ok=True)
    selected_dir = report_dir / "selected_pages"
    document = fitz.open(pdf_path)
    page_records: list[dict[str, object]] = []

    try:
        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            text = normalize(page.get_text("text"))
            score, matches = page_score(text)
            page_records.append(
                {
                    "page_number_1_based": page_number + 1,
                    "score": score,
                    "matches": matches,
                    "text_length": len(text),
                    "image_count": len(page.get_images(full=True)),
                    "text_excerpt": text[:4000],
                }
            )

        ranked = sorted(page_records, key=lambda item: (-int(item["score"]), int(item["page_number_1_based"])))
        selected: set[int] = set()
        # Always include the beginning/end for title pages, TOCs, appendices and certifications.
        selected.update(range(min(8, document.page_count)))
        selected.update(range(max(0, document.page_count - 8), document.page_count))
        for record in ranked[:35]:
            if int(record["score"]) <= 0:
                break
            page_index = int(record["page_number_1_based"]) - 1
            for nearby in range(max(0, page_index - 1), min(document.page_count, page_index + 2)):
                selected.add(nearby)

        rendered: list[dict[str, object]] = []
        for page_index in sorted(selected):
            destination = selected_dir / f"page_{page_index + 1:04d}.png"
            render_info = render_page(document.load_page(page_index), destination)
            render_info.update(
                {
                    "page_number_1_based": page_index + 1,
                    "score": page_records[page_index]["score"],
                    "matches": page_records[page_index]["matches"],
                    "file": str(destination.relative_to(output_root)),
                }
            )
            rendered.append(render_info)

        contact_sheets = build_contact_sheets(document, report_dir, stem)
        result = {
            "source_file": pdf_path.name,
            "source_bytes": pdf_path.stat().st_size,
            "page_count": document.page_count,
            "selected_page_count": len(rendered),
            "ranked_pages": ranked,
            "rendered_selected_pages": rendered,
            "contact_sheets": [str((report_dir / item).relative_to(output_root)) for item in contact_sheets],
        }
        (report_dir / "page_index.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    finally:
        document.close()


def main() -> int:
    source_dir_value = os.environ.get("JR_WHITING_SOURCE_DIR")
    if not source_dir_value:
        raise RuntimeError("JR_WHITING_SOURCE_DIR is required")
    source_dir = Path(source_dir_value)
    pdfs = sorted(source_dir.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {source_dir}")

    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / "artifacts" / "jr_whiting_closeout"
    output_root.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for pdf_path in pdfs:
        try:
            reports.append(process_pdf(pdf_path, output_root))
        except Exception as exc:  # Preserve progress if one part is malformed.
            failures.append({"source_file": pdf_path.name, "error": str(exc)})

    result = {
        "status": "EXTRACTION_COMPLETE_MANUAL_SURVEY_REVIEW_REQUIRED" if reports else "EXTRACTION_FAILED",
        "source_pdf_count": len(pdfs),
        "processed_pdf_count": len(reports),
        "failures": failures,
        "reports": reports,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_SURVEY_TABLES_AND_ACCURACY_NOTES_ARE_REVIEWED",
    }
    (output_root / "extraction_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output_root / "README.md").write_text(
        "# J.R. Whiting closeout extraction\n\n"
        "Review each report's contact sheets, then open the high-resolution selected "
        "pages with the strongest survey, ROWE, topsoil, subgrade, record-drawing, "
        "datum, benchmark, accuracy, tolerance, and elevation matches. Source PDFs "
        "are intentionally excluded from the artifact. No Earth Engine query or "
        "calibration row is authorized by this extraction.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    if not reports:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
