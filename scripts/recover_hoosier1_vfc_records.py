"""Recover public IDEM VFC closure records for Hoosier #1 Landfill.

The search is limited to SW Program ID 43-01 and public environmental closure
records: final-cover plans, closure certifications, CQA reports, drawings,
as-built surveys, approvals, and post-closure records. It does not call Earth
Engine, create calibration rows, train a model, or enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlencode, urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE = "https://ecm.idem.in.gov/cs/idcplg"
PROGRAM_ID = "43-01"
RESULT_COUNT = 100
MAX_RESULT_PAGES = 25
MAX_METADATA_RECORDS = 250
MAX_DOWNLOADS = 60
MAX_BYTES = 350 * 1024 * 1024

QUERY_TEXT = f"xSWProgramID <contains> `{PROGRAM_ID}`"
SEARCH_PARAMS = {
    "IdcService": "GET_SEARCH_RESULTS",
    "SortField": "dInDate",
    "SortOrder": "Asc",
    "ResultCount": str(RESULT_COUNT),
    "QueryText": QUERY_TEXT,
    "listTemplateId": "",
    "ftx": "",
    "SearchQueryFormat": "UNIVERSAL",
    "TargetedQuickSearchSelection": "n",
    "MiniSearchText": PROGRAM_ID,
}

RELEVANCE_WEIGHTS = {
    "closure certification": 180,
    "closure construction certification": 180,
    "final closure certification": 180,
    "construction quality assurance": 150,
    "quality assurance": 100,
    "cqa": 90,
    "as-built": 150,
    "as built": 150,
    "final cover": 130,
    "composite final cover": 140,
    "soil final cover": 130,
    "closure approval": 120,
    "completion report": 110,
    "completion document": 100,
    "final construction": 110,
    "construction certification": 120,
    "survey": 90,
    "drawing": 80,
    "plan": 45,
    "closure": 45,
    "post-closure": 25,
    "post closure": 25,
    "43-01": 15,
    "hoosier": 15,
}

TYPE_WEIGHTS = {
    "completion document": 110,
    "certification": 105,
    "drawing": 90,
    "survey": 95,
    "olq permit": 65,
    "olq report": 65,
    "technical review": 55,
    "approval": 75,
    "plan": 50,
    "report": 40,
}

TARGET_DATE_RANGES = (
    (datetime(1994, 1, 1), datetime(1996, 12, 31)),
    (datetime(2008, 1, 1), datetime(2011, 12, 31)),
)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def build_search_url(extra: dict[str, str] | None = None) -> str:
    params = dict(SEARCH_PARAMS)
    if extra:
        params.update(extra)
    return f"{BASE}?{urlencode(params, quote_via=quote_plus)}"


def parse_date(text: str) -> datetime | None:
    for pattern in (r"\b(\d{1,2}/\d{1,2}/\d{4})\b", r"\b(\d{4}-\d{2}-\d{2})\b"):
        match = re.search(pattern, text)
        if not match:
            continue
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                pass
    return None


def in_target_date_range(date: datetime | None) -> bool:
    if date is None:
        return False
    return any(start <= date <= end for start, end in TARGET_DATE_RANGES)


def score_text(text: str, document_type: str = "", document_date: datetime | None = None) -> int:
    lower = text.lower()
    score = sum(weight for token, weight in RELEVANCE_WEIGHTS.items() if token in lower)
    type_lower = document_type.lower()
    score += sum(weight for token, weight in TYPE_WEIGHTS.items() if token in type_lower)
    if in_target_date_range(document_date):
        score += 90
    if PROGRAM_ID in text:
        score += 20
    return score


def extract_result_rows(page_url: str, html: str) -> list[dict[str, object]]:
    # Use a tiny browser DOM in the caller instead of fragile HTML regex.
    raise RuntimeError("extract_result_rows must be evaluated in the browser")


def browser_rows(page) -> list[dict[str, object]]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('table tr')).map(row => {
          const text = (row.innerText || '').replace(/\s+/g, ' ').trim();
          const links = Array.from(row.querySelectorAll('a')).map(a => ({
            text: (a.innerText || '').replace(/\s+/g, ' ').trim(),
            href: a.href || a.getAttribute('href') || '',
            onclick: a.getAttribute('onclick') || ''
          }));
          return {text, links};
        }).filter(row => row.text && row.links.some(link => /DOC_INFO|GET_FILE/i.test((link.href || '') + ' ' + (link.onclick || ''))))"""
    )


def browser_page_links(page) -> list[str]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]'))
          .map(a => a.href)
          .filter(href => /GET_SEARCH_RESULTS/i.test(href) && /PageNumber=|StartRow=/i.test(href))"""
    )


def normalize_link(base_url: str, link: str) -> str:
    return urljoin(base_url, link.replace("&amp;", "&"))


def ids_from_url(url: str) -> tuple[str | None, str | None]:
    query = parse_qs(urlparse(url).query)
    did = (query.get("dID") or [None])[0]
    doc_name = (query.get("dDocName") or [None])[0]
    return did, doc_name


def derive_file_urls(doc_info_url: str) -> list[str]:
    did, doc_name = ids_from_url(doc_info_url)
    if not did or not doc_name:
        return []
    common = {
        "IdcService": "GET_FILE",
        "dID": did,
        "dDocName": doc_name,
        "allowInterrupt": "1",
        "noSaveAs": "1",
    }
    return [
        f"{BASE}?{urlencode({**common, 'Rendition': rendition})}"
        for rendition in ("web", "Primary", "primary")
    ] + [f"{BASE}?{urlencode(common)}"]


def page_metadata_text(page) -> str:
    return clean(page.locator("body").inner_text(timeout=20000))


def metadata_from_page(page, url: str) -> dict[str, object]:
    body = page_metadata_text(page)
    title = clean(page.title())
    fields = page.evaluate(
        """() => {
          const out = {};
          for (const row of document.querySelectorAll('tr')) {
            const cells = Array.from(row.querySelectorAll('th,td')).map(c => (c.innerText || '').replace(/\s+/g, ' ').trim());
            if (cells.length >= 2 && cells[0] && cells[1]) out[cells[0]] = cells.slice(1).join(' | ');
          }
          for (const el of document.querySelectorAll('input,textarea,select')) {
            const key = el.name || el.id;
            if (key && el.value) out[key] = el.value;
          }
          return out;
        }"""
    )
    file_links = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(href => /GET_FILE/i.test(href))"""
    )
    return {
        "url": url,
        "title": title,
        "body_text": body[:160000],
        "fields": fields,
        "file_links": file_links,
    }


def download_response(context, url: str, destination: Path) -> dict[str, object]:
    response = context.request.get(
        url,
        headers={"Referer": BASE, "Accept": "application/pdf,text/html,*/*"},
        timeout=180000,
        fail_on_status_code=False,
    )
    body = response.body()
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
    record: dict[str, object] = {
        "url": response.url,
        "status": response.status,
        "content_type": content_type,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
    }
    if len(body) > MAX_BYTES:
        record["skipped"] = "size_limit"
        return record
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(body)
    record.update(
        {
            "sha256": hashlib.sha256(body).hexdigest(),
            "saved_path": str(path),
        }
    )
    return record


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "hoosier1_vfc"
    output.mkdir(parents=True, exist_ok=True)
    downloads_dir = output / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "program_id": PROGRAM_ID,
        "search_url": build_search_url(),
        "result_pages": [],
        "records": [],
        "ranked_records": [],
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
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            accept_downloads=True,
        )
        page = context.new_page()

        first_url = build_search_url()
        page.goto(first_url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except PlaywrightTimeoutError:
            pass
        page.screenshot(path=str(output / "search_results_page_1.png"), full_page=True)
        (output / "search_results_page_1.html").write_text(page.content(), encoding="utf-8")

        queued: list[str] = [page.url]
        queued.extend(normalize_link(page.url, url) for url in browser_page_links(page))
        seen_pages: set[str] = set()
        raw_records: dict[str, dict[str, object]] = {}

        while queued and len(seen_pages) < MAX_RESULT_PAGES:
            url = queued.pop(0)
            if url in seen_pages:
                continue
            seen_pages.add(url)
            if page.url != url:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(2500)
            rows = browser_rows(page)
            page_links = [normalize_link(page.url, item) for item in browser_page_links(page)]
            for next_url in page_links:
                if next_url not in seen_pages and next_url not in queued:
                    queued.append(next_url)
            report["result_pages"].append(
                {
                    "url": page.url,
                    "row_count": len(rows),
                    "pagination_link_count": len(page_links),
                    "body_preview": clean(page.locator("body").inner_text(timeout=15000))[:5000],
                }
            )
            for row in rows:
                text = clean(str(row.get("text", "")))
                if PROGRAM_ID not in text and "hoosier" not in text.lower():
                    continue
                links = row.get("links", [])
                doc_info_url = None
                direct_file_urls: list[str] = []
                for link in links:
                    href = normalize_link(page.url, str(link.get("href", "")))
                    if "DOC_INFO" in href.upper():
                        doc_info_url = href
                    if "GET_FILE" in href.upper():
                        direct_file_urls.append(href)
                identity = doc_info_url or (direct_file_urls[0] if direct_file_urls else text)
                doc_date = parse_date(text)
                raw_records[identity] = {
                    "row_text": text,
                    "document_date": doc_date.strftime("%Y-%m-%d") if doc_date else None,
                    "doc_info_url": doc_info_url,
                    "direct_file_urls": direct_file_urls,
                    "row_score": score_text(text, document_date=doc_date),
                }

        records = list(raw_records.values())
        records.sort(key=lambda item: (-int(item["row_score"]), str(item["row_text"])))
        report["records"] = records

        metadata_page = context.new_page()
        enriched: list[dict[str, object]] = []
        for record in records[:MAX_METADATA_RECORDS]:
            item = dict(record)
            doc_info_url = item.get("doc_info_url")
            metadata: dict[str, object] = {}
            if doc_info_url:
                try:
                    metadata_page.goto(str(doc_info_url), wait_until="domcontentloaded", timeout=90000)
                    metadata_page.wait_for_timeout(1000)
                    metadata = metadata_from_page(metadata_page, str(doc_info_url))
                except Exception as exc:
                    metadata = {"url": doc_info_url, "error": repr(exc), "body_text": "", "fields": {}, "file_links": []}
            combined = " ".join(
                [
                    str(item.get("row_text", "")),
                    str(metadata.get("title", "")),
                    str(metadata.get("body_text", "")),
                    json.dumps(metadata.get("fields", {}), sort_keys=True),
                ]
            )
            document_type = ""
            for key, value in (metadata.get("fields") or {}).items():
                if "type" in str(key).lower():
                    document_type += f" {value}"
            doc_date = None
            if item.get("document_date"):
                try:
                    doc_date = datetime.strptime(str(item["document_date"]), "%Y-%m-%d")
                except ValueError:
                    pass
            item["metadata"] = metadata
            item["document_type"] = clean(document_type)
            item["score"] = score_text(combined, document_type=document_type, document_date=doc_date)
            file_urls: list[str] = []
            for url in item.get("direct_file_urls", []):
                if url not in file_urls:
                    file_urls.append(url)
            for url in metadata.get("file_links", []) if isinstance(metadata, dict) else []:
                normalized = normalize_link(str(doc_info_url or BASE), str(url))
                if normalized not in file_urls:
                    file_urls.append(normalized)
            if doc_info_url:
                for url in derive_file_urls(str(doc_info_url)):
                    if url not in file_urls:
                        file_urls.append(url)
            item["candidate_file_urls"] = file_urls
            enriched.append(item)

        enriched.sort(key=lambda item: (-int(item["score"]), str(item["row_text"])))
        report["ranked_records"] = enriched
        (output / "ranked_records.json").write_text(json.dumps(enriched, indent=2), encoding="utf-8")

        downloaded_hashes: set[str] = set()
        for index, record in enumerate(enriched[:MAX_DOWNLOADS], start=1):
            attempts: list[dict[str, object]] = []
            selected_pdf: dict[str, object] | None = None
            for candidate_index, url in enumerate(record.get("candidate_file_urls", [])[:8], start=1):
                try:
                    result = download_response(
                        context,
                        str(url),
                        downloads_dir / f"{index:03d}_{candidate_index:02d}_{safe_name(str(record.get('row_text', 'document')))}",
                    )
                    attempts.append(result)
                    digest = str(result.get("sha256", ""))
                    if result.get("is_pdf") and digest and digest not in downloaded_hashes:
                        downloaded_hashes.add(digest)
                        selected_pdf = result
                        break
                except Exception as exc:
                    attempts.append({"url": url, "error": repr(exc)})
            report["download_attempts"].append(
                {
                    "score": record.get("score"),
                    "row_text": record.get("row_text"),
                    "document_date": record.get("document_date"),
                    "document_type": record.get("document_type"),
                    "doc_info_url": record.get("doc_info_url"),
                    "attempts": attempts,
                    "selected_pdf": selected_pdf,
                }
            )

        metadata_page.close()
        browser.close()

    pdf_count = sum(bool(item.get("selected_pdf")) for item in report["download_attempts"])
    report["result_page_count"] = len(report["result_pages"])
    report["record_count"] = len(report["records"])
    report["recovered_pdf_count"] = pdf_count
    report["status"] = "RECOVERED" if pdf_count else "NO_PUBLIC_PDF_RECOVERED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
