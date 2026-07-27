"""Recover shortlisted Ohio full-scale landfill closure certifications.

The shortlisted records come from the restricted Ohio eDocument inventory and
remain subject to the approved gates: full-scale vegetated surface, 30–40 m
clean interior after exclusions, and final measured as-built depths.

This temporary recovery tool does not call Earth Engine, create calibration
rows, train a model, or enable numeric depth output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import APIResponse, sync_playwright

PORTAL = "https://edocpub.epa.ohio.gov/publicportal/"
DOCUMENTS = {
    "arcelormittal_cleveland_2021": {
        "docid": "1494723",
        "portal_row": "ARCELORMITTAL CLEVELAND LLC (CLEVELAND CITY) - Report - 1/8/2021 - INDUSTRIAL MANUFACTURING WASTE LANDFILLS - CUYAHOGA - ISWL020091 - CLOSURE CERTIFICATION - 1494723",
    },
    "huron_river_properties_2016_a": {
        "docid": "535526",
        "portal_row": "HURON RIVER PROPERTIES INC - Report - 12/27/2016 - INDUSTRIAL MANUFACTURING WASTE LANDFILLS - ERIE - RSWL018770 - CLOSURE CERTIFICATION - 535526",
    },
    "huron_river_properties_2016_b": {
        "docid": "535617",
        "portal_row": "HURON RIVER PROPERTIES INC - Report - 12/27/2016 - INDUSTRIAL MANUFACTURING WASTE LANDFILLS - ERIE - RSWL018770 - CLOSURE CERTIFICATION - 535617",
    },
    "huron_river_properties_2018": {
        "docid": "942224",
        "portal_row": "HURON RIVER PROPERTIES INC - Report - 11/15/2018 - INDUSTRIAL MANUFACTURING WASTE LANDFILLS - ERIE - RSWL018770 - CLOSURE CERTIFICATION - 942224",
    },
    "huron_river_properties_2019": {
        "docid": "1105691",
        "portal_row": "HURON RIVER PROPERTIES INC - Report - 5/15/2019 - INDUSTRIAL MANUFACTURING WASTE LANDFILLS - ERIE - RSWL018770 - CLOSURE CERTIFICATION - 1105691",
    },
}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180]


def content_type(response: APIResponse) -> str:
    return response.headers.get("content-type", "").lower()


def save_response(response: APIResponse, destination: Path) -> dict[str, object]:
    body = response.body()
    ctype = content_type(response)
    is_pdf = body.startswith(b"%PDF-") or "application/pdf" in ctype
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(body)
    return {
        "url": response.url,
        "status": response.status,
        "content_type": ctype,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
        "saved_path": str(path),
    }


def candidate_urls(base_url: str, html: bytes) -> list[str]:
    text = html.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    urls: list[str] = []
    for tag, attribute in (
        ("a", "href"),
        ("iframe", "src"),
        ("embed", "src"),
        ("object", "data"),
        ("form", "action"),
    ):
        for element in soup.find_all(tag):
            value = element.get(attribute)
            if value:
                urls.append(urljoin(base_url, value))
    for meta in soup.find_all("meta"):
        if str(meta.get("http-equiv", "")).lower() == "refresh":
            match = re.search(r"url\s*=\s*([^;]+)$", str(meta.get("content", "")), re.I)
            if match:
                urls.append(urljoin(base_url, match.group(1).strip(" '\"")))
    patterns = (
        r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)",
        r"['\"]([^'\"]*(?:download|document|getfile|viewfile|filehandler)[^'\"]*)['\"]",
        r"['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            urls.append(urljoin(base_url, match.group(1)))
    unique: list[str] = []
    seen: set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


def recover_one(context, output: Path, key: str, metadata: dict[str, str]) -> dict[str, object]:
    folder = output / key
    folder.mkdir(parents=True, exist_ok=True)
    docid = metadata["docid"]
    view_url = f"{PORTAL}ViewDocument.aspx?docid={docid}"
    result: dict[str, object] = {
        "key": key,
        "docid": docid,
        "portal_row": metadata["portal_row"],
        "view_url": view_url,
        "attempts": [],
        "pdf_files": [],
    }

    response = context.request.get(
        view_url,
        headers={"Referer": PORTAL, "Accept": "text/html,application/pdf,*/*"},
        timeout=120000,
        fail_on_status_code=False,
    )
    first = save_response(response, folder / "view_document")
    result["attempts"].append(first)
    if first["is_pdf"]:
        result["pdf_files"].append(first["saved_path"])
        return result

    html = response.body()
    candidates = candidate_urls(response.url, html)
    (folder / "candidate_urls.json").write_text(
        json.dumps(candidates, indent=2), encoding="utf-8"
    )
    for index, url in enumerate(candidates[:80], start=1):
        # Avoid leaving the Ohio public-record host or recursively opening the
        # same wrapper URL.
        if url == view_url or "edocpub.epa.ohio.gov" not in urlparse(url).netloc.lower():
            continue
        try:
            candidate = context.request.get(
                url,
                headers={"Referer": view_url, "Accept": "application/pdf,text/html,*/*"},
                timeout=120000,
                fail_on_status_code=False,
            )
            record = save_response(
                candidate,
                folder / f"candidate_{index:03d}_{safe_name(Path(urlparse(url).path).name or 'response')}",
            )
            result["attempts"].append(record)
            if record["is_pdf"]:
                result["pdf_files"].append(record["saved_path"])
        except Exception as exc:
            result["attempts"].append({"url": url, "error": repr(exc)})
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "ohio_closure_certifications"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "OHIO_CLOSURE_CERTIFICATION_RECOVERY_STARTED",
        "documents": [],
        "approved_scope": {
            "full_scale_vegetated_cover_only": True,
            "required_clean_width_m": "30-40 after exclusions",
            "final_measured_as_built_depths_required": True,
            "small_test_plots_excluded": True,
        },
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
        )
        page = context.new_page()
        page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)
        for key, metadata in DOCUMENTS.items():
            report["documents"].append(recover_one(context, output, key, metadata))
        browser.close()

    recovered = sum(bool(item.get("pdf_files")) for item in report["documents"])
    report["recovered_pdf_document_count"] = recovered
    report["status"] = (
        "OHIO_CLOSURE_CERTIFICATIONS_RECOVERED"
        if recovered
        else "OHIO_CLOSURE_CERTIFICATION_RECOVERY_FAILED"
    )
    report["decision"] = "MANUAL_REPORT_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if recovered else 1


if __name__ == "__main__":
    raise SystemExit(main())
