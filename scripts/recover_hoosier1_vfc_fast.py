"""Fast recovery of public Hoosier #1 closure records from IDEM VFC.

The VFC query for SW Program ID 43-01 returns hundreds of records. This pass
extracts the actual result rows, prioritizes the 1994-1996 and 2008-2011 closure
windows, reads metadata for the most relevant permits/reports/drawings/surveys,
and downloads only high-ranked public PDFs. It does not call Earth Engine,
create calibration rows, train a model, or enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlencode, urljoin, urlparse, urlunparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE = "https://ecm.idem.in.gov/cs/idcplg"
PROGRAM_ID = "43-01"
RESULT_COUNT = 100
MAX_PAGES = 10
MAX_METADATA = 180
MAX_DOWNLOADS = 60
MAX_BYTES = 350 * 1024 * 1024

QUERY_TEXT = f"xSWProgramID <contains> `{PROGRAM_ID}`"
SEARCH_PARAMS = {
    "IdcService": "GET_SEARCH_RESULTS",
    "SortField": "dInDate",
    "SortOrder": "Asc",
    "ResultCount": str(RESULT_COUNT),
    "QueryText": QUERY_TEXT,
    "SearchQueryFormat": "UNIVERSAL",
    "searchFormType": "standard",
    "listTemplateId": "SearchResultsIDEM",
    "SearchProviders": "WCC_IDEM",
}

TARGET_WINDOWS = (
    (datetime(1994, 1, 1), datetime(1996, 12, 31)),
    (datetime(2008, 1, 1), datetime(2011, 12, 31)),
)
TARGET_DATES = (datetime(1995, 9, 1), datetime(2010, 12, 2))

TYPE_WEIGHTS = {
    "drawing": 130,
    "map": 90,
    "olq permit": 120,
    "olq report": 115,
    "technical review": 120,
    "correspondence": 70,
    "olq authorization": 80,
    "olq field inspections": 30,
    "olq monitoring": 15,
    "olq financial assurance": 5,
}

TEXT_WEIGHTS = {
    "closure certification": 250,
    "final closure certification": 260,
    "closure construction certification": 260,
    "construction quality assurance": 220,
    "quality assurance": 140,
    "cqa": 120,
    "as-built": 220,
    "as built": 220,
    "final cover": 190,
    "composite final cover": 210,
    "soil final cover": 200,
    "closure approval": 190,
    "final closure": 180,
    "completion report": 170,
    "completion document": 160,
    "construction certification": 190,
    "final construction": 160,
    "survey": 130,
    "drawing": 90,
    "closure": 70,
    "cover": 45,
    "hoosier #1": 60,
    "hoosier 1": 60,
    "43-01": 40,
}


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def search_url() -> str:
    return f"{BASE}?{urlencode(SEARCH_PARAMS, quote_via=quote_plus)}"


def strip_fragment(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment=""))


def normalize(base_url: str, value: str) -> str:
    return strip_fragment(urljoin(base_url, value.replace("&amp;", "&")))


def parse_date(value: str) -> datetime | None:
    match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%m/%d/%Y")
    except ValueError:
        return None


def in_target_window(value: datetime | None) -> bool:
    return bool(value and any(start <= value <= end for start, end in TARGET_WINDOWS))


def date_score(value: datetime | None) -> int:
    if value is None:
        return 0
    score = 100 if in_target_window(value) else 0
    distance = min(abs((value - target).days) for target in TARGET_DATES)
    if distance <= 31:
        score += 120
    elif distance <= 120:
        score += 80
    elif distance <= 365:
        score += 40
    return score


def row_score(record: dict[str, object]) -> int:
    doc_type = str(record.get("document_type", "")).lower()
    score = sum(weight for token, weight in TYPE_WEIGHTS.items() if token in doc_type)
    date = None
    if record.get("document_date"):
        try:
            date = datetime.strptime(str(record["document_date"]), "%Y-%m-%d")
        except ValueError:
            pass
    return score + date_score(date)


def text_score(value: str) -> int:
    lower = value.lower()
    return sum(weight for token, weight in TEXT_WEIGHTS.items() if token in lower)


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
        cells = item.get("cells", [])
        if len(cells) < 6:
            continue
        content_id = clean(str(cells[0]))
        date = parse_date(str(cells[1]))
        program = clean(str(cells[2]))
        document_type = clean(str(cells[3]))
        security_group = clean(str(cells[4]))
        file_size = clean(str(cells[5]))
        file_url = None
        info_url = None
        for link in item.get("links", []):
            href = normalize(page.url, str(link.get("href", "")))
            if "GET_FILE" in href.upper() and file_url is None:
                file_url = href
            if "DOC_INFO" in href.upper() and info_url is None:
                info_url = href
        result.append(
            {
                "content_id": content_id,
                "document_date": date.strftime("%Y-%m-%d") if date else None,
                "program": program,
                "document_type": document_type,
                "security_group": security_group,
                "file_size": file_size,
                "file_url": file_url,
                "doc_info_url": info_url,
            }
        )
    return result


def pagination_links(page) -> list[str]:
    values = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
          .filter(href => /GET_SEARCH_RESULTS/i.test(href) && /PageNumber=/i.test(href))"""
    )
    return sorted({normalize(page.url, value) for value in values})


def info_snapshot(page, url: str) -> dict[str, object]:
    body = clean(page.locator("body").inner_text(timeout=20000))
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
        "title": clean(page.title()),
        "body_text": body[:180000],
        "fields": fields,
        "file_links": [normalize(url, item) for item in file_links],
    }


def download(context, url: str, destination: Path) -> dict[str, object]:
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
    record.update({"sha256": hashlib.sha256(body).hexdigest(), "saved_path": str(path)})
    return record


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "hoosier1_vfc_fast"
    output.mkdir(parents=True, exist_ok=True)
    downloads_dir = output / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "program_id": PROGRAM_ID,
        "search_url": search_url(),
        "pages": [],
        "records": [],
        "metadata_records": [],
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
        page.goto(search_url(), wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        queue = [strip_fragment(page.url), *pagination_links(page)]
        seen: set[str] = set()
        records_by_id: dict[str, dict[str, object]] = {}
        while queue and len(seen) < MAX_PAGES:
            url = strip_fragment(queue.pop(0))
            if url in seen:
                continue
            seen.add(url)
            if strip_fragment(page.url) != url:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(2500)
            rows = extract_rows(page)
            links = pagination_links(page)
            for link in links:
                if link not in seen and link not in queue:
                    queue.append(link)
            report["pages"].append(
                {
                    "url": page.url,
                    "row_count": len(rows),
                    "pagination_link_count": len(links),
                    "body_preview": clean(page.locator("body").inner_text(timeout=15000))[:2500],
                }
            )
            for record in rows:
                record["row_score"] = row_score(record)
                records_by_id[str(record["content_id"])] = record

        records = sorted(records_by_id.values(), key=lambda item: (-int(item["row_score"]), str(item["content_id"])))
        report["records"] = records
        (output / "all_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

        # Metadata pass only for target-era, higher-value document classes.
        candidates = [
            item for item in records
            if in_target_window(datetime.strptime(str(item["document_date"]), "%Y-%m-%d"))
            and any(token in str(item["document_type"]).lower() for token in TYPE_WEIGHTS)
        ]
        candidates = candidates[:MAX_METADATA]
        info_page = context.new_page()
        enriched: list[dict[str, object]] = []
        for record in candidates:
            item = dict(record)
            metadata: dict[str, object] = {}
            url = item.get("doc_info_url")
            if url:
                try:
                    info_page.goto(str(url), wait_until="domcontentloaded", timeout=90000)
                    info_page.wait_for_timeout(700)
                    metadata = info_snapshot(info_page, str(url))
                except Exception as exc:
                    metadata = {"url": url, "error": repr(exc), "title": "", "body_text": "", "fields": {}, "file_links": []}
            combined = " ".join(
                [
                    str(item.get("content_id", "")),
                    str(item.get("document_type", "")),
                    str(metadata.get("title", "")),
                    str(metadata.get("body_text", "")),
                    json.dumps(metadata.get("fields", {}), sort_keys=True),
                ]
            )
            item["metadata"] = metadata
            item["score"] = int(item["row_score"]) + text_score(combined)
            file_urls: list[str] = []
            for candidate_url in [item.get("file_url"), *(metadata.get("file_links", []) if isinstance(metadata, dict) else [])]:
                if candidate_url and candidate_url not in file_urls:
                    file_urls.append(str(candidate_url))
            item["candidate_file_urls"] = file_urls
            enriched.append(item)

        enriched.sort(key=lambda item: (-int(item["score"]), str(item["content_id"])))
        report["metadata_records"] = enriched
        (output / "ranked_records.json").write_text(json.dumps(enriched, indent=2), encoding="utf-8")

        hashes: set[str] = set()
        for index, record in enumerate(enriched[:MAX_DOWNLOADS], start=1):
            attempts: list[dict[str, object]] = []
            selected: dict[str, object] | None = None
            for candidate_index, url in enumerate(record.get("candidate_file_urls", [])[:5], start=1):
                try:
                    result = download(
                        context,
                        str(url),
                        downloads_dir / f"{index:03d}_{candidate_index:02d}_{record['content_id']}_{safe_name(str(record['document_type']))}",
                    )
                    attempts.append(result)
                    digest = str(result.get("sha256", ""))
                    if result.get("is_pdf") and digest and digest not in hashes:
                        hashes.add(digest)
                        selected = result
                        break
                except Exception as exc:
                    attempts.append({"url": url, "error": repr(exc)})
            report["download_attempts"].append(
                {
                    "content_id": record.get("content_id"),
                    "document_date": record.get("document_date"),
                    "document_type": record.get("document_type"),
                    "score": record.get("score"),
                    "metadata": record.get("metadata"),
                    "attempts": attempts,
                    "selected_pdf": selected,
                }
            )

        info_page.close()
        browser.close()

    pdf_count = sum(bool(item.get("selected_pdf")) for item in report["download_attempts"])
    report["page_count"] = len(report["pages"])
    report["record_count"] = len(report["records"])
    report["metadata_record_count"] = len(report["metadata_records"])
    report["recovered_pdf_count"] = pdf_count
    report["status"] = "RECOVERED" if pdf_count else "NO_PUBLIC_PDF_RECOVERED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
