"""Extract the map pages needed to evaluate the John Sevier Bottom Ash Pond.

This is a one-off evidence-recovery utility. It downloads TVA's public History of
Construction PDF, indexes page text, renders likely final-configuration and
construction-drawing pages, and writes a machine-readable report. It does not
call Earth Engine, create calibration rows, or enable depth output.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import requests
from PIL import Image, ImageDraw

PDF_URL = (
    "https://www.tva.com/docs/default-source/ccr/jsf/"
    "surface-impoundment---bottom-ash-pond/design-criteria/"
    "history-of-construction/257-73%28c%29-_history-of-construction_"
    "jsf_bottom-ash-pond.pdf?sfvrsn=703326f1_2"
)

KEYWORDS = (
    "bottom ash pond final configuration",
    "construction drawings",
    "final instrumentation layout",
    "unit history exhibit",
    "as-built",
    "stateplane",
    "coordinate system",
    "earthen berm",
    "final cover",
)


def download_pdf(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(PDF_URL, stream=True, timeout=(30, 900)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    if destination.stat().st_size < 10_000_000:
        raise RuntimeError(
            f"Downloaded file is unexpectedly small: {destination.stat().st_size} bytes"
        )


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def select_pages(document: fitz.Document) -> tuple[list[dict[str, object]], list[int]]:
    index: list[dict[str, object]] = []
    selected: set[int] = set(range(min(18, document.page_count)))
    marker_pages: dict[str, list[int]] = {key: [] for key in KEYWORDS}

    for page_number in range(document.page_count):
        text = document.load_page(page_number).get_text("text")
        normalized = clean_text(text)
        lowered = normalized.lower()
        matches = [keyword for keyword in KEYWORDS if keyword in lowered]
        if matches:
            index.append(
                {
                    "page_number_1_based": page_number + 1,
                    "matches": matches,
                    "text_excerpt": normalized[:2000],
                }
            )
            for keyword in matches:
                marker_pages[keyword].append(page_number)
            for nearby in range(max(0, page_number - 2), min(document.page_count, page_number + 4)):
                selected.add(nearby)

    # Appendices often have title pages with text followed by scanned drawing pages.
    appendix_windows = {
        "construction drawings": 20,
        "final instrumentation layout": 8,
        "unit history exhibit": 8,
    }
    for marker, span in appendix_windows.items():
        for page_number in marker_pages[marker]:
            for nearby in range(page_number, min(document.page_count, page_number + span + 1)):
                selected.add(nearby)

    return index, sorted(selected)


def render_pages(document: fitz.Document, page_numbers: list[int], output_dir: Path) -> list[dict[str, object]]:
    rendered: list[dict[str, object]] = []
    pages_dir = output_dir / "rendered_pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    for page_number in page_numbers:
        page = document.load_page(page_number)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
        destination = pages_dir / f"page_{page_number + 1:04d}.png"
        pixmap.save(destination)
        rendered.append(
            {
                "page_number_1_based": page_number + 1,
                "file": str(destination.relative_to(output_dir)),
                "width_px": pixmap.width,
                "height_px": pixmap.height,
            }
        )
    return rendered


def extract_page_images(document: fitz.Document, page_numbers: list[int], output_dir: Path) -> list[dict[str, object]]:
    extracted: list[dict[str, object]] = []
    images_dir = output_dir / "embedded_images"
    images_dir.mkdir(parents=True, exist_ok=True)
    seen_xrefs: set[int] = set()

    for page_number in page_numbers:
        page = document.load_page(page_number)
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = int(image_info[0])
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            payload = document.extract_image(xref)
            extension = payload.get("ext", "bin")
            destination = images_dir / f"page_{page_number + 1:04d}_img_{image_index:02d}_xref_{xref}.{extension}"
            destination.write_bytes(payload["image"])
            extracted.append(
                {
                    "source_page_1_based": page_number + 1,
                    "xref": xref,
                    "file": str(destination.relative_to(output_dir)),
                    "width_px": payload.get("width"),
                    "height_px": payload.get("height"),
                    "extension": extension,
                }
            )
    return extracted


def make_contact_sheets(rendered: list[dict[str, object]], output_dir: Path) -> list[str]:
    page_files = [output_dir / str(item["file"]) for item in rendered]
    output_files: list[str] = []
    if not page_files:
        return output_files

    chunk_size = 12
    thumb_width = 360
    label_height = 34
    margin = 16
    columns = 3

    for chunk_index in range(0, len(page_files), chunk_size):
        chunk = page_files[chunk_index : chunk_index + chunk_size]
        thumbnails: list[tuple[Path, Image.Image]] = []
        max_thumb_height = 0
        for path in chunk:
            image = Image.open(path).convert("RGB")
            ratio = thumb_width / image.width
            thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
            thumbnails.append((path, thumb))
            max_thumb_height = max(max_thumb_height, thumb.height)

        rows = (len(thumbnails) + columns - 1) // columns
        canvas = Image.new(
            "RGB",
            (
                margin + columns * (thumb_width + margin),
                margin + rows * (max_thumb_height + label_height + margin),
            ),
            "white",
        )
        draw = ImageDraw.Draw(canvas)
        for index, (path, thumb) in enumerate(thumbnails):
            row, column = divmod(index, columns)
            x = margin + column * (thumb_width + margin)
            y = margin + row * (max_thumb_height + label_height + margin)
            canvas.paste(thumb, (x, y))
            draw.text((x, y + max_thumb_height + 6), path.stem.replace("page_", "PDF page "), fill="black")

        destination = output_dir / f"contact_sheet_{chunk_index // chunk_size + 1:02d}.jpg"
        canvas.save(destination, quality=90)
        output_files.append(destination.name)
    return output_files


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "artifacts" / "john_sevier_final_configuration"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "john_sevier_history_of_construction.pdf"

    download_pdf(pdf_path)
    document = fitz.open(pdf_path)
    try:
        text_index, selected_pages = select_pages(document)
        rendered = render_pages(document, selected_pages, output_dir)
        embedded_images = extract_page_images(document, selected_pages, output_dir)
        contact_sheets = make_contact_sheets(rendered, output_dir)
        report = {
            "status": "EXTRACTION_COMPLETE_MANUAL_MAP_REVIEW_REQUIRED",
            "source_url": PDF_URL,
            "pdf_bytes": pdf_path.stat().st_size,
            "pdf_page_count": document.page_count,
            "selected_page_count": len(selected_pages),
            "selected_pages_1_based": [page + 1 for page in selected_pages],
            "keyword_hits": text_index,
            "rendered_pages": rendered,
            "embedded_images": embedded_images,
            "contact_sheets": contact_sheets,
            "earth_engine_query_executed": False,
            "calibration_record_created": False,
            "decision": "HOLD_UNTIL_FINAL_CONFIGURATION_MAP_IS_REVIEWED",
        }
        (output_dir / "extraction_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        (output_dir / "README.md").write_text(
            "# John Sevier final-configuration extraction\n\n"
            "Review the contact sheets first, then the full rendered pages. "
            "The objective is to identify the exact eastern capped area, western "
            "excavated/restored area, berm boundary, coordinate references, and "
            "infrastructure exclusions. This extraction does not authorize an "
            "Earth Engine query or a calibration row.\n",
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
