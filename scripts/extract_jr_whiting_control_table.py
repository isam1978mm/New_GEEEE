"""Extract word-level data from the J.R. Whiting construction control-point table.

The target is PDF page 30 of Final Construction Documentation Report part 1.
The output preserves vector-text coordinates so the 107 final-cover thickness
rows can be reconstructed without OCR. It does not call Earth Engine, create a
calibration row, or enable depth output.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF

TARGET_PAGE_1_BASED = 30


def main() -> int:
    source_value = os.environ.get("JR_WHITING_REPORT_1")
    if not source_value:
        raise RuntimeError("JR_WHITING_REPORT_1 is required")
    source_path = Path(source_value)
    if not source_path.exists():
        raise RuntimeError(f"Source PDF not found: {source_path}")

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "artifacts" / "jr_whiting_control_table"
    output_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(source_path)
    try:
        if document.page_count < TARGET_PAGE_1_BASED:
            raise RuntimeError(
                f"Report has only {document.page_count} pages; target page is {TARGET_PAGE_1_BASED}"
            )
        page = document.load_page(TARGET_PAGE_1_BASED - 1)
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
        raw_text = page.get_text("text", sort=True)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4), alpha=False)
        rendered_path = output_dir / "page_0030_control_point_table.png"
        pixmap.save(rendered_path)

        payload = {
            "status": "CONTROL_TABLE_VECTOR_TEXT_EXTRACTED",
            "source_file": source_path.name,
            "source_bytes": source_path.stat().st_size,
            "pdf_page_count": document.page_count,
            "target_page_1_based": TARGET_PAGE_1_BASED,
            "page_width_points": page.rect.width,
            "page_height_points": page.rect.height,
            "word_count": len(words),
            "block_count": len(blocks),
            "words": words,
            "blocks": blocks,
            "earth_engine_query_executed": False,
            "calibration_record_created": False,
            "decision": "HOLD_PENDING_TABLE_RECONSTRUCTION_AND_SURVEY_ACCURACY",
        }
        (output_dir / "page_0030_words.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        (output_dir / "page_0030_raw_text.txt").write_text(raw_text, encoding="utf-8")
        (output_dir / "README.md").write_text(
            "# J.R. Whiting control-point table extraction\n\n"
            "This artifact contains vector-text word coordinates, text blocks, raw "
            "text, and a high-resolution rendering of PDF page 30 from report part 1. "
            "Use it to reconstruct control points 1000-1106 and their final-cover "
            "thicknesses without OCR. It does not authorize an Earth Engine query or "
            "a calibration row.\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "word_count": len(words),
                    "block_count": len(blocks),
                    "rendered_file": str(rendered_path),
                },
                indent=2,
            )
        )
    finally:
        document.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
