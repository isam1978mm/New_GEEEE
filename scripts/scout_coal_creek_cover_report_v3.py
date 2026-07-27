"""Recover the exact official LRC-50-F Coal Creek cover document.

This diagnostic-safe one-off extractor writes download and identity evidence
before any validation decision. It accepts the exact official NDIC URL as the
project selector, extracts available text, and renders all pages when the PDF is
image-only. It never calls Earth Engine, creates calibration rows, trains a
model, or enables depth.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import requests
from PIL import Image, ImageDraw

URL = (
    "https://www.ndic.nd.gov/sites/www/files/documents/Lignite-Research-Council/"
    "Grant-Rounds--Final-Reports/Proposals/Grant%20Rounds%2059-50/"
    "LRC-50-F-Alternative-Cover-Demonstration-Project-a.pdf"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
    "Referer": "https://www.ndic.nd.gov/lignite-research-program-grant-rounds-59-50",
}
KEYWORDS = (
    "coal creek", "alternative cover", "cover design", "cover profile",
    "compacted clay", "evapotranspiration", "evapotranspirative", "topsoil",
    "vegetation", "seed", "thickness", "lysimeter", "test cell",
    "test section", "width", "length", "dimension", "as-built", "survey",
    "coordinate", "datum", "monitoring", "decommission", "closure",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_contact_sheet(paths: list[Path], destination: Path) -> None:
    if not paths:
        return
    thumb_w, margin, label_h, cols = 420, 18, 32, 2
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
    output = root / "artifacts" / "coal_creek_cover_scout_v3"
    render_dir = output / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    diagnostic: dict[str, object] = {"requested_url": URL}

    try:
        response = requests.get(URL, headers=HEADERS, timeout=600, allow_redirects=True)
        diagnostic.update(
            {
                "status_code": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("content-type"),
                "content_length": len(response.content),
                "starts_with_pdf_magic": response.content.startswith(b"%PDF-"),
            }
        )
        (output / "download_diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2), encoding="utf-8"
        )
        response.raise_for_status()
        if not response.content.startswith(b"%PDF-"):
            raise RuntimeError("exact official URL did not return PDF bytes")

        pdf_path = Path("/tmp/coal_creek_cover_exact.pdf")
        pdf_path.write_bytes(response.content)
        document = fitz.open(pdf_path)
        page_records: list[dict[str, object]] = []
        matched: set[int] = set()
        total_text_chars = 0
        identity_found = False

        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            text = normalize(page.get_text("text"))
            total_text_chars += len(text)
            lower = text.lower()
            if "coal creek" in lower and "cover" in lower:
                identity_found = True
            matches = [keyword for keyword in KEYWORDS if keyword in lower]
            page_records.append(
                {
                    "page_number_1_based": page_number + 1,
                    "matches": matches,
                    "text_excerpt": text[:24000],
                    "text_character_count": len(text),
                    "width_pt": page.rect.width,
                    "height_pt": page.rect.height,
                    "rotation": page.rotation,
                }
            )
            if matches:
                matched.add(page_number)

        # Image-only reports require visual review, so render every page up to 160.
        if total_text_chars < max(1000, document.page_count * 40):
            selected = list(range(min(document.page_count, 160)))
            extraction_mode = "image_heavy_render_all"
        else:
            selected_set: set[int] = set(range(min(10, document.page_count)))
            for page_number in matched:
                selected_set.update(
                    number
                    for number in (page_number - 1, page_number, page_number + 1)
                    if 0 <= number < document.page_count
                )
            selected = sorted(selected_set)[:120]
            extraction_mode = "text_ranked"

        rendered: list[Path] = []
        for page_number in selected:
            page = document.load_page(page_number)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
            path = render_dir / f"page_{page_number + 1:04d}.png"
            pix.save(path)
            rendered.append(path)

        metadata = document.metadata
        page_count = document.page_count
        document.close()
        pdf_path.unlink(missing_ok=True)

        (output / "page_index.json").write_text(
            json.dumps(page_records, indent=2), encoding="utf-8"
        )
        make_contact_sheet(rendered, output / "contact_sheet.jpg")
        report = {
            "status": "COAL_CREEK_EXACT_DOCUMENT_EXTRACTED_MANUAL_REVIEW_REQUIRED",
            "project": "FY04-50-127 / LRC-50-F",
            "source_url": response.url,
            "pdf_metadata": metadata,
            "page_count": page_count,
            "total_text_characters": total_text_chars,
            "text_identity_found": identity_found,
            "url_identity_confirmed": "LRC-50-F-Alternative-Cover" in response.url,
            "extraction_mode": extraction_mode,
            "rendered_pages_1_based": [n + 1 for n in selected],
            "earth_engine_query_executed": False,
            "calibration_record_created": False,
            "app_depth_enabled": False,
            "decision": "HOLD_UNTIL_PROFILE_GEOMETRY_SURFACE_AND_SURVIVAL_REVIEW",
        }
        (output / "extraction_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        return 0
    except Exception as exc:
        diagnostic["error"] = f"{type(exc).__name__}: {exc}"
        (output / "failure.json").write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
        print(json.dumps(diagnostic, indent=2), file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
