"""Recover official Plattsburgh AFB landfill completion records for evidence review.

This temporary script downloads only public NYSDEC records relevant to LF-022 and
LF-023. It does not call Earth Engine, create calibration rows, train a model, or
enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://extapps.dec.ny.gov/data/DecDocs/510003/"
DOCUMENTS = {
    "final_construction_cert_vol3": "Report.HW.510003.2000-05-30.OHM_FinalConstructionCert_Vol3.pdf",
    "five_year_review_2009": "Report.HW.510003.2009-11-19.EPA_5_Year_Review.pdf",
    "lf022_rod": "ROD.HW.510003.1992-09-01.plattsburgh_afb_draft_ou1_LF-22.pdf",
    "lf023_rod": "ROD.HW.510003.1992-09-01.plattsburgh_afb_ou2_LF-23_source.pdf",
}


def download(url: str, destination: Path) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            "Accept": "application/pdf,*/*",
        },
    )
    with urlopen(request, timeout=300) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "")
    destination.write_bytes(data)
    return {
        "url": url,
        "path": str(destination),
        "size_bytes": len(data),
        "content_type": content_type,
        "is_pdf": data.startswith(b"%PDF-"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def extract_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    process = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "text_path": str(text_path),
        "text_size_bytes": text_path.stat().st_size if text_path.exists() else 0,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "plattsburgh_landfill_pair"
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "documents": [],
        "approved_scope": {
            "full_scale_vegetated_cover_only": True,
            "required_clean_width_m": "30-40 after exclusions",
            "coordinate_tied_measured_depths_required": True,
            "matching_near_surface_construction_required": True,
            "stable_sentinel1_period_required": True,
            "plan_changed": False,
        },
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    failures = 0
    for key, filename in DOCUMENTS.items():
        url = BASE + filename
        destination = output / f"{key}.pdf"
        item: dict[str, object] = {"key": key, "filename": filename}
        try:
            item.update(download(url, destination))
            if not item["is_pdf"]:
                failures += 1
                item["error"] = "Downloaded response is not a PDF"
            else:
                item["text_extraction"] = extract_text(destination)
        except Exception as exc:
            failures += 1
            item["error"] = repr(exc)
        report["documents"].append(item)

    report["status"] = "RECOVERED" if failures == 0 else "PARTIAL_OR_FAILED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
