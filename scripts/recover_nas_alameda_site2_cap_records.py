"""Recover official NAS Alameda Site 2 landfill-cover completion records.

Temporary public-record recovery for the locked numerical-depth evidence search.
The helper downloads only official EPA/Navy documents, extracts searchable text,
and records passages relevant to cover-thickness verification, survey grids,
coordinates, measurement tolerances, common surface construction, vegetation,
repairs, and long-term stability.

It does not call Earth Engine, create calibration rows, train a model, or enable
numerical depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DOCUMENTS = {
    "EPA SEMS document 100035046": [
        "https://semspub.epa.gov/work/09/100035046.pdf",
        "https://semspub.epa.gov/src/document/09/100035046",
    ],
    "EPA Alameda Naval Air Station profile": [
        "https://cumulis.epa.gov/supercpad/cursites/csitinfo.cfm?id=0902731",
    ],
}
KEYWORDS = (
    "site 2",
    "landfill",
    "remedial action completion",
    "construction completion",
    "final cover",
    "cover thickness",
    "thickness verification",
    "verification monument",
    "monument",
    "100-foot",
    "100 foot",
    "grid",
    "survey",
    "as-built",
    "as built",
    "average thickness",
    "minimum thickness",
    "maximum thickness",
    "topsoil",
    "vegetative",
    "vegetation",
    "79 acre",
    "79-acre",
    "settlement",
    "repair",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_with_retries(session: requests.Session, urls: list[str]) -> tuple[requests.Response, str]:
    errors: list[str] = []
    for url in urls:
        for attempt in range(1, 4):
            try:
                response = session.get(
                    url,
                    headers=HEADERS,
                    timeout=(60, 600),
                    allow_redirects=True,
                    stream=False,
                )
                response.raise_for_status()
                return response, url
            except Exception as exc:
                errors.append(f"{url} attempt {attempt}: {exc!r}")
                time.sleep(attempt * 3)
    raise RuntimeError("; ".join(errors))


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
                start = max(0, index - 6)
                end = min(len(lines), index + 10)
                selected.extend(lines[start:end])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:30000],
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
    output = root / "artifacts" / "nas_alameda_site2_cap_records"
    documents_dir = output / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    for index, (title, urls) in enumerate(DOCUMENTS.items(), start=1):
        record: dict[str, object] = {"title": title, "candidate_urls": urls}
        try:
            response, requested_url = get_with_retries(session, urls)
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
            raw_name = Path(parsed.path).name or safe_name(title)
            filename = safe_name(raw_name)
            if not filename.lower().endswith(suffix):
                filename += suffix
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)

            record.update(
                {
                    "requested_url": requested_url,
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
                )[:15000]
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
