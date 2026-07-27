"""Enumerate Ohio landfill cap certification records under the approved scope.

This is a temporary public-record inventory tool. It restricts the Ohio EPA
search to municipal or industrial landfill programs and to Professional
Certification or Report document types, requests up to 600 rows per search,
and ranks likely full-scale final-cap construction records for manual review.

It does not call Earth Engine, create calibration rows, train a model, or enable
numeric depth output.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

PORTAL = "https://edocpub.epa.ohio.gov/publicportal/"
PROGRAMS = (
    "MUNICIPAL SOLID WASTE LANDFILLS",
    "INDUSTRIAL MANUFACTURING WASTE LANDFILLS",
)
DOCUMENT_TYPES = (
    "Professional Certification",
    "Report",
)
SEARCH_TERMS = (
    '"construction certification report"',
    '"cap protection layer"',
    '"final cap" certification',
    '"closure certification" cap',
)

FULL_TEXT = "#ctl00_search_txtFullText"
PROGRAM = "#ctl00_search_KeywordPanel1_ddlValue_-1_1_109_1"
DOC_TYPE = "#ctl00_search_ddlDocType"
SEARCH_BUTTON = "#ctl00_search_btnSearch"
PAGE_SIZE = "#ctl00_results_DocHitList_DocHitList_CurrentPageSize"
RESULT_LINK = "a[onclick*='ViewDocument.aspx?docid=']"


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def wait_for_results(page: Page) -> None:
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


def set_page_size_600(page: Page) -> None:
    selector = page.locator(PAGE_SIZE)
    if selector.count() != 1:
        return
    current = selector.input_value()
    if current == "600":
        return
    before = page.locator(RESULT_LINK).count()
    selector.select_option("600")
    page.wait_for_timeout(3500)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    # ASP.NET postback can replace the whole result table without changing URL.
    page.wait_for_function(
        """({selector, before}) => {
          const sel = document.querySelector(selector);
          const count = document.querySelectorAll("a[onclick*='ViewDocument.aspx?docid=']").length;
          return !sel || sel.value === '600' || count !== before;
        }""",
        {"selector": PAGE_SIZE, "before": before},
        timeout=60000,
    )
    page.wait_for_timeout(1500)


def parse_result_text(text: str) -> dict[str, Any]:
    # Preserve the authoritative portal row verbatim; parsed fields are helpers.
    record: dict[str, Any] = {"row_text": clean(text)}
    docid_match = re.search(r"\b(\d{5,})\s*$", record["row_text"])
    if docid_match:
        record["docid"] = docid_match.group(1)
    date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", record["row_text"])
    if date_match:
        record["document_date"] = date_match.group(1)
    return record


def extract_rows(page: Page) -> list[dict[str, Any]]:
    links = page.locator(RESULT_LINK)
    records: list[dict[str, Any]] = []
    for index in range(links.count()):
        link = links.nth(index)
        text = clean(link.inner_text())
        onclick = link.get_attribute("onclick") or ""
        match = re.search(r"ViewDocument\.aspx\?docid=(\d+)", onclick)
        if not match:
            continue
        record = parse_result_text(text)
        record["docid"] = match.group(1)
        record["view_url"] = f"{PORTAL}ViewDocument.aspx?docid={match.group(1)}"
        records.append(record)
    return records


def date_year(record: dict[str, Any]) -> int | None:
    value = record.get("document_date")
    if not value:
        return None
    try:
        return datetime.strptime(value, "%m/%d/%Y").year
    except ValueError:
        return None


def score_record(record: dict[str, Any]) -> tuple[int, list[str]]:
    text = record.get("row_text", "").lower()
    score = 0
    reasons: list[str] = []
    weights = (
        ("construction certification", 20),
        ("professional certification", 16),
        ("final cap", 14),
        ("closure certification", 14),
        ("cap construction", 12),
        ("cap protection", 10),
        ("final closure", 10),
        ("as-built", 9),
        ("as built", 9),
        ("composite cap", 8),
        ("closure", 5),
        ("certification", 5),
        ("report", 2),
    )
    for token, weight in weights:
        if token in text:
            score += weight
            reasons.append(token)
    if "municipal solid waste landfills" in text:
        score += 4
        reasons.append("municipal-landfill program")
    if "industrial manufacturing waste landfills" in text:
        score += 4
        reasons.append("industrial-landfill program")
    year = date_year(record)
    if year is not None:
        # Prefer completed projects old enough to have Sentinel-1 follow-up,
        # while retaining recent records in the inventory.
        if 2014 <= year <= 2023:
            score += 7
            reasons.append("Sentinel-1-era follow-up possible")
        elif 2000 <= year < 2014:
            score += 3
            reasons.append("pre-Sentinel-1 construction")
    return score, reasons


def run_query(page: Page, term: str, program: str, document_type: str) -> dict[str, Any]:
    page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2500)
    page.locator(FULL_TEXT).fill(term)
    page.locator(PROGRAM).select_option(label=program)
    page.locator(DOC_TYPE).select_option(label=document_type)
    page.locator(SEARCH_BUTTON).click()
    wait_for_results(page)
    set_page_size_600(page)
    rows = extract_rows(page)
    body = clean(page.locator("body").inner_text())
    count_match = re.search(r"Search returned\s+(\d+)\s+matching documents", body, re.I)
    return {
        "term": term,
        "program": program,
        "document_type": document_type,
        "reported_match_count": int(count_match.group(1)) if count_match else None,
        "extracted_row_count": len(rows),
        "rows": rows,
        "status": "SEARCH_COMPLETED",
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "ohio_full_scale_cap_records_v3"
    output.mkdir(parents=True, exist_ok=True)

    queries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    by_docid: dict[str, dict[str, Any]] = {}
    matched_queries: dict[str, list[dict[str, str]]] = defaultdict(list)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        for query_index, program in enumerate(PROGRAMS):
            for document_type in DOCUMENT_TYPES:
                for term in SEARCH_TERMS:
                    descriptor = {
                        "term": term,
                        "program": program,
                        "document_type": document_type,
                    }
                    try:
                        result = run_query(page, term, program, document_type)
                        queries.append(result)
                        for row in result["rows"]:
                            docid = row["docid"]
                            by_docid.setdefault(docid, row)
                            matched_queries[docid].append(descriptor)
                    except Exception as exc:
                        failure = {**descriptor, "status": "SEARCH_FAILED", "error": repr(exc)}
                        failures.append(failure)
                        page.screenshot(
                            path=output / f"failure_{len(failures):02d}.png", full_page=True
                        )
        browser.close()

    ranked: list[dict[str, Any]] = []
    for docid, row in by_docid.items():
        score, reasons = score_record(row)
        ranked.append(
            {
                **row,
                "score": score,
                "score_reasons": reasons,
                "matched_queries": matched_queries[docid],
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item.get("document_date", ""), item["docid"]))

    summary = {
        "status": "OHIO_RESTRICTED_CAP_CERTIFICATION_INVENTORY_COMPLETE"
        if queries
        else "OHIO_RESTRICTED_CAP_CERTIFICATION_INVENTORY_FAILED",
        "portal": PORTAL,
        "approved_scope": {
            "full_scale_vegetated_cover_only": True,
            "required_clean_width_m": "30-40 after exclusions",
            "final_measured_as_built_depths_required": True,
            "small_test_plots_excluded": True,
        },
        "query_count_completed": len(queries),
        "query_count_failed": len(failures),
        "unique_document_count": len(ranked),
        "top_candidate_records": ranked[:100],
        "failures": failures,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "decision": "DOCUMENT_INVENTORY_ONLY_MANUAL_REPORT_REVIEW_REQUIRED",
    }
    (output / "query_results.json").write_text(json.dumps(queries, indent=2), encoding="utf-8")
    (output / "ranked_document_inventory.json").write_text(
        json.dumps(ranked, indent=2), encoding="utf-8"
    )
    (output / "inventory_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0 if queries else 1


if __name__ == "__main__":
    raise SystemExit(main())
