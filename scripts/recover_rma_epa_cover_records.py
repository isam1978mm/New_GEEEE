"""Recover public EPA records for the RMA integrated soil-cover system.

This temporary evidence tool searches only environmental cover documents:
long-term care plans, cover designs, construction completion reports, and
as-built surveys. It does not call Earth Engine, create calibration rows,
train a model, or enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

PAGE_URL = (
    "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?"
    "colid=70067&doc=Y&fuseaction=second.scs&id=0800357&region=08&type=SC"
)
SEARCH_TERMS = (
    "RCRA-Equivalent, 2-, and 3-Foot Covers Long-Term Care Plan",
    "Integrated Cover System Long-Term Care Plan",
    "South Plants Balance of Areas",
    "100 Percent Design Package",
    "cover construction completion",
    "cover as-built",
    "cover as built",
)
ROW_SCRIPT = """
() => ({
  url: location.href,
  title: document.title,
  inputs: Array.from(document.querySelectorAll('.dataTables_filter input, input[type="search"], input[aria-controls]')).map((el, i) => ({index: i, placeholder: el.placeholder || '', aria: el.getAttribute('aria-controls') || ''})),
  rows: Array.from(document.querySelectorAll('table tbody tr, table tr')).slice(0, 2500).map(row => ({
    text: (row.innerText || '').replace(/\\s+/g, ' ').trim(),
    links: Array.from(row.querySelectorAll('a')).map(a => ({
      text: (a.innerText || '').replace(/\\s+/g, ' ').trim(),
      href: a.href || a.getAttribute('href') || '',
      onclick: a.getAttribute('onclick') || ''
    }))
  })).filter(row => row.text)
})
"""


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def row_matches(text: str, term: str) -> bool:
    lower = text.lower()
    needle = term.lower()
    if needle in lower:
        return True
    tokens = [token for token in re.split(r"[^a-z0-9]+", needle) if len(token) >= 3]
    return bool(tokens) and sum(token in lower for token in tokens) >= max(2, len(tokens) // 2)


def urls_from_link(base_url: str, link: dict[str, str]) -> list[str]:
    combined = f"{link.get('href', '')} {link.get('onclick', '')}"
    values: list[str] = []
    href = link.get("href", "")
    if href:
        values.append(urljoin(base_url, href))
    for pattern in (
        r"https?://[^\s'\"<>]+",
        r"['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]",
        r"(?:window\.)?open\(['\"]([^'\"]+)",
        r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)",
    ):
        for match in re.finditer(pattern, combined, re.I):
            value = match.group(1) if match.lastindex else match.group(0)
            values.append(urljoin(base_url, value))
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def save_response(response, destination: Path) -> dict[str, object]:
    body = response.body()
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(body)
    return {
        "url": response.url,
        "status": response.status,
        "content_type": content_type,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
        "sha256": hashlib.sha256(body).hexdigest(),
        "saved_path": str(path),
    }


def snapshot(frame) -> dict[str, object]:
    try:
        return frame.evaluate(ROW_SCRIPT)
    except Exception as exc:
        return {"url": frame.url, "error": repr(exc), "inputs": [], "rows": []}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "rma_epa_cover_records"
    output.mkdir(parents=True, exist_ok=True)
    downloads = output / "downloads"
    downloads.mkdir(exist_ok=True)
    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "page_url": PAGE_URL,
        "search_terms": list(SEARCH_TERMS),
        "network_responses": [],
        "initial_snapshots": [],
        "search_results": [],
        "download_attempts": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
        )
        page = context.new_page()
        network: list[dict[str, object]] = []

        def on_response(response) -> None:
            content_type = response.headers.get("content-type", "").lower()
            url_lower = response.url.lower()
            if any(token in url_lower for token in ("doc", "ajax", "supercpad", "semspub", "siteprofile")) or "json" in content_type or "pdf" in content_type:
                network.append({"url": response.url, "status": response.status, "content_type": content_type})

        page.on("response", on_response)
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(12000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except PlaywrightTimeoutError:
            pass
        page.screenshot(path=str(output / "page.png"), full_page=True)
        (output / "page.html").write_text(page.content(), encoding="utf-8")

        initial = [snapshot(frame) for frame in page.frames]
        report["initial_snapshots"] = initial
        candidate_urls: list[str] = []
        seen_urls: set[str] = set()

        for term in SEARCH_TERMS:
            result: dict[str, object] = {"term": term, "attempts": [], "matches": []}
            for frame in page.frames:
                inputs = frame.locator('.dataTables_filter input, input[type="search"], input[aria-controls]')
                if inputs.count() == 0:
                    snap = snapshot(frame)
                    matches = [row for row in snap.get("rows", []) if row_matches(str(row.get("text", "")), term)]
                    if matches:
                        result["matches"].extend(matches)
                    continue
                for index in range(min(inputs.count(), 4)):
                    field = inputs.nth(index)
                    try:
                        field.fill(term, timeout=8000)
                        page.wait_for_timeout(1500)
                        snap = snapshot(frame)
                        matches = [row for row in snap.get("rows", []) if row_matches(str(row.get("text", "")), term)]
                        result["attempts"].append({"frame_url": frame.url, "input_index": index, "row_count": len(snap.get("rows", [])), "match_count": len(matches)})
                        result["matches"].extend(matches)
                        field.fill("", timeout=8000)
                        page.wait_for_timeout(500)
                    except Exception as exc:
                        result["attempts"].append({"frame_url": frame.url, "input_index": index, "error": repr(exc)})
            for row in result["matches"]:
                for link in row.get("links", []):
                    for url in urls_from_link(PAGE_URL, link):
                        if url not in seen_urls:
                            seen_urls.add(url)
                            candidate_urls.append(url)
            report["search_results"].append(result)

        for item in network:
            url = str(item.get("url", ""))
            ctype = str(item.get("content_type", "")).lower()
            if ("pdf" in ctype or url.lower().endswith(".pdf")) and url not in seen_urls:
                seen_urls.add(url)
                candidate_urls.append(url)

        report["network_responses"] = network
        (output / "candidate_urls.json").write_text(json.dumps(candidate_urls, indent=2), encoding="utf-8")
        for index, url in enumerate(candidate_urls[:60], start=1):
            try:
                response = context.request.get(
                    url,
                    headers={"Referer": PAGE_URL, "Accept": "application/pdf,text/html,*/*"},
                    timeout=120000,
                    fail_on_status_code=False,
                )
                report["download_attempts"].append(
                    save_response(response, downloads / f"{index:03d}_{safe_name(Path(urlparse(url).path).name or 'document')}")
                )
            except Exception as exc:
                report["download_attempts"].append({"url": url, "error": repr(exc)})
        browser.close()

    matched = sum(len(item.get("matches", [])) for item in report["search_results"])
    pdfs = sum(bool(item.get("is_pdf")) for item in report["download_attempts"])
    report["matched_row_count"] = matched
    report["recovered_pdf_count"] = pdfs
    report["status"] = "RECOVERED" if matched or pdfs else "NO_MATCHING_PUBLIC_RECORDS_FOUND"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
