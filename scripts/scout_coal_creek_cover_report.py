"""Recover and screen the Coal Creek Station alternative-cover final report.

One-off evidence scout. It discovers the North Dakota Industrial Commission
FY04-50-127 final-report link, downloads the official report, extracts text and
renders pages relevant to cover profiles, dimensions, vegetation, construction,
monitoring duration, decommissioning, survey control, and Sentinel-1-era
persistence.

It does not call Earth Engine, create calibration rows, train a model, or enable
depth output.
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

PAGE_URLS = (
    "https://www.ndic.nd.gov/lignite-research-program-grant-rounds-59-50",
    "https://www.ndic.nd.gov/research-grant-programs/lignite-research-program/"
    "lignite-research-program-grant-rounds/lignite-research-program-grant-rounds-59-50",
)
PROJECT_MARKERS = (
    "FY04-50-127",
    "Alternative Cover Demonstration Project at Coal Creek Station",
    "LRC-50-F",
)
KEYWORDS = (
    "cover profile",
    "cover design",
    "compacted clay",
    "evapotranspiration",
    "evapotranspirative",
    "topsoil",
    "vegetation",
    "seed",
    "thickness",
    "feet thick",
    "inches thick",
    "lysimeter",
    "test cell",
    "test section",
    "dimensions",
    "width",
    "length",
    "as-built",
    "as built",
    "survey",
    "coordinate",
    "datum",
    "monitoring",
    "decommission",
    "removed",
    "closure",
    "final cover",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def fetch_index(output: Path) -> tuple[str, str]:
    errors: list[str] = []
    for url in PAGE_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=120, allow_redirects=True)
            response.raise_for_status()
            text = response.text
            if not any(marker.lower() in text.lower() for marker in PROJECT_MARKERS):
                raise RuntimeError("project marker not found in returned HTML")
            (output / "ndic_index.html").write_text(text, encoding="utf-8")
            return response.url, text
        except Exception as exc:  # pragma: no cover - network-specific
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors))


def discover_links(base_url: str, html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor.get("href", ""))
        label = normalize(anchor.get_text(" ", strip=True))
        context = ""
        node = anchor
        for _ in range(8):
            node = node.parent
            if node is None:
                break
            context = normalize(node.get_text(" ", strip=True))
            if any(marker.lower() in context.lower() for marker in PROJECT_MARKERS):
                break
        if not context:
            context = label
        records.append({"label": label, "url": href, "context": context[:4000]})

    # Rank links that are actually associated with project 127.
    def score(record: dict[str, str]) -> tuple[int, int]:
        combined = f"{record['label']} {record['url']} {record['context']}".lower()
        value = 0
        if "fy04-50-127" in combined or "lrc-50-f" in combined:
            value += 100
        if "alternative cover demonstration project at coal creek" in combined:
            value += 80
        if "final report" in combined:
            value += 40
        if ".pdf" in record["url"].lower():
            value += 20
        return (-value, len(record["url"]))

    ranked = sorted(records, key=score)
    return [record for record in ranked if -score(record)[0] >= 40]


def download_report(candidates: list[dict[str, str]], destination: Path) -> tuple[str, list[str]]:
    errors: list[str] = []
    for record in candidates:
        url = record["url"]
        try:
            response = requests.get(url, headers=HEADERS, timeout=600, allow_redirects=True)
            response.raise_for_status()
            body = response.content
            content_type = response.headers.get("content-type", "")
            if not body.startswith(b"%PDF-"):
                raise RuntimeError(f"not a PDF: {content_type}; {len(body)} bytes")
            destination.write_bytes(body)
            return response.url, errors
        except Exception as exc:  # pragma: no cover - network-specific
            errors.append(f"{url}: {exc}")
            destination.unlink(missing_ok=True)
    raise RuntimeError("No candidate produced a PDF. " + "; ".join(errors))


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


def extract_report(pdf_path: Path, output: Path, source_url: str) -> dict[str, object]:
    render_dir = output / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    page_records: list[dict[str, object]] = []
    matched: set[int] = set()
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        text = normalize(page.get_text("text"))
        lower = text.lower()
        matches = [keyword for keyword in KEYWORDS if keyword in lower]
        page_records.append(
            {
                "page_number_1_based": page_number + 1,
                "matches": matches,
                "text_excerpt": text[:16000],
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
                "rotation": page.rotation,
            }
        )
        if matches:
            matched.add(page_number)

    selected: set[int] = set(range(min(8, document.page_count)))
    for page_number in matched:
        selected.update(
            number
            for number in (page_number - 1, page_number, page_number + 1)
            if 0 <= number < document.page_count
        )
    ranked = sorted(selected, key=lambda n: (-len(page_records[n]["matches"]), n))[:100]
    ranked.sort()

    rendered: list[Path] = []
    for page_number in ranked:
        page = document.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        path = render_dir / f"page_{page_number + 1:04d}.png"
        pix.save(path)
        rendered.append(path)
    metadata = document.metadata
    page_count = document.page_count
    document.close()

    (output / "page_index.json").write_text(
        json.dumps(page_records, indent=2), encoding="utf-8"
    )
    make_contact_sheet(rendered, output / "contact_sheet.jpg")
    report = {
        "status": "COAL_CREEK_FINAL_REPORT_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "project": "FY04-50-127",
        "source_url": source_url,
        "pdf_metadata": metadata,
        "page_count": page_count,
        "matched_page_count": len(matched),
        "rendered_pages_1_based": [number + 1 for number in ranked],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_PROFILE_GEOMETRY_SURFACE_AND_SURVIVAL_REVIEW",
    }
    (output / "extraction_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "coal_creek_cover_scout"
    output.mkdir(parents=True, exist_ok=True)
    index_url, html = fetch_index(output)
    links = discover_links(index_url, html)
    (output / "link_inventory.json").write_text(
        json.dumps(links, indent=2), encoding="utf-8"
    )
    if not links:
        raise RuntimeError("No FY04-50-127 final-report links were discovered")
    pdf_path = Path("/tmp/coal_creek_cover_final_report.pdf")
    source_url, errors = download_report(links, pdf_path)
    (output / "download_attempts.json").write_text(
        json.dumps({"successful_url": source_url, "prior_errors": errors}, indent=2),
        encoding="utf-8",
    )
    report = extract_report(pdf_path, output, source_url)
    pdf_path.unlink(missing_ok=True)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "EXTRACTION_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
