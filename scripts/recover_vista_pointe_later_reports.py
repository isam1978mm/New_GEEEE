"""Recover later Cleveland-Cliffs/Vista Pointe public landfill reports.

This one-off evidence recovery is restricted to Ohio EPA public records already
identified in the approved full-scale cover search. It does not call Earth
Engine, create calibration rows, train a model, or enable numeric depth output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

PORTAL = "https://edocpub.epa.ohio.gov/publicportal/"
DOCUMENTS = {
    "annual_2023": {"docid": "2561718", "label": "2023 annual operational report"},
    "report_2023": {"docid": "2259952", "label": "2023 industrial-landfill report"},
    "annual_2025": {"docid": "3777273", "label": "2025 annual operational report"},
}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180]


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
        "saved_path": str(path),
    }


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
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def recover_one(context, root: Path, key: str, metadata: dict[str, str]) -> dict[str, object]:
    folder = root / key
    folder.mkdir(parents=True, exist_ok=True)
    docid = metadata["docid"]
    view_url = f"{PORTAL}ViewDocument.aspx?docid={docid}"
    result: dict[str, object] = {
        "key": key,
        "docid": docid,
        "label": metadata["label"],
        "view_url": view_url,
        "attempts": [],
        "pdf_files": [],
    }
    first = context.request.get(
        view_url,
        headers={"Referer": PORTAL, "Accept": "text/html,application/pdf,*/*"},
        timeout=180000,
        fail_on_status_code=False,
    )
    record = save_response(first, folder / "view_document")
    result["attempts"].append(record)
    if record["is_pdf"]:
        result["pdf_files"].append(record["saved_path"])
        return result
    candidates = candidate_urls(first.url, first.body())
    (folder / "candidate_urls.json").write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    for index, url in enumerate(candidates[:100], start=1):
        if url == view_url or "edocpub.epa.ohio.gov" not in urlparse(url).netloc.lower():
            continue
        try:
            response = context.request.get(
                url,
                headers={"Referer": view_url, "Accept": "application/pdf,text/html,*/*"},
                timeout=180000,
                fail_on_status_code=False,
            )
            item = save_response(
                response,
                folder / f"candidate_{index:03d}_{safe_name(Path(urlparse(url).path).name or 'response')}",
            )
            result["attempts"].append(item)
            if item["is_pdf"]:
                result["pdf_files"].append(item["saved_path"])
        except Exception as exc:
            result["attempts"].append({"url": url, "error": repr(exc)})
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "vista_pointe_later_reports"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "RECOVERY_STARTED",
        "documents": [],
        "approved_scope": {
            "full_scale_vegetated_cover_only": True,
            "required_clean_width_m": "30-40 after exclusions",
            "final_measured_as_built_depths_required": True,
            "plan_changed": False,
        },
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36")
        page = context.new_page()
        page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2000)
        for key, metadata in DOCUMENTS.items():
            report["documents"].append(recover_one(context, output, key, metadata))
        browser.close()
    recovered = sum(bool(item.get("pdf_files")) for item in report["documents"])
    report["recovered_pdf_document_count"] = recovered
    report["status"] = "RECOVERED" if recovered else "RECOVERY_FAILED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if recovered else 1


if __name__ == "__main__":
    raise SystemExit(main())
