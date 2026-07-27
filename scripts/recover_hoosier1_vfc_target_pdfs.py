"""Directly recover target-window Hoosier #1 public PDFs from IDEM VFC.

This bounded pass avoids metadata-page latency. It queries closure-relevant
VFC document types for SW Program ID 43-01, keeps records dated 1994-1996 or
2008-2011, and downloads their public web PDF renditions. It does not call
Earth Engine, create calibration rows, train a model, or enable app depth.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlencode, urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE = "https://ecm.idem.in.gov/cs/idcplg"
PROGRAM_ID = "43-01"
DOCUMENT_TYPES = (
    "Drawing",
    "Map",
    "OLQ Permit",
    "OLQ Report",
    "Technical Review",
    "Correspondence",
    "OLQ Authorization",
)
TARGET_WINDOWS = (
    (datetime(1994, 1, 1), datetime(1996, 12, 31)),
    (datetime(2008, 1, 1), datetime(2011, 12, 31)),
)
MAX_DOWNLOADS = 140
MAX_BYTES = 400 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:100] or "document")


def query_url(document_type: str) -> str:
    params = {
        "IdcService": "GET_SEARCH_RESULTS",
        "QueryText": f"xSWProgramID <contains> `{PROGRAM_ID}`",
        "QueryFilter": f"xIDEMDocumentType <Matches> `{document_type}`",
        "FilterFields": "xIDEMDocumentType",
        "SortField": "xDocumentDate",
        "SortOrder": "Asc",
        "ResultCount": "100",
        "SearchQueryFormat": "UNIVERSAL",
        "searchFormType": "standard",
        "listTemplateId": "SearchResultsIDEM",
        "SearchProviders": "WCC_IDEM",
        "PageNumber": "1",
        "StartRow": "1",
        "EndRow": "100",
    }
    return f"{BASE}?{urlencode(params, quote_via=quote_plus)}"


def parse_date(value: str) -> datetime | None:
    match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%m/%d/%Y")
    except ValueError:
        return None


def in_window(value: datetime | None) -> bool:
    return bool(value and any(start <= value <= end for start, end in TARGET_WINDOWS))


def extract_rows(page) -> list[dict[str, object]]:
    raw = page.evaluate(
        """() => Array.from(document.querySelectorAll('table tr')).map(row => {
          const cells = Array.from(row.querySelectorAll('td.xuiListContentCell_Odd, td.xuiListContentCell_Even'))
            .map(cell => (cell.innerText || '').replace(/\s+/g, ' ').trim());
          const links = Array.from(row.querySelectorAll('a[href]')).map(a => ({
            text: (a.innerText || '').replace(/\s+/g, ' ').trim(),
            href: a.href || a.getAttribute('href') || ''
          }));
          return {cells, links};
        }).filter(item => item.cells.length >= 6 && item.links.some(link => /GET_FILE/i.test(link.href)))"""
    )
    result: list[dict[str, object]] = []
    for item in raw:
        cells = item["cells"]
        date = parse_date(str(cells[1]))
        file_url = None
        info_url = None
        for link in item.get("links", []):
            href = urljoin(page.url, str(link.get("href", "")).replace("&amp;", "&"))
            if "GET_FILE" in href.upper() and file_url is None:
                file_url = href
            if "DOC_INFO" in href.upper() and info_url is None:
                info_url = href
        result.append(
            {
                "content_id": clean(str(cells[0])),
                "document_date": date.strftime("%Y-%m-%d") if date else None,
                "program": clean(str(cells[2])),
                "document_type": clean(str(cells[3])),
                "security_group": clean(str(cells[4])),
                "file_size": clean(str(cells[5])),
                "file_url": file_url,
                "doc_info_url": info_url,
            }
        )
    return result


def download(context, record: dict[str, object], destination: Path) -> dict[str, object]:
    response = context.request.get(
        str(record["file_url"]),
        headers={"Referer": BASE, "Accept": "application/pdf,text/html,*/*"},
        timeout=180000,
        fail_on_status_code=False,
    )
    body = response.body()
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
    item: dict[str, object] = {
        **record,
        "response_url": response.url,
        "status": response.status,
        "content_type": content_type,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
    }
    if len(body) > MAX_BYTES:
        item["skipped"] = "size_limit"
        return item
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(body)
    item.update({"saved_path": str(path), "sha256": hashlib.sha256(body).hexdigest()})
    return item


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "hoosier1_vfc_target_pdfs"
    output.mkdir(parents=True, exist_ok=True)
    downloads = output / "downloads"
    downloads.mkdir(exist_ok=True)
    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "queries": [],
        "target_records": [],
        "downloads": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36")
        page = context.new_page()
        records_by_id: dict[str, dict[str, object]] = {}
        for document_type in DOCUMENT_TYPES:
            url = query_url(document_type)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(3000)
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except PlaywrightTimeoutError:
                    pass
                rows = extract_rows(page)
                report["queries"].append({
                    "document_type": document_type,
                    "url": page.url,
                    "row_count": len(rows),
                    "body_preview": clean(page.locator("body").inner_text(timeout=15000))[:2500],
                })
                for record in rows:
                    date = datetime.strptime(str(record["document_date"]), "%Y-%m-%d") if record.get("document_date") else None
                    if in_window(date) and record.get("file_url"):
                        records_by_id[str(record["content_id"])] = record
            except Exception as exc:
                report["queries"].append({"document_type": document_type, "url": url, "error": repr(exc)})
        target_records = sorted(records_by_id.values(), key=lambda r: (str(r.get("document_date")), str(r.get("document_type")), str(r.get("content_id"))))
        report["target_records"] = target_records
        (output / "target_records.json").write_text(json.dumps(target_records, indent=2), encoding="utf-8")

        hashes: set[str] = set()
        for index, record in enumerate(target_records[:MAX_DOWNLOADS], start=1):
            try:
                item = download(
                    context,
                    record,
                    downloads / f"{index:03d}_{record['document_date']}_{record['content_id']}_{safe_name(str(record['document_type']))}",
                )
                digest = str(item.get("sha256", ""))
                if item.get("is_pdf") and digest and digest in hashes:
                    item["duplicate"] = True
                elif item.get("is_pdf") and digest:
                    hashes.add(digest)
                report["downloads"].append(item)
            except Exception as exc:
                report["downloads"].append({**record, "error": repr(exc)})
        browser.close()

    pdfs = sum(bool(item.get("is_pdf")) for item in report["downloads"])
    report["target_record_count"] = len(report["target_records"])
    report["recovered_pdf_count"] = pdfs
    report["status"] = "RECOVERED" if pdfs else "NO_PUBLIC_PDF_RECOVERED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
