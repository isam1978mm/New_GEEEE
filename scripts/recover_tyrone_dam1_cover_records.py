"""Recover official Tyrone Dam 1 cover-thickness records.

Temporary public-record recovery for the locked numerical-depth evidence search.
The helper downloads only official New Mexico EMNRD records associated with the
Dam 1 / No. 1 tailing reclamation and financial-assurance releases. It extracts
searchable text, renders relevant pages, and checks PDFs for embedded electronic
files that could contain mapped as-built thickness geometry.

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

DOCUMENTS = {
    "2008 FA reduction application": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20081223_FAReduction-Application.pdf"
    ),
    "2008 Dam 1 financial assurance attachment": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20081223_FAReduction-AttachmentD.pdf"
    ),
    "2008 electronic files attachment": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20081223_FAReduction-AttachmentI.pdf"
    ),
    "2009 partial financial assurance release": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20091223_Tyrone_Mod09-03_Finanial_Assurance_Reduction.pdf"
    ),
    "2012 financial assurance release application": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "2012-12-17_Mod12-3Application_GR010RE.pdf"
    ),
}

KEYWORDS = (
    "dam 1 cover thickness",
    "cover thickness summary",
    "cover thickness",
    "thickness map",
    "thickness contour",
    "isopach",
    "greater than 3",
    ">3'",
    "three feet",
    "3 feet",
    "less than 3",
    "dam 1 top",
    "outslope",
    "12 ponds",
    "no. 1 tailing",
    "no. 1a tailing",
    "no. 1x tailing",
    "as-built",
    "as built",
    "final survey",
    "survey data",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "northing",
    "easting",
    "coordinate",
    "gps",
    "gis",
    "cad",
    "electronic files",
    "shape file",
    "shapefile",
    "vegetation",
    "revegetation",
    "financial assurance release",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024
MAX_RENDERED_PAGES = 60


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def request(session: requests.Session, url: str) -> requests.Response:
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=(60, 1200),
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc!r}")
            time.sleep(attempt * 4)
    raise RuntimeError("; ".join(errors))


def run_command(args: list[str]) -> dict[str, object]:
    process = subprocess.run(args, capture_output=True, text=True, check=False)
    return {
        "returncode": process.returncode,
        "stdout": process.stdout[-20000:],
        "stderr": process.stderr[-4000:],
    }


def extract_pdf(pdf_path: Path, render_dir: Path, embedded_dir: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    text_result = run_command(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)]
    )
    text = (
        text_path.read_text(encoding="utf-8", errors="replace")
        if text_path.exists()
        else ""
    )
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
    render_pages: list[int] = []
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        terms = [term for term in KEYWORDS if term.lower() in lower]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term.lower() in line.lower() for term in KEYWORDS):
                selected.extend(lines[max(0, index - 7):min(len(lines), index + 12)])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:40000],
            }
        )
        render_pages.append(page_number)

    render_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, object]] = []
    for page_number in sorted(set(render_pages))[:MAX_RENDERED_PAGES]:
        prefix = render_dir / f"page_{page_number:04d}"
        render = run_command(
            [
                "pdftoppm",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-png",
                "-r",
                "180",
                "-singlefile",
                str(pdf_path),
                str(prefix),
            ]
        )
        png_path = prefix.with_suffix(".png")
        rendered.append(
            {
                "page": page_number,
                "path": str(png_path) if png_path.exists() else None,
                **render,
            }
        )

    embedded_dir.mkdir(parents=True, exist_ok=True)
    attachment_list = run_command(["pdfdetach", "-list", str(pdf_path)])
    attachment_extract = run_command(
        ["pdfdetach", "-saveall", "-o", str(embedded_dir), str(pdf_path)]
    )
    embedded_files = [
        {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(embedded_dir.rglob("*"))
        if path.is_file()
    ]

    return {
        "text_extraction": text_result,
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
        "rendered_pages": rendered,
        "attachment_list": attachment_list,
        "attachment_extract": attachment_extract,
        "embedded_files": embedded_files,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "tyrone_dam1_cover_records"
    documents_dir = output / "documents"
    rendered_root = output / "rendered_pages"
    embedded_root = output / "embedded_files"
    documents_dir.mkdir(parents=True, exist_ok=True)
    rendered_root.mkdir(parents=True, exist_ok=True)
    embedded_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "official_source_page": (
            "https://www.emnrd.nm.gov/mmd/mining-act-reclamation-program/"
            "pending-and-approved-mine-applications/mining-applications-regular-existing/"
            "gr010retyrone-mine/"
        ),
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    for index, (title, url) in enumerate(DOCUMENTS.items(), start=1):
        record: dict[str, object] = {"title": title, "requested_url": url}
        try:
            response = request(session, url)
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
            if len(body) > MAX_BYTES:
                record.update(
                    {
                        "status": response.status_code,
                        "size_bytes": len(body),
                        "error": "size_limit",
                    }
                )
                report["documents"].append(record)
                continue
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            if not is_pdf:
                record.update(
                    {
                        "status": response.status_code,
                        "content_type": content_type,
                        "size_bytes": len(body),
                        "error": "not_pdf",
                    }
                )
                report["documents"].append(record)
                continue
            raw_name = Path(urlparse(response.url).path).name or safe_name(title)
            filename = safe_name(raw_name)
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)
            record.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": content_type,
                    "size_bytes": len(body),
                    "is_pdf": True,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "saved_path": str(path),
                    "extraction": extract_pdf(
                        path,
                        rendered_root / f"{index:02d}_{safe_name(title)}",
                        embedded_root / f"{index:02d}_{safe_name(title)}",
                    ),
                }
            )
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    embedded_count = sum(
        len(item.get("extraction", {}).get("embedded_files", []))
        for item in report["documents"]
        if isinstance(item.get("extraction"), dict)
    )
    report["pdf_count"] = pdf_count
    report["embedded_file_count"] = embedded_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (output / "recovery_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "pdf_count": pdf_count,
                "embedded_file_count": embedded_count,
            },
            indent=2,
        )
    )
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
