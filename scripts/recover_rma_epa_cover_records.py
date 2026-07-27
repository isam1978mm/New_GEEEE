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

from bs4 import BeautifulSoup
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
OUTPUT_LIMIT_BYTES = 40 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def extract_urls(base_url: str, text: str) -> list[str]:
    urls: list[str] = []
    soup = BeautifulSoup(text, "html.parser")
    for tag, attr in (("a", "href"), ("iframe", "src"), ("embed", "src"), ("object", "data"), ("form", "action")):
        for element in soup.find_all(tag):
            value = element.get(attr)
            if value:
                urls.append(urljoin(base_url, value))
    for pattern in (
        r"https?://[^\s'\"<>]+",
        r"['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]",
        r"(?:window\.)?open\(['\"]([^'\"]+)",
        r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)",
    ):
        for match in re.finditer(pattern, text, re.I):
            value = match.group(1) if match.lastindex else match.group(0)
            urls.append(urljoin(base_url, value))
    result: list[str] = []
    seen: set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or url in seen:
            continue
        seen.add(url)
        result.append(url)
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


def frame_snapshot(frame) -> dict[str, object]:
    try:
        body_text = clean(frame.locator("body").inner_text(timeout=15000))
    except Exception:
        body_text = ""
    rows: list[dict[str, object]] = []
    for selector in ("table tbody tr", "table tr"):
        locator = frame.locator(selector)
        if locator.count() == 0:
            continue
        for index in range(min(locator.count(), 2000)):
            row = locator.nth(index)
            try:
                text = clean(row.inner_text(timeout=5000))
            except Exception:
                continue
            if not text:
                continue
            links: list[dict[str, str]] = []
            anchors = row.locator("a")
            for link_index in range(anchors.count()):
                anchor = anchors.nth(link_index)
                links.append(
                    {
                        "text": clean(anchor.inner_text(timeout=3000)),
                        "href": anchor.get_attribute("href") or "",
                        "onclick": anchor.get_attribute("onclick") or "",
                    }
                )
            rows.append({"text": text, "links": links})
        if rows:
            break
    return {"url": frame.url, "body_text": body_text[:200000], "rows": rows}


def matching_rows(snapshot: dict[str, object], term: str) -> list[dict[str, object]]:
    needle = term.lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", needle) if len(token) >= 3]
    results: list[dict[str, object]] = []
    for row in snapshot.get("rows", []):
        text = str(row.get("text", "")).lower()
        if needle in text or (tokens and sum(token in text for token in tokens) >= max(2, len(tokens) // 2)):
            results.append(row)
    return results


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "rma_epa_cover_records"
    output.mkdir(parents=True, exist_ok=True)
    network_dir = output / "network"
    downloads_dir = output / "downloads"
    network_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "page_url": PAGE_URL,
        "search_terms": list(SEARCH_TERMS),
        "network_responses": [],
        "frame_snapshots": [],
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
        captured: list[dict[str, object]] = []

        def on_response(response) -> None:
            url_lower = response.url.lower()
            content_type = response.headers.get("content-type", "").lower()
            relevant = any(token in url_lower for token in ("doc", "ajax", "supercpad", "semspub", "siteprofile"))
            relevant = relevant or "json" in content_type or "pdf" in content_type
            if not relevant or response.status >= 400:
                return
            try:
                body = response.body()
            except Exception:
                return
            if len(body) > OUTPUT_LIMIT_BYTES:
                captured.append({"url": response.url, "status": response.status, "content_type": content_type, "size_bytes": len(body), "skipped": "size_limit"})
                return
            suffix = ".pdf" if body.startswith(b"%PDF-") or "application/pdf" in content_type else ".json" if "json" in content_type else ".html"
            path = network_dir / f"{len(captured)+1:03d}_{safe_name(Path(urlparse(response.url).path).name or 'response')}{suffix}"
            path.write_bytes(body)
            captured.append({"url": response.url, "status": response.status, "content_type": content_type, "size_bytes": len(body), "saved_path": str(path)})

        page.on("response", on_response)
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(15000)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            pass

        initial_snapshots = [frame_snapshot(frame) for frame in page.frames]
        report["frame_snapshots"] = initial_snapshots
        (output / "page.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(output / "page.png"), full_page=True)

        search_inputs = []
        for frame in page.frames:
            for selector in (".dataTables_filter input", "input[type='search']", "input[aria-controls]"):
                locator = frame.locator(selector)
                for index in range(locator.count()):
                    search_inputs.append((frame, locator.nth(index), selector, index))

        for term in SEARCH_TERMS:
            term_result: dict[str, object] = {"term": term, "input_attempts": [], "matches": []}
            if search_inputs:
                for frame, input_locator, selector, index in search_inputs:
                    try:
                        input_locator.fill(term, timeout=10000)
                        page.wait_for_timeout(2500)
                        snapshot = frame_snapshot(frame)
                        matches = matching_rows(snapshot, term)
                        term_result["input_attempts"].append({"frame_url": frame.url, "selector": selector, "index": index, "row_count": len(snapshot.get("rows", [])), "match_count": len(matches)})
                        term_result["matches"].extend(matches)
                        input_locator.fill("", timeout=10000)
                        page.wait_for_timeout(1000)
                    except Exception as exc:
                        term_result["input_attempts"].append({"frame_url": frame.url, "selector": selector, "index": index, "error": repr(exc)})
            else:
                for snapshot in initial_snapshots:
                    term_result["matches"].extend(matching_rows(snapshot, term))
            report["search_results"].append(term_result)

        candidate_urls: list[str] = []
        seen_urls: set[str] = set()
        for term_result in report["search_results"]:
            for row in term_result.get("matches", []):
                for link in row.get("links", []):
                    combined = f"{link.get('href','')} {link.get('onclick','')}"
                    for url in extract_urls(PAGE_URL, combined):
                        if url not in seen_urls:
                            seen_urls.add(url)
                            candidate_urls.append(url)
        for item in captured:
            url = str(item.get("url", ""))
            if ("pdf" in str(item.get("content_type", "")).lower() or url.lower().endswith(".pdf")) and url not in seen_urls:
                seen_urls.add(url)
                candidate_urls.append(url)

        (output / "candidate_urls.json").write_text(json.dumps(candidate_urls, indent=2), encoding="utf-8")
        for index, url in enumerate(candidate_urls[:80], start=1):
            try:
                response = context.request.get(
                    url,
                    headers={"Referer": PAGE_URL, "Accept": "application/pdf,text/html,*/*"},
                    timeout=180000,
                    fail_on_status_code=False,
                )
                report["download_attempts"].append(save_response(response, downloads_dir / f"{index:03d}_{safe_name(Path(urlparse(url).path).name or 'document')}"))
            except Exception as exc:
                report["download_attempts"].append({"url": url, "error": repr(exc)})

        browser.close()
        report["network_responses"] = captured

    matched_rows = sum(len(item.get("matches", [])) for item in report["search_results"])
    pdf_count = sum(bool(item.get("is_pdf")) for item in report["download_attempts"])
    report["matched_row_count"] = matched_rows
    report["recovered_pdf_count"] = pdf_count
    report["status"] = "RECOVERED" if matched_rows or pdf_count else "NO_MATCHING_PUBLIC_RECORDS_FOUND"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
