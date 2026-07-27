"""Recover the 1993 Area B landfill closure certification and as-built records.

The search is limited to Ohio EPA public records for Cleveland/LTV Area B,
secondary ID ISWL018762, original PTI 02-5830, and the 1992-1995 closure period.
It does not call Earth Engine, create calibration rows, train a model, or enable
numeric depth output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

PORTAL = "https://edocpub.epa.ohio.gov/publicportal/"
SEARCH_BUTTON = "#ctl00_search_btnSearch"
PAGE_SIZE = "#ctl00_results_DocHitList_DocHitList_CurrentPageSize"
RESULT_LINK = "a[onclick*='ViewDocument.aspx?docid=']"

QUERIES = (
    {
        "name": "secondary_id",
        "secondary_id": "ISWL018762",
        "full_text": "",
        "permit": "",
        "entity": "",
        "date_from": "01/01/1992",
        "date_to": "12/31/1995",
    },
    {
        "name": "permit_number",
        "secondary_id": "",
        "full_text": "",
        "permit": "02-5830",
        "entity": "",
        "date_from": "01/01/1991",
        "date_to": "12/31/1995",
    },
    {
        "name": "area_b_closure",
        "secondary_id": "",
        "full_text": '"Area B" closure',
        "permit": "",
        "entity": "LTV STEEL",
        "date_from": "01/01/1992",
        "date_to": "12/31/1995",
    },
    {
        "name": "closure_certification",
        "secondary_id": "",
        "full_text": '"closure certification"',
        "permit": "",
        "entity": "LTV STEEL",
        "date_from": "01/01/1992",
        "date_to": "12/31/1995",
    },
)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180]


def wait_for_results(page) -> None:
    page.wait_for_timeout(2500)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_function(
        """() => document.body && (
          document.body.innerText.includes('Search returned') ||
          document.body.innerText.includes('No matching documents') ||
          document.querySelector("a[onclick*='ViewDocument.aspx?docid=']")
        )""",
        timeout=90000,
    )


def set_page_size(page) -> None:
    selector = page.locator(PAGE_SIZE)
    if selector.count() == 1 and selector.input_value() != "600":
        selector.select_option("600")
        page.wait_for_timeout(3500)


def extract_rows(page) -> list[dict[str, str]]:
    links = page.locator(RESULT_LINK)
    rows: list[dict[str, str]] = []
    for index in range(links.count()):
        link = links.nth(index)
        onclick = link.get_attribute("onclick") or ""
        match = re.search(r"ViewDocument\.aspx\?docid=(\d+)", onclick)
        if not match:
            continue
        docid = match.group(1)
        rows.append(
            {
                "docid": docid,
                "row_text": clean(link.inner_text()),
                "view_url": f"{PORTAL}ViewDocument.aspx?docid={docid}",
            }
        )
    return rows


def run_query(page, query: dict[str, str]) -> list[dict[str, str]]:
    page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2000)
    page.locator("#ctl00_search_KeywordPanel1_txtFrom").fill(query["date_from"])
    page.locator("#ctl00_search_KeywordPanel1_txtTo").fill(query["date_to"])
    page.locator("#ctl00_search_KeywordPanel1_txtValue_-1_1_111_1").fill(query["secondary_id"])
    page.locator("#ctl00_search_KeywordPanel1_txtValue_-1_1_121_1").fill(query["permit"])
    page.locator("#ctl00_search_KeywordPanel1_txtValue_-1_1_106_1").fill(query["entity"])
    page.locator("#ctl00_search_txtFullText").fill(query["full_text"])
    page.locator(SEARCH_BUTTON).click()
    wait_for_results(page)
    set_page_size(page)
    return extract_rows(page)


def candidate_urls(base_url: str, html: bytes) -> list[str]:
    text = html.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    urls: list[str] = []
    for tag, attribute in (("a", "href"), ("iframe", "src"), ("embed", "src"), ("object", "data"), ("form", "action")):
        for element in soup.find_all(tag):
            value = element.get(attribute)
            if value:
                urls.append(urljoin(base_url, value))
    for pattern in (
        r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)",
        r"['\"]([^'\"]*(?:download|document|getfile|viewfile|filehandler)[^'\"]*)['\"]",
        r"['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]",
    ):
        for match in re.finditer(pattern, text, re.I):
            urls.append(urljoin(base_url, match.group(1)))
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
    path = destination.with_suffix(".pdf" if is_pdf else ".html")
    path.write_bytes(body)
    return {
        "url": response.url,
        "status": response.status,
        "content_type": content_type,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
        "saved_path": str(path),
    }


def score_row(row: dict[str, str]) -> int:
    text = row["row_text"].lower()
    score = 0
    for token, weight in (
        ("closure certification", 50),
        ("closure", 20),
        ("as-built", 20),
        ("as built", 20),
        ("final cover", 15),
        ("cap", 8),
        ("report", 5),
        ("1993", 5),
    ):
        if token in text:
            score += weight
    return score


def recover_document(context, output: Path, row: dict[str, str]) -> dict[str, object]:
    folder = output / f"doc_{row['docid']}"
    folder.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {**row, "attempts": [], "pdf_files": []}
    first = context.request.get(
        row["view_url"],
        headers={"Referer": PORTAL, "Accept": "text/html,application/pdf,*/*"},
        timeout=180000,
        fail_on_status_code=False,
    )
    record = save_response(first, folder / "view_document")
    result["attempts"].append(record)
    if record["is_pdf"]:
        result["pdf_files"].append(record["saved_path"])
        return result
    urls = candidate_urls(first.url, first.body())
    (folder / "candidate_urls.json").write_text(json.dumps(urls, indent=2), encoding="utf-8")
    for index, url in enumerate(urls[:80], start=1):
        if url == row["view_url"] or "edocpub.epa.ohio.gov" not in urlparse(url).netloc.lower():
            continue
        try:
            response = context.request.get(
                url,
                headers={"Referer": row["view_url"], "Accept": "application/pdf,text/html,*/*"},
                timeout=180000,
                fail_on_status_code=False,
            )
            item = save_response(response, folder / f"candidate_{index:03d}_{safe_name(Path(urlparse(url).path).name or 'response')}")
            result["attempts"].append(item)
            if item["is_pdf"]:
                result["pdf_files"].append(item["saved_path"])
        except Exception as exc:
            result["attempts"].append({"url": url, "error": repr(exc)})
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "area_b_1993_closure"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "SEARCH_STARTED",
        "queries": [],
        "documents": [],
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
        all_rows: dict[str, dict[str, str]] = {}
        for query in QUERIES:
            try:
                rows = run_query(page, query)
                report["queries"].append({**query, "status": "SEARCH_COMPLETED", "rows": rows})
                for row in rows:
                    all_rows[row["docid"]] = row
            except Exception as exc:
                report["queries"].append({**query, "status": "SEARCH_FAILED", "error": repr(exc)})
        ranked = sorted(all_rows.values(), key=lambda row: (-score_row(row), row["docid"]))
        (output / "ranked_rows.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
        for row in ranked[:20]:
            report["documents"].append(recover_document(context, output, row))
        browser.close()
    recovered = sum(bool(item.get("pdf_files")) for item in report["documents"])
    report["recovered_pdf_document_count"] = recovered
    report["status"] = "RECOVERED" if recovered else "NO_PUBLIC_PDF_RECOVERED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
