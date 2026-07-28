"""Recover official Olympic View Sanitary Landfill cap records.

Temporary evidence-recovery helper for the locked numerical-depth search.
It downloads only public Washington Department of Ecology records, extracts
searchable text, and records passages relevant to measured final-cover
thickness, mapped investigation points, repairs, cap construction, and
post-closure stability.

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

SITE_URL = "https://apps.ecology.wa.gov/cleanupsearch/site/4217"
EXPLICIT_DOCUMENT_URLS = {
    "2011 Final Cover Investigation and Erosion Repair Report":
        "https://apps.ecology.wa.gov/cleanupsearch/document/6986",
}
TITLE_TOKENS = (
    "final cover investigation",
    "erosion repair",
    "post-closure operation and maintenance",
    "periodic review",
    "cleanup action plan",
    "annual monitoring report",
)
KEYWORDS = (
    "final cover",
    "cover thickness",
    "thickness",
    "test pit",
    "test pits",
    "boring",
    "probe",
    "survey",
    "as-built",
    "as built",
    "topsoil",
    "vegetative",
    "geomembrane",
    "protective soil",
    "erosion",
    "repair",
    "old barney white",
    "phase i",
    "phase ii",
    "inches",
    "feet",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 500 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(session: requests.Session, url: str) -> requests.Response:
    response = session.get(
        url,
        headers=HEADERS,
        timeout=180,
        allow_redirects=True,
    )
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
                start = max(0, index - 4)
                end = min(len(lines), index + 7)
                selected.extend(lines[start:end])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:20000],
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
    output = root / "artifacts" / "olympic_view_cap_records"
    documents_dir = output / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "source_page": SITE_URL,
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    page_response = request(session, SITE_URL)
    (output / "site_page.html").write_bytes(page_response.content)
    soup = BeautifulSoup(page_response.text, "html.parser")

    candidates: dict[str, dict[str, str]] = {}
    for title, url in EXPLICIT_DOCUMENT_URLS.items():
        candidates[url] = {"title": title, "url": url}

    for tag in soup.find_all("a", href=True):
        title = clean(tag.get_text(" "))
        lower = title.lower()
        if not any(token in lower for token in TITLE_TOKENS):
            continue
        url = urljoin(page_response.url, tag["href"])
        candidates.setdefault(url, {"title": title, "url": url})

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
                )[:10000]
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    report["pdf_count"] = pdf_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (output / "recovery_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "pdf_count": pdf_count}, indent=2))
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
