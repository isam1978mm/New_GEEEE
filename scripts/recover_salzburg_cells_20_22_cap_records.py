"""Recover official Salzburg Landfill Cells 20-22 closure records.

Temporary evidence-recovery helper for the locked numerical-depth search.
It downloads only public Michigan EGLE records, extracts searchable text, and
records passages relevant to the 2017 closure, final-cover construction,
coordinate-tied thickness surveys, CQA certification, as-built drawings,
measurement accuracy, vegetation, repairs, and postclosure stability.

It does not call Earth Engine, create calibration rows, train a model, or
enable numerical depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

LICENSE_PAGE = (
    "https://www.michigan.gov/egle/about/organization/materials-management/"
    "hazardous-waste/liquid-industrial-byproducts/"
    "dow-midland-salzburg-landfill-operating-license/license-documents"
)
FACILITY_DATABASE = "https://www.egle.state.mi.us/wdspi/Pca/Facility.aspx?w=399133"
EXPLICIT_DOCUMENTS = {
    "2016 Cells 20-22 final-cover design submittal": (
        "https://www.michigan.gov/documents/deq/"
        "deq-owmrp-hws_2016-02-11_Design_Submittal_Minus_Appendix_A_527156_7.pdf"
    ),
    "Current signed operating license": (
        "https://www.michigan.gov/egle/-/media/Project/Websites/egle/Documents/"
        "Programs/MMD/Licenses/MMD/Final-Signed-Dow-License.pdf"
    ),
}
ANCHOR_TERMS = (
    "landfill",
    "closure",
    "postclosure",
    "post closure",
    "topographic",
    "drawing",
    "current license",
    "operating license",
)
KEYWORDS = (
    "cells 20-22",
    "cells 20, 21, and 22",
    "cells 20, 21 and 22",
    "cell 20",
    "cell 21",
    "cell 22",
    "final cover",
    "construction certification",
    "closure certification",
    "cqa certification",
    "as-built",
    "as built",
    "thickness",
    "same coordinates",
    "survey",
    "survey data",
    "vertical tolerance",
    "horizontal tolerance",
    "0.01 ft",
    "0.1 ft",
    "protective cover",
    "topsoil",
    "vegetative",
    "settlement",
    "2017",
    "august 2, 2017",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=240, allow_redirects=True)
    response.raise_for_status()
    return response


def extract_pdf_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    process = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        terms = [term for term in KEYWORDS if term in lower]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in KEYWORDS):
                start = max(0, index - 5)
                end = min(len(lines), index + 9)
                selected.extend(lines[start:end])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:24000],
            }
        )
    return {
        "returncode": process.returncode,
        "stderr": process.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "salzburg_cells_20_22_cap_records"
    documents_dir = output / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "source_page": LICENSE_PAGE,
        "facility_database": FACILITY_DATABASE,
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    candidates: dict[str, dict[str, str]] = {}
    for title, url in EXPLICIT_DOCUMENTS.items():
        candidates[url] = {"title": title, "url": url}

    for source_name, source_url in (
        ("license_page", LICENSE_PAGE),
        ("facility_database", FACILITY_DATABASE),
    ):
        try:
            response = request(session, source_url)
            (output / f"{source_name}.html").write_bytes(response.content)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                title = clean(tag.get_text(" "))
                lower = title.lower()
                url = urljoin(response.url, tag["href"])
                if any(term in lower for term in ANCHOR_TERMS):
                    candidates.setdefault(url, {"title": title or source_name, "url": url})
        except Exception as exc:
            report.setdefault("source_errors", []).append(
                {"source": source_url, "error": repr(exc)}
            )

    for index, item in enumerate(candidates.values(), start=1):
        record: dict[str, object] = {
            "title": item["title"],
            "requested_url": item["url"],
        }
        try:
            response = request(session, item["url"])
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
            if len(body) > MAX_BYTES:
                record.update(
                    {
                        "status": response.status_code,
                        "size_bytes": len(body),
                        "skipped": "size_limit",
                    }
                )
                report["documents"].append(record)
                continue

            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            suffix = ".pdf" if is_pdf else ".html"
            parsed = urlparse(response.url)
            raw_name = Path(parsed.path).name or safe_name(item["title"])
            filename = safe_name(raw_name)
            if not filename.lower().endswith(suffix):
                filename += suffix
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)

            record.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": content_type,
                    "size_bytes": len(body),
                    "is_pdf": is_pdf,
                    "sha256": sha256(body),
                    "saved_path": str(path),
                }
            )
            if is_pdf:
                record["text_extraction"] = extract_pdf_text(path)
            else:
                record["html_preview"] = clean(
                    BeautifulSoup(response.text, "html.parser").get_text(" ")
                )[:12000]
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    report["pdf_count"] = pdf_count
    report["candidate_count"] = len(candidates)
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (output / "recovery_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_count": len(candidates),
                "pdf_count": pdf_count,
            },
            indent=2,
        )
    )
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
