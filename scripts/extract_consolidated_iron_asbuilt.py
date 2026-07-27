"""Recover Consolidated Iron and Metal final-remedy survey evidence.

This one-off research utility loads EPA's dynamic Superfund document pages with
Chromium, records the document-table network traffic, downloads linked EPA PDFs,
and indexes pages relevant to actual excavation depths, geotextile elevations,
as-built surveys, final surface elevations, accuracy, geometry, and subsequent
site changes. It does not call Earth Engine, create calibration rows, train a
model, or enable application depth output.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import fitz
import requests
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

SITE_ID = "0204175"
EPA_ID = "NY0002455756"
PROFILE_URL = f"https://cumulis.epa.gov/supercpad/cursites/csitinfo.cfm?id={SITE_ID}"
COLLECTION_URL = (
    "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?"
    f"colid=70219&doc=Y&fuseaction=second.scs&id={SITE_ID}&region=02&type=SC"
)
DOCUMENTS_URL = (
    "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?"
    f"fuseaction=second.docdata&id={SITE_ID}"
)
CLEANUP_URL = (
    "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?"
    f"fuseaction=second.cleanup&id={SITE_ID}"
)

KEYWORDS = (
    "remedial action report",
    "final remedial action",
    "as-built",
    "as built",
    "record drawing",
    "licensed surveyor",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "northing",
    "easting",
    "coordinate system",
    "state plane",
    "navd",
    "geotextile",
    "demarcation layer",
    "demarcation fabric",
    "bottom of excavation",
    "excavation bottom",
    "excavation depth",
    "final grade",
    "final surface",
    "water table",
    "50-foot grid",
    "50 foot grid",
    "lift layer",
    "six feet",
    "6 feet",
    "topsoil",
    "hydroseed",
    "site modification plan",
    "environmental easement",
    "redevelopment",
)

PDF_URL_RE = re.compile(
    r"https?://[^\s\"'<>]+(?:\.pdf(?:\?[^\s\"'<>]*)?|/src/document/[^\s\"'<>]+|/work/\d{2}/[^\s\"'<>]+)",
    re.I,
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def safe_name(url: str, index: int) -> str:
    path = urlparse(url).path
    stem = Path(path).name or f"document_{index:02d}"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
    if not stem.lower().endswith(".pdf"):
        stem += ".pdf"
    return f"{index:02d}_{stem}"


def make_contact_sheet(paths: list[Path], destination: Path) -> None:
    if not paths:
        return
    thumb_width = 420
    margin = 18
    label_height = 34
    columns = 2
    thumbs: list[tuple[Path, Image.Image]] = []
    max_height = 0
    for path in paths:
        image = Image.open(path).convert("RGB")
        ratio = thumb_width / image.width
        thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
        thumbs.append((path, thumb))
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
    for idx, (path, thumb) in enumerate(thumbs):
        row, col = divmod(idx, columns)
        x = margin + col * (thumb_width + margin)
        y = margin + row * (max_height + label_height + margin)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + max_height + 6), path.stem, fill="black")
    canvas.save(destination, quality=88)


async def discover_dynamic_documents(output: Path) -> dict[str, object]:
    pages = {
        "profile": PROFILE_URL,
        "collection": COLLECTION_URL,
        "documents": DOCUMENTS_URL,
        "cleanup": CLEANUP_URL,
    }
    discovered: set[str] = set()
    network_records: list[dict[str, object]] = []
    page_records: list[dict[str, object]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/126.0 Safari/537.36 environmental-evidence-recovery/1.0"
            ),
            accept_downloads=True,
        )

        async def visit(label: str, url: str) -> None:
            page = await context.new_page()
            responses: list[dict[str, object]] = []

            async def capture(response) -> None:  # noqa: ANN001
                record: dict[str, object] = {
                    "url": response.url,
                    "status": response.status,
                    "content_type": response.headers.get("content-type", ""),
                }
                relevant = any(
                    token in response.url.lower()
                    for token in ("document", "datatable", "ajax", "collection", "scs", "semspub")
                )
                if relevant:
                    try:
                        body = await response.body()
                        if len(body) <= 4_000_000:
                            text = body.decode("utf-8", errors="replace")
                            record["body_excerpt"] = text[:250_000]
                            discovered.update(PDF_URL_RE.findall(text))
                    except Exception as exc:  # best-effort diagnostic capture
                        record["body_error"] = str(exc)
                    responses.append(record)

            page.on("response", capture)
            await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            try:
                await page.wait_for_load_state("networkidle", timeout=45_000)
            except Exception:
                pass
            await page.wait_for_timeout(12_000)

            html = await page.content()
            (output / f"{label}.html").write_text(html, encoding="utf-8")
            discovered.update(PDF_URL_RE.findall(html))
            anchors = await page.eval_on_selector_all(
                "a",
                "els => els.map(a => ({text:(a.innerText||a.textContent||'').trim(), href:a.href||''}))",
            )
            for anchor in anchors:
                href = str(anchor.get("href", ""))
                text = str(anchor.get("text", ""))
                if href:
                    lower = href.lower()
                    if "semspub.epa.gov" in lower or lower.endswith(".pdf") or "/src/document/" in lower:
                        discovered.add(href)
                # Preserve announcement links even when JavaScript redirects them.
                if any(term in text.lower() for term in ("five-year review", "remedial action", "site modification")):
                    page_records.append({"page": label, "text": text, "href": href})
            page_records.append(
                {
                    "page": label,
                    "url": url,
                    "title": await page.title(),
                    "anchor_count": len(anchors),
                    "anchors": anchors,
                }
            )
            network_records.extend({"page": label, **record} for record in responses)
            await page.close()

        for label, url in pages.items():
            await visit(label, url)
        await browser.close()

    # Normalize HTML-escaped ampersands and strip trailing punctuation.
    normalized: set[str] = set()
    for url in discovered:
        value = url.replace("&amp;", "&").rstrip(".,);]")
        if value.startswith("/"):
            value = urljoin("https://semspub.epa.gov", value)
        normalized.add(value)

    (output / "page_records.json").write_text(json.dumps(page_records, indent=2), encoding="utf-8")
    (output / "network_records.json").write_text(json.dumps(network_records, indent=2), encoding="utf-8")
    (output / "discovered_urls.json").write_text(json.dumps(sorted(normalized), indent=2), encoding="utf-8")
    return {
        "pages_visited": list(pages.values()),
        "discovered_urls": sorted(normalized),
        "network_record_count": len(network_records),
    }


def download_candidates(urls: list[str], source_dir: Path, output: Path) -> list[dict[str, object]]:
    source_dir.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
        "Referer": PROFILE_URL,
    }
    records: list[dict[str, object]] = []
    seen_hashes: set[str] = set()
    for index, url in enumerate(urls, start=1):
        record: dict[str, object] = {"url": url}
        try:
            response = requests.get(url, headers=headers, timeout=300, allow_redirects=True)
            record["status_code"] = response.status_code
            record["final_url"] = response.url
            record["content_type"] = response.headers.get("content-type", "")
            response.raise_for_status()
            body = response.content
            if not body.startswith(b"%PDF-"):
                record["decision"] = "not_pdf"
                record["bytes"] = len(body)
                # A document landing page may expose a direct PDF URL.
                text = body.decode("utf-8", errors="replace")
                nested = sorted(set(PDF_URL_RE.findall(text)))
                record["nested_pdf_urls"] = nested
                records.append(record)
                continue
            digest = hashlib.sha256(body).hexdigest()
            record["sha256"] = digest
            record["bytes"] = len(body)
            if digest in seen_hashes:
                record["decision"] = "duplicate_pdf"
                records.append(record)
                continue
            seen_hashes.add(digest)
            destination = source_dir / safe_name(response.url, index)
            destination.write_bytes(body)
            record["decision"] = "downloaded_pdf"
            record["local_file"] = destination.name
        except Exception as exc:
            record["decision"] = "download_failed"
            record["error"] = str(exc)
        records.append(record)
    (output / "download_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def index_pdfs(source_dir: Path, output: Path) -> dict[str, object]:
    render_dir = output / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, object]] = []
    rendered: list[Path] = []
    pdf_summaries: list[dict[str, object]] = []

    for pdf_index, pdf_path in enumerate(sorted(source_dir.glob("*.pdf")), start=1):
        document = fitz.open(pdf_path)
        page_records: list[dict[str, object]] = []
        matched_pages: list[int] = []
        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            text = normalize(page.get_text("text"))
            lower = text.lower()
            matches = [keyword for keyword in KEYWORDS if keyword in lower]
            record = {
                "pdf": pdf_path.name,
                "page_number_1_based": page_number + 1,
                "matches": matches,
                "text_excerpt": text[:7000],
            }
            page_records.append(record)
            all_records.append(record)
            if matches:
                matched_pages.append(page_number)

        selected: set[int] = set()
        for page_number in matched_pages:
            selected.update(
                candidate
                for candidate in (page_number - 1, page_number, page_number + 1)
                if 0 <= candidate < document.page_count
            )
        ranked = sorted(
            selected,
            key=lambda number: (-len(page_records[number]["matches"]), number),
        )[:70]
        ranked.sort()
        for page_number in ranked:
            page = document.load_page(page_number)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.1, 2.1), alpha=False)
            destination = render_dir / f"pdf_{pdf_index:02d}_page_{page_number + 1:04d}.png"
            pixmap.save(destination)
            rendered.append(destination)
        pdf_summaries.append(
            {
                "pdf": pdf_path.name,
                "page_count": document.page_count,
                "matched_page_count": len(matched_pages),
                "rendered_pages_1_based": [number + 1 for number in ranked],
            }
        )
        document.close()

    (output / "pdf_page_index.json").write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    (output / "pdf_summaries.json").write_text(json.dumps(pdf_summaries, indent=2), encoding="utf-8")
    make_contact_sheet(rendered, output / "contact_sheet.jpg")
    return {
        "pdf_count": len(pdf_summaries),
        "pdf_summaries": pdf_summaries,
        "rendered_page_count": len(rendered),
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output = repo_root / "artifacts" / "consolidated_iron_asbuilt"
    source_dir = Path("/tmp/consolidated_iron_pdfs")
    output.mkdir(parents=True, exist_ok=True)

    discovery = asyncio.run(discover_dynamic_documents(output))
    urls = list(discovery["discovered_urls"])
    downloads = download_candidates(urls, source_dir, output)

    # Follow nested direct PDF URLs found in document landing pages.
    nested_urls: set[str] = set()
    for record in downloads:
        nested_urls.update(record.get("nested_pdf_urls", []))
    if nested_urls:
        second = download_candidates(sorted(nested_urls), source_dir, output / "nested")
        downloads.extend(second)

    indexed = index_pdfs(source_dir, output)
    report = {
        "status": "CONSOLIDATED_IRON_DYNAMIC_COLLECTION_EXTRACTED_MANUAL_REVIEW_REQUIRED",
        "site_name": "Consolidated Iron and Metal",
        "site_id": SITE_ID,
        "epa_id": EPA_ID,
        "discovery": discovery,
        "download_record_count": len(downloads),
        "indexed": indexed,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_MEASURED_DEPTH_GEOMETRY_UNCERTAINTY_AND_STABILITY_REVIEW",
    }
    (output / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# Consolidated Iron and Metal evidence extraction\n\n"
        "Review network records, discovered document URLs, PDF indexes, rendered pages, and the contact sheet. "
        "The acceptance gates are: actual final surface-to-geotextile depths by location; exact surveyed shallow "
        "and deep boundaries; supported horizontal/vertical uncertainty; identical final topsoil/vegetation; at "
        "least one clean 20 m interior in each zone; and a stable post-remedy observation period. No Earth Engine "
        "query or calibration record is authorized by this extraction.\n",
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
