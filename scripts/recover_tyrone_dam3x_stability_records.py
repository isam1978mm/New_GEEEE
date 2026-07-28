"""Recover decisive Tyrone Dam 3X coordinate and stability records.

Downloads only official New Mexico EMNRD records that may close the remaining
Tyrone documentary gates: the comprehensive cover evaluation, 2020 closure-plan
text/drawings, and 2021 approval. Extracts text and renders pages mentioning Dam
3X, test plots, monitoring, repairs, reclaimed status, survey control or plot
coordinates.

No Earth Engine, calibration, training, or app-depth changes are performed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests

DOCUMENTS = {
    "Comprehensive cover performance evaluation": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20071011_Closeout_Plan_Update_AppendixE_C.75_Comp_Cover_Performance_Eval_Stck.pdf"
    ),
    "2020 closure plan text figures plates tables": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "2-18106417_004RRev1_Tyrone_CCP_Update_20200429.pdf"
    ),
    "2020 reclamation design drawings": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "3-AppendixA_ReclamationDesignDrawings_Rev1.pdf"
    ),
    "2021 Revision 09-1 approval": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "TyroneRevision09-1Final_signed_32921.pdf"
    ),
}
KEYWORDS = (
    "dam 3x", "no. 3x dam", "3x dam", "3x tailing", "test plot 5",
    "test plot 6", "tp#5", "tp#6", "reclaimed", "reclamation complete",
    "monitoring", "maintenance", "repair", "subsidence", "settlement",
    "erosion", "vegetation", "financial assurance release", "as-built",
    "as built", "survey", "coordinate", "northing", "easting", "datum",
    "gps", "accuracy", "precision", "tolerance", "stable", "disturbance",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024
MAX_RENDERED = 30


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180] or "document"


def extract(pdf_path: Path, render_dir: Path) -> dict[str, object]:
    txt = pdf_path.with_suffix(".txt")
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(txt)],
        capture_output=True,
        text=True,
        check=False,
    )
    text = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
    render_pages: list[int] = []
    for page_no, page in enumerate(pages, 1):
        lower = page.lower()
        terms = [term for term in KEYWORDS if term in lower]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in KEYWORDS):
                selected.extend(lines[max(0, i - 6):min(len(lines), i + 10)])
        matches.append({
            "page": page_no,
            "terms": terms,
            "snippet": "\n".join(selected)[:36000],
        })
        render_pages.append(page_no)

    render_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, object]] = []
    for page_no in sorted(set(render_pages))[:MAX_RENDERED]:
        prefix = render_dir / f"page_{page_no:04d}"
        render = subprocess.run(
            ["pdftoppm", "-f", str(page_no), "-l", str(page_no), "-png",
             "-r", "150", "-singlefile", str(pdf_path), str(prefix)],
            capture_output=True,
            text=True,
            check=False,
        )
        png = prefix.with_suffix(".png")
        rendered.append({
            "page": page_no,
            "returncode": render.returncode,
            "stderr": render.stderr[-2000:],
            "path": str(png) if png.exists() else None,
        })
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr[-4000:],
        "text_path": str(txt),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
        "rendered_pages": rendered,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "tyrone_dam3x_stability_records"
    docs = out / "documents"
    rendered = out / "rendered_pages"
    docs.mkdir(parents=True, exist_ok=True)
    rendered.mkdir(parents=True, exist_ok=True)
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
    for index, (title, url) in enumerate(DOCUMENTS.items(), 1):
        rec: dict[str, object] = {"title": title, "requested_url": url}
        try:
            response = session.get(url, headers=HEADERS, timeout=(60, 900), allow_redirects=True)
            response.raise_for_status()
            body = response.content
            ctype = response.headers.get("content-type", "").lower()
            if len(body) > MAX_BYTES:
                rec.update({"status": response.status_code, "size_bytes": len(body), "error": "size_limit"})
            elif not (body.startswith(b"%PDF-") or "application/pdf" in ctype):
                rec.update({"status": response.status_code, "content_type": ctype, "size_bytes": len(body), "error": "not_pdf"})
            else:
                raw = Path(urlparse(response.url).path).name or safe_name(title)
                name = safe_name(raw)
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                path = docs / f"{index:02d}_{name}"
                path.write_bytes(body)
                rec.update({
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": ctype,
                    "size_bytes": len(body),
                    "is_pdf": True,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "saved_path": str(path),
                    "text_extraction": extract(path, rendered / f"{index:02d}_{safe_name(title)}"),
                })
        except Exception as exc:
            rec["error"] = repr(exc)
        report["documents"].append(rec)
    pdf_count = sum(1 for row in report["documents"] if row.get("is_pdf"))
    report["pdf_count"] = pdf_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (out / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "pdf_count": pdf_count}, indent=2))
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
