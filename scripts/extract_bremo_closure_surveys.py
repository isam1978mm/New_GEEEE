"""Extract survey and final-acceptance evidence from Bremo Bluff closure reports.

This one-off evidence-recovery utility scans already-downloaded official Virginia
DEQ construction-report PDFs, builds a page index, renders likely survey and
record-drawing pages, and creates low-resolution contact sheets. It does not call
Earth Engine, create calibration rows, or enable depth output.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

KEYWORDS: dict[str, int] = {
    "survey": 10,
    "surveyed": 10,
    "as-built": 14,
    "as built": 14,
    "record drawing": 14,
    "final survey": 16,
    "topographic": 9,
    "coordinate": 9,
    "state plane": 14,
    "nad83": 14,
    "benchmark": 12,
    "accuracy": 14,
    "tolerance": 8,
    "grid": 8,
    "cell": 5,
    "excavation limit": 14,
    "excavation limits": 14,
    "native soil": 12,
    "visual inspection": 10,
    "acceptance": 9,
    "accepted": 9,
    "clean": 8,
    "verification": 8,
    "restoration": 7,
    "seed": 5,
    "vegetation": 5,
    "final grade": 9,
    "east ash pond": 4,
    "west ash pond": 4,
    "drawing": 4,
    "appendix": 3,
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def score_page(text: str) -> tuple[int, list[str]]:
    lowered = text.lower()
    matches: list[str] = []
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword in lowered:
            matches.append(keyword)
            score += weight
    return score, matches


def make_contact_sheets(document: fitz.Document, output_dir: Path, stem: str) -> list[str]:
    sheets_dir = output_dir / "contact_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    per_sheet = 30
    columns = 5
    thumb_width = 210
    margin = 10
    label_height = 24
    results: list[str] = []

    for start in range(0, document.page_count, per_sheet):
        entries: list[tuple[int, Image.Image]] = []
        max_height = 0
        for page_index in range(start, min(document.page_count, start + per_sheet)):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.34, 0.34), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            ratio = thumb_width / image.width
            thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
            entries.append((page_index + 1, thumb))
            max_height = max(max_height, thumb.height)

        rows = (len(entries) + columns - 1) // columns
        canvas = Image.new(
            "RGB",
            (
                margin + columns * (thumb_width + margin),
                margin + rows * (max_height + label_height + margin),
            ),
            "white",
        )
        draw = ImageDraw.Draw(canvas)
        for idx, (page_number, thumb) in enumerate(entries):
            row, column = divmod(idx, columns)
            x = margin + column * (thumb_width + margin)
            y = margin + row * (max_height + label_height + margin)
            canvas.paste(thumb, (x, y))
            draw.text((x, y + max_height + 4), f"p{page_number}", fill="black")

        destination = sheets_dir / f"{stem}_{start + 1:04d}_{min(document.page_count, start + per_sheet):04d}.jpg"
        canvas.save(destination, quality=85)
        results.append(str(destination.relative_to(output_dir)))
    return results


def process_pdf(pdf_path: Path, output_root: Path) -> dict[str, object]:
    stem = pdf_path.stem
    report_dir = output_root / stem
    selected_dir = report_dir / "selected_pages"
    selected_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    records: list[dict[str, object]] = []

    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            text = normalize(page.get_text("text"))
            score, matches = score_page(text)
            records.append(
                {
                    "page_number_1_based": page_index + 1,
                    "score": score,
                    "matches": matches,
                    "text_length": len(text),
                    "image_count": len(page.get_images(full=True)),
                    "drawing_count": len(page.get_drawings()),
                    "text_excerpt": text[:3500],
                }
            )

        ranked = sorted(records, key=lambda item: (-int(item["score"]), int(item["page_number_1_based"])))
        selected: set[int] = set(range(min(6, document.page_count)))
        selected.update(range(max(0, document.page_count - 10), document.page_count))
        for record in ranked[:50]:
            if int(record["score"]) <= 0:
                break
            page_index = int(record["page_number_1_based"]) - 1
            for nearby in range(max(0, page_index - 1), min(document.page_count, page_index + 2)):
                selected.add(nearby)

        rendered: list[dict[str, object]] = []
        for page_index in sorted(selected):
            page = document.load_page(page_index)
            destination = selected_dir / f"page_{page_index + 1:04d}.png"
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
            pixmap.save(destination)
            rendered.append(
                {
                    "page_number_1_based": page_index + 1,
                    "score": records[page_index]["score"],
                    "matches": records[page_index]["matches"],
                    "file": str(destination.relative_to(output_root)),
                    "width_px": pixmap.width,
                    "height_px": pixmap.height,
                }
            )

        contacts = make_contact_sheets(document, report_dir, stem)
        payload = {
            "source_file": pdf_path.name,
            "source_bytes": pdf_path.stat().st_size,
            "page_count": document.page_count,
            "ranked_pages": ranked,
            "rendered_selected_pages": rendered,
            "contact_sheets": [str((report_dir / item).relative_to(output_root)) for item in contacts],
        }
        (report_dir / "page_index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
    finally:
        document.close()


def main() -> int:
    source_value = os.environ.get("BREMO_SOURCE_DIR")
    if not source_value:
        raise RuntimeError("BREMO_SOURCE_DIR is required")
    source_dir = Path(source_value)
    pdfs = sorted(source_dir.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDF files found in {source_dir}")

    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / "artifacts" / "bremo_closure_surveys"
    output_root.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for pdf_path in pdfs:
        try:
            reports.append(process_pdf(pdf_path, output_root))
        except Exception as exc:
            failures.append({"source_file": pdf_path.name, "error": str(exc)})

    result = {
        "status": "EXTRACTION_COMPLETE_MANUAL_SURVEY_REVIEW_REQUIRED" if reports else "EXTRACTION_FAILED",
        "source_pdf_count": len(pdfs),
        "processed_pdf_count": len(reports),
        "reports": reports,
        "failures": failures,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_FINAL_SURVEY_AND_ACCEPTANCE_PAGES_ARE_REVIEWED",
    }
    (output_root / "extraction_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output_root / "README.md").write_text(
        "# Bremo Bluff closure-survey extraction\n\n"
        "Review each contact sheet, then the high-scoring full-resolution pages for "
        "final survey coordinates, accepted excavation cells, native-soil verification, "
        "restoration geometry, accuracy, and stable-surface evidence. Source PDFs are "
        "excluded. No Earth Engine query or calibration row is authorized.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0 if reports else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
