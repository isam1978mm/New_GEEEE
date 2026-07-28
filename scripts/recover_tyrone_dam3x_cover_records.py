"""Recover official Tyrone Dam 3X and No. 1 Stockpile cover records.

Temporary public-record recovery for the locked numerical-depth evidence search.
The helper downloads only official New Mexico EMNRD records, extracts searchable
text, and renders selected evidence pages relevant to measured cover thickness,
plot dimensions, coordinates, survey accuracy, common surface material,
vegetation, repairs, and long-term stability.

It does not call Earth Engine, create calibration rows, train a model, or enable
numerical depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE = "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
DOCUMENTS = {
    "3X tailing as-built report": BASE + "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.76_3XTailing_AsBuilt_Report.pdf",
    "3X tailing annual summary": BASE + "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.76_3XTailing_Annual_Summary_Report_Jan07.pdf",
    "No. 1 Stockpile as-built report": BASE + "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.76_No1Stockpile_AsBuilt_Report.pdf",
    "No. 1 Stockpile annual summary": BASE + "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.76_No1Stockpile_Annual_Summary_Report.pdf",
    "Comprehensive cover performance evaluation": BASE + "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.76_Comprehensive_Cover_Performance_Evaluation.pdf",
}
KEYWORDS = (
    "2-foot cover",
    "3-foot cover",
    "two-foot cover",
    "three-foot cover",
    "cover thickness",
    "thickness treatment",
    "measured thickness",
    "as-built survey",
    "as built survey",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "tolerance",
    "northing",
    "easting",
    "coordinates",
    "plot dimensions",
    "plot width",
    "plot length",
    "test plot",
    "top surface",
    "slope treatment",
    "seed",
    "vegetation",
    "mulch",
    "cover material",
    "borrow source",
    "erosion",
    "subsidence",
    "repair",
    "monitoring",
)
RENDER_TERMS = (
    "table 3",
    "cover thickness",
    "plot dimensions",
    "test plot layout",
    "as-built plan",
    "as built plan",
    "plate 1",
    "2-foot cover",
    "3-foot cover",
    "two-foot cover",
    "three-foot cover",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024
MAX_RENDERED_PAGES_PER_DOCUMENT = 20


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_and_render(pdf_path: Path, render_dir: Path) -> dict[str, object]:
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
    render_pages: list[int] = []
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        terms = [term for term in KEYWORDS if term in lower]
        if terms:
            lines = page.splitlines()
            selected: list[str] = []
            for index, line in enumerate(lines):
                if any(term in line.lower() for term in KEYWORDS):
                    selected.extend(lines[max(0, index - 6):min(len(lines), index + 10)])
            matches.append(
                {
                    "page": page_number,
                    "terms": terms,
                    "snippet": "\n".join(selected)[:32000],
                }
            )
        if any(term in lower for term in RENDER_TERMS):
            render_pages.append(page_number)

    render_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, object]] = []
    for page_number in sorted(set(render_pages))[:MAX_RENDERED_PAGES_PER_DOCUMENT]:
        prefix = render_dir / f"page_{page_number:04d}"
        render = subprocess.run(
            [
                "pdftoppm",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-png",
                "-r",
                "160",
                "-singlefile",
                str(pdf_path),
                str(prefix),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        png_path = prefix.with_suffix(".png")
        rendered.append(
            {
                "page": page_number,
                "returncode": render.returncode,
                "stderr": render.stderr[-2000:],
                "path": str(png_path) if png_path.exists() else None,
            }
        )
    return {
        "returncode": process.returncode,
        "stderr": process.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
        "rendered_pages": rendered,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "tyrone_dam3x_cover_records"
    documents_dir = output / "documents"
    rendered_root = output / "rendered_pages"
    documents_dir.mkdir(parents=True, exist_ok=True)
    rendered_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "official_source_page": (
            "https://www.emnrd.nm.gov/mmd/mining-act-reclamation-program/"
            "pending-and-approved-mine-applications/mining-applications-regular-existing/"
            "gr010retyrone-mine-revision-09-1/"
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
            response = session.get(
                url,
                headers=HEADERS,
                timeout=(60, 600),
                allow_redirects=True,
            )
            response.raise_for_status()
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
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
            raw_name = Path(urlparse(response.url).path).name or safe_name(title)
            filename = safe_name(raw_name)
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)
            render_dir = rendered_root / f"{index:02d}_{safe_name(title)}"
            record.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": content_type,
                    "size_bytes": len(body),
                    "is_pdf": True,
                    "sha256": sha256(body),
                    "saved_path": str(path),
                    "text_extraction": extract_and_render(path, render_dir),
                }
            )
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
