"""Recover Meredosia CQA/as-built evidence from Ameren's public CCR page.

This one-off evidence utility discovers the Construction Quality Assurance PDF from
Ameren's Meredosia page, downloads it, indexes all pages, renders only pages likely
to contain survey/as-built/closure geometry or installed-cover evidence, and writes
machine-readable summaries. It does not call Earth Engine or create calibration rows.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import fitz
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

PAGE_URL = "https://www.ameren.com/sustainability/waste/ccr/inactive-basins/meredosia"
OUT = Path("artifacts/meredosia_cqa_asbuilt")
PDF_PATH = Path("/tmp/meredosia_cqa.pdf")

KEYWORDS = (
    "as-built",
    "as built",
    "record drawing",
    "survey",
    "northing",
    "easting",
    "coordinate",
    "control point",
    "benchmark",
    "horizontal datum",
    "vertical datum",
    "tolerance",
    "accuracy",
    "final grade",
    "final elevation",
    "closureturf",
    "armorfill",
    "geomembrane",
    "bottom ash pond",
    "fly ash pond",
    "east fly ash stockpile",
    "removal boundary",
    "excavation limit",
    "backfill",
    "vegetated",
    "certification",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def discover_pdf_url() -> str:
    response = requests.get(
        PAGE_URL,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0 (compatible; evidence-recovery/1.0)"},
    )
    response.raise_for_status()
    (OUT / "page.html").write_text(response.text, encoding="utf-8")
    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        label = normalize(anchor.get_text(" ", strip=True))
        href = urljoin(PAGE_URL, anchor["href"])
        if "construction quality assurance" in label.lower():
            candidates.append({"label": label, "href": href})
    (OUT / "discovered_links.json").write_text(
        json.dumps(candidates, indent=2), encoding="utf-8"
    )
    if not candidates:
        raise RuntimeError("Construction Quality Assurance link not found on Ameren page")
    return candidates[0]["href"]


def download_pdf(url: str) -> None:
    with requests.get(
        url,
        stream=True,
        timeout=(30, 1200),
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; evidence-recovery/1.0)",
            "Referer": PAGE_URL,
        },
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        total = 0
        with PDF_PATH.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
                    total += len(chunk)
    if total < 10_000:
        raise RuntimeError(f"Downloaded CQA file is too small: {total} bytes")
    if "pdf" not in content_type.lower() and PDF_PATH.read_bytes()[:4] != b"%PDF":
        raise RuntimeError(f"Downloaded CQA file is not PDF: content-type={content_type}")
    (OUT / "download_metadata.json").write_text(
        json.dumps({"url": url, "bytes": total, "content_type": content_type}, indent=2),
        encoding="utf-8",
    )


def contact_sheet(files: list[Path], destination: Path) -> None:
    if not files:
        return
    width = 420
    margin = 16
    label_h = 28
    columns = 2
    thumbs: list[tuple[Path, Image.Image]] = []
    max_h = 0
    for file in files:
        image = Image.open(file).convert("RGB")
        ratio = width / image.width
        thumb = image.resize((width, max(1, int(image.height * ratio))))
        thumbs.append((file, thumb))
        max_h = max(max_h, thumb.height)
    rows = (len(thumbs) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (margin + columns * (width + margin), margin + rows * (max_h + label_h + margin)),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (file, thumb) in enumerate(thumbs):
        row, column = divmod(index, columns)
        x = margin + column * (width + margin)
        y = margin + row * (max_h + label_h + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_h + 4), file.stem, fill="black")
    canvas.save(destination, quality=88)


def extract() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    render_dir = OUT / "rendered_pages"
    render_dir.mkdir(exist_ok=True)

    source_url = discover_pdf_url()
    download_pdf(source_url)

    document = fitz.open(PDF_PATH)
    page_records: list[dict[str, object]] = []
    rendered: list[Path] = []
    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            text = normalize(page.get_text("text"))
            lower = text.lower()
            matches = [keyword for keyword in KEYWORDS if keyword in lower]
            drawings = page.get_drawings()
            images = page.get_images(full=True)
            page_record = {
                "page_number_1_based": page_index + 1,
                "matches": matches,
                "text_excerpt": text[:5000],
                "drawing_count": len(drawings),
                "image_count": len(images),
                "width_points": page.rect.width,
                "height_points": page.rect.height,
            }
            if matches:
                pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
                path = render_dir / f"page_{page_index + 1:04d}.png"
                pix.save(path)
                page_record["rendered_file"] = str(path.relative_to(OUT))
                rendered.append(path)
            page_records.append(page_record)
    finally:
        document.close()

    contact_sheet(rendered[:80], OUT / "contact_sheet_first_80_matches.jpg")
    report = {
        "status": "MEREDOSIA_CQA_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "source_page": PAGE_URL,
        "source_pdf": source_url,
        "page_count": len(page_records),
        "matched_page_count": sum(bool(row["matches"]) for row in page_records),
        "pages": page_records,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_AS_BUILT_GEOMETRY_AND_DEPTH_DEFINITION_ARE_REVIEWED",
    }
    (OUT / "extraction_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (OUT / "README.md").write_text(
        "# Meredosia CQA/as-built extraction\n\n"
        "Review the JSON page index and rendered pages for exact removed-area boundaries, "
        "fly-ash cap geometry, survey controls, tolerances, and final construction elevations. "
        "This is evidence recovery only. No Earth Engine query or calibration row is authorized.\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    report = extract()
    print(json.dumps({
        "status": report["status"],
        "page_count": report["page_count"],
        "matched_page_count": report["matched_page_count"],
        "source_pdf": report["source_pdf"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "failure.json").write_text(
            json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}, indent=2),
            encoding="utf-8",
        )
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
