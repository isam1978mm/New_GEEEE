"""Recover decisive Allen Harbor records from EPA SEMS collection feeds.

The public Cumulis pages load their document tables from official SEMS JSON
collection endpoints. This temporary helper reads only those official feeds,
selects Allen Harbor / Site 09 construction, design, as-built, monitoring and
settlement records, downloads the corresponding EPA PDFs, and extracts relevant
text. It does not call Earth Engine, create calibration rows, train a model, or
enable numerical depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import requests

COLLECTIONS = {
    "key_documents": "https://semspub.epa.gov/src/cachejson/01/SC/70121",
    "public_documents": "https://semspub.epa.gov/src/cachejson/01/SC/31799",
    "five_year_reviews": "https://semspub.epa.gov/src/cachejson/01/SC/32764",
    "decision_documents": "https://semspub.epa.gov/src/cachejson/01/SC/32765",
}

TITLE_TERMS = (
    "allen harbor",
    "site 09",
    "site 9",
    "remedial action report",
    "design analysis report",
    "final design",
    "construction completion",
    "construction quality",
    "as-built",
    "as built",
    "landfill cap",
    "long-term management",
    "long term management",
    "settlement survey",
    "landfill inspection",
    "five-year review",
    "five year review",
    "explanation of significant differences",
)

TEXT_TERMS = (
    "multimedia cap",
    "soil cap",
    "final cover",
    "cover thickness",
    "cap thickness",
    "as-built",
    "as built",
    "survey",
    "surveyor",
    "accuracy",
    "precision",
    "tolerance",
    "certification",
    "18-inch",
    "6-inch",
    "36 inches",
    "3-foot",
    "2-foot",
    "common borrow",
    "vegetative",
    "settlement",
    "subsidence",
    "repair",
    "erosion",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "application/json,text/html,application/pdf,*/*",
}
MAX_BYTES = 900 * 1024 * 1024


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180] or "document"


def request(session: requests.Session, url: str) -> requests.Response:
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=(45, 300),
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc!r}")
            time.sleep(attempt * 2)
    raise RuntimeError("; ".join(errors))


def extract_pdf_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    proc = subprocess.run(
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
        terms = [term for term in TEXT_TERMS if term in lower]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in TEXT_TERMS):
                selected.extend(lines[max(0, index - 5):min(len(lines), index + 9)])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:30000],
            }
        )
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def normalized_rows(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, dict):
        rows = payload.get("data", [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "allen_harbor_collection_records"
    docs = out / "documents"
    feeds = out / "feeds"
    docs.mkdir(parents=True, exist_ok=True)
    feeds.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "collections": COLLECTIONS,
        "selected_records": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    selected: dict[str, dict[str, object]] = {}
    for label, url in COLLECTIONS.items():
        try:
            response = request(session, url)
            payload = response.json()
            (feeds / f"{label}.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
            rows = normalized_rows(payload)
            report.setdefault("collection_counts", {})[label] = len(rows)
            for row in rows:
                title = clean(row.get("docTitle"))
                lower = title.lower()
                doc_id = clean(row.get("docId"))
                if not doc_id or not any(term in lower for term in TITLE_TERMS):
                    continue
                selected.setdefault(
                    doc_id,
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "doc_date": clean(row.get("docDate")),
                        "author": clean(row.get("author")),
                        "addressee": clean(row.get("addressee")),
                        "collections": [],
                    },
                )["collections"].append(label)
        except Exception as exc:
            report.setdefault("collection_errors", []).append(
                {"label": label, "url": url, "error": repr(exc)}
            )

    for index, item in enumerate(selected.values(), start=1):
        doc_id = str(item["doc_id"])
        record = dict(item)
        urls = [
            f"https://semspub.epa.gov/work/01/{doc_id}.pdf",
            f"https://semspub.epa.gov/src/document/01/{doc_id}",
        ]
        record["candidate_urls"] = urls
        for url in urls:
            try:
                response = request(session, url)
                body = response.content
                ctype = response.headers.get("content-type", "").lower()
                if len(body) > MAX_BYTES:
                    record["error"] = f"size_limit:{len(body)}"
                    break
                is_pdf = body.startswith(b"%PDF-") or "application/pdf" in ctype
                if not is_pdf:
                    record.setdefault("non_pdf_responses", []).append(
                        {"url": url, "content_type": ctype, "size_bytes": len(body)}
                    )
                    continue
                filename = f"{index:03d}_{safe_name(doc_id)}_{safe_name(str(item['title']))}.pdf"
                path = docs / filename
                path.write_bytes(body)
                record.update(
                    {
                        "status": response.status_code,
                        "final_url": response.url,
                        "content_type": ctype,
                        "size_bytes": len(body),
                        "is_pdf": True,
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "saved_path": str(path),
                        "text_extraction": extract_pdf_text(path),
                    }
                )
                break
            except Exception as exc:
                record.setdefault("download_errors", []).append(
                    {"url": url, "error": repr(exc)}
                )
        report["selected_records"].append(record)

    pdf_count = sum(1 for row in report["selected_records"] if row.get("is_pdf"))
    report["selected_count"] = len(selected)
    report["pdf_count"] = pdf_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (out / "recovery_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "selected_count": len(selected),
                "pdf_count": pdf_count,
            },
            indent=2,
        )
    )
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
