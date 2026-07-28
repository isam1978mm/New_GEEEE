"""Focused official-record recovery for SLAPS measured-depth screening.

Downloads only the decisive USACE design, phase, grading, and final-status survey
records. Extracts text and page snippets for excavation depths, final grading,
backfill/restoration, coordinate control, survey accuracy, and infrastructure.
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

BASE = "https://www.mvs.usace.army.mil/Portals/54/docs/fusrap/Admin_Records/NORCO/"
DOCUMENTS = {
    "Site-wide design analysis": BASE + "NCountySites_02.04_0031_a.PDF",
    "Phase 1 work description": BASE + "NCountySites_02.04_0030_a.PDF",
    "Phases 2 and 3 work description": BASE + "NCountySites_02.04_0033_a.PDF",
    "Phases 4 5 and 6 design basis": BASE + "NCountySites_02.04_0035_a.PDF",
    "Site grading and drainage plan": BASE + "NCountySites_02.04_0041_a.PDF",
    "Phases 4 and 5 work description": BASE + "NCountySites_02.04_0042_a.PDF",
    "Phase 6 work description": BASE + "NCountySites_02.04_0043_a.PDF",
    "Radiological final status survey plan": BASE + "NCountySites_02.04_0075_a.PDF",
    "SLAPS implementation report": BASE + "NCountySites_03.10_0009_a.PDF",
    "Phases 4 5 6 pre-design investigation": BASE + "NCountySites_02.13_0004_a.PDF",
}
KEYWORDS = (
    "excavation depth", "depth of excavation", "excavation contour",
    "excavation surface", "cut surface", "final excavation", "as-built",
    "as built", "final grade", "final grading", "backfill", "restoration",
    "topsoil", "vegetation", "hydroseed", "seed", "survey coordinate",
    "northing", "easting", "horizontal accuracy", "vertical accuracy",
    "survey tolerance", "precision", "uncertainty", "survey unit",
    "rail spur", "sedimentation basin", "drainage", "monitoring well",
    "berm", "slope", "coldwater creek", "three-foot grid", "3-foot grid",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/pdf,*/*",
}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:180] or "document"


def extract(path: Path) -> dict[str, object]:
    txt = path.with_suffix(".txt")
    proc = subprocess.run(
        ["pdftotext", "-layout", str(path), str(txt)],
        capture_output=True, text=True, check=False,
    )
    text = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
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
            "snippet": "\n".join(selected)[:32000],
        })
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr[-4000:],
        "text_path": str(txt),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "slaps_cap_depth_records_fast"
    docs = out / "documents"
    docs.mkdir(parents=True, exist_ok=True)
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
        record: dict[str, object] = {"title": title, "requested_url": url}
        try:
            response = session.get(url, headers=HEADERS, timeout=(45, 300), allow_redirects=True)
            response.raise_for_status()
            body = response.content
            ctype = response.headers.get("content-type", "").lower()
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in ctype
            if not is_pdf:
                record.update({"status": response.status_code, "content_type": ctype, "size_bytes": len(body), "error": "not_pdf"})
            else:
                name = safe_name(Path(urlparse(response.url).path).name)
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                path = docs / f"{index:02d}_{name}"
                path.write_bytes(body)
                record.update({
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": ctype,
                    "size_bytes": len(body),
                    "is_pdf": True,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "saved_path": str(path),
                    "text_extraction": extract(path),
                })
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)
    pdf_count = sum(1 for row in report["documents"] if row.get("is_pdf"))
    match_pages = sum(
        len(row.get("text_extraction", {}).get("matches", []))
        for row in report["documents"]
        if isinstance(row.get("text_extraction"), dict)
    )
    report.update({
        "pdf_count": pdf_count,
        "match_page_count": match_pages,
        "status": "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED",
    })
    (out / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "pdf_count": pdf_count, "match_page_count": match_pages}, indent=2))
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
