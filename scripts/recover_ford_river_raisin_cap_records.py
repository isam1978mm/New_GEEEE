"""Recover public Ford River Raisin landfill cap records.

This temporary evidence tool downloads only official Michigan EGLE documents
linked from the Ford River Raisin Warehouse facility page, extracts searchable
text, and records passages relevant to the east/west containment cell cap
profiles, closure certification, surveys, and as-built evidence.

It does not call Earth Engine, create calibration rows, train a model, or enable
numeric depth output.
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

PAGE_URL = (
    "https://www.michigan.gov/egle/about/organization/materials-management/"
    "hazardous-waste/liquid-industrial-byproducts/ford-river-raisin-warehouse"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
KEYWORDS = (
    "east containment",
    "eastern containment",
    "west containment",
    "western containment",
    "final cover",
    "cover system",
    "cap thickness",
    "topsoil",
    "vegetative",
    "as-built",
    "as built",
    "survey",
    "closure certification",
    "construction certification",
    "protective soil",
    "barrier soil",
)
MAX_BYTES = 500 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=180, allow_redirects=True)
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
        page_terms = [term for term in KEYWORDS if term in lower]
        if not page_terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in KEYWORDS):
                start = max(0, index - 3)
                end = min(len(lines), index + 5)
                selected.extend(lines[start:end])
        snippet = "\n".join(selected)
        matches.append(
            {
                "page": page_number,
                "terms": page_terms,
                "snippet": snippet[:16000],
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
    output = root / "artifacts" / "ford_river_raisin_cap_records"
    output.mkdir(parents=True, exist_ok=True)
    docs_dir = output / "documents"
    docs_dir.mkdir(exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "source_page": PAGE_URL,
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    page_response = request(session, PAGE_URL)
    (output / "facility_page.html").write_bytes(page_response.content)
    soup = BeautifulSoup(page_response.text, "html.parser")

    candidates: list[dict[str, str]] = []
    for tag in soup.find_all("a", href=True):
        anchor = clean(tag.get_text(" "))
        url = urljoin(page_response.url, tag["href"])
        lower_url = url.lower()
        lower_anchor = anchor.lower()
        if (
            lower_url.endswith(".pdf")
            or "/-/media/" in lower_url
            or any(token in lower_anchor for token in ("license", "fact sheet", "final decision", "response to comments"))
        ):
            candidates.append({"anchor": anchor, "url": url})

    # Include the official license URL explicitly in case the page renderer hides it.
    candidates.append(
        {
            "anchor": "License - 9/30/2022",
            "url": (
                "https://www.michigan.gov/egle/-/media/Project/Websites/egle/Documents/"
                "Programs/MMD/Hazardous-Waste/Ford-River-Raisin/"
                "2022-09-30-Ford-River-Raisin-License.pdf"
            ),
        }
    )

    deduped: dict[str, dict[str, str]] = {}
    for item in candidates:
        deduped.setdefault(item["url"], item)

    for index, item in enumerate(deduped.values(), start=1):
        record: dict[str, object] = {"anchor": item["anchor"], "requested_url": item["url"]}
        try:
            response = request(session, item["url"])
            body = response.content
            if len(body) > MAX_BYTES:
                record.update({"status": response.status_code, "skipped": "size_limit", "size_bytes": len(body)})
                report["documents"].append(record)
                continue
            content_type = response.headers.get("content-type", "").lower()
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            suffix = ".pdf" if is_pdf else ".html"
            parsed = urlparse(response.url)
            filename = safe_name(Path(parsed.path).name or f"document_{index}")
            if not filename.lower().endswith(suffix):
                filename += suffix
            path = docs_dir / f"{index:02d}_{filename}"
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
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    report["pdf_count"] = pdf_count
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "pdf_count": pdf_count}, indent=2))
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
