#!/usr/bin/env python3
"""Recover official Little Rock/Tyrone USNR cover-test records.

Public environmental records only. No Earth Engine, calibration rows, training,
or app-depth changes are performed.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

OUT = Path("artifacts/little_rock_usnr_cover_records")
OUT.mkdir(parents=True, exist_ok=True)

DOCS = {
    "2017_as_built": "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/12380014_USNR_Test_Plot_As-Built_Rpt_F_20170308.pdf",
    "2018_annual": "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/20180430-100_Tyrone_USNR_Annual_Report_2.pdf",
    "2019_annual": "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/12380014-R-Rev0-USNR_AnnRpt_2018-20190425.pdf",
    "2020_annual": "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/19122576-002-R-Rev0-USNR_AnnRpt_2020_04282021_unlocked.pdf",
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; public-record evidence recovery)",
    "Accept": "application/pdf,*/*;q=0.8",
})

keyword_re = re.compile(
    r"cover thickness|thickness|as[- ]built|test plot|treatment|plot [0-9]|"
    r"coordinate|northing|easting|survey|accuracy|tolerance|dimension|acre|"
    r"reveget|seed|erosion|repair|subsidence|disturb|instrument|lysimeter|"
    r"figure|drawing|plate|depth",
    re.IGNORECASE,
)

inventory: list[dict[str, object]] = []
for name, url in DOCS.items():
    doc_dir = OUT / name
    doc_dir.mkdir(exist_ok=True)
    pdf_path = doc_dir / f"{name}.pdf"
    text_path = doc_dir / f"{name}.txt"
    response = session.get(url, timeout=240, allow_redirects=True)
    body_is_pdf = response.content.startswith(b"%PDF-")
    entry: dict[str, object] = {
        "name": name,
        "url": url,
        "final_url": response.url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(response.content),
        "body_is_pdf": body_is_pdf,
    }
    if not body_is_pdf:
        (doc_dir / "response_body.bin").write_bytes(response.content)
        inventory.append(entry)
        continue
    pdf_path.write_bytes(response.content)
    subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], check=True)
    info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    page_count = int(match.group(1)) if match else 0
    entry["page_count"] = page_count

    page_hits: list[dict[str, object]] = []
    page_dir = doc_dir / "pages"
    page_dir.mkdir(exist_ok=True)
    for page in range(1, page_count + 1):
        page_txt = page_dir / f"page-{page:04d}.txt"
        subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf_path), str(page_txt)],
            check=True,
        )
        text = page_txt.read_text(encoding="utf-8", errors="replace")
        hits = [line.strip() for line in text.splitlines() if keyword_re.search(line)]
        if hits:
            page_hits.append({"page": page, "hits": hits[:100]})
    entry["keyword_pages"] = page_hits

    scored: list[tuple[int, int]] = []
    for item in page_hits:
        page = int(item["page"])
        joined = " ".join(str(v) for v in item["hits"]).lower()
        score = len(item["hits"])
        for term in (
            "as-built", "cover thickness", "northing", "easting", "survey",
            "test plot", "treatment", "figure", "drawing", "repair", "erosion",
        ):
            if term in joined:
                score += 15
        scored.append((score, page))
    selected = sorted({page for _, page in sorted(scored, reverse=True)[:35]})
    entry["selected_render_pages"] = selected
    rendered = doc_dir / "rendered"
    rendered.mkdir(exist_ok=True)
    for page in selected:
        subprocess.run(
            [
                "pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "140",
                str(pdf_path), str(rendered / f"page-{page:04d}"),
            ],
            check=True,
        )
    inventory.append(entry)

report = {
    "documents": inventory,
    "safety": {
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    },
}
(OUT / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"documents": [{"name": d["name"], "status_code": d["status_code"], "body_is_pdf": d["body_is_pdf"], "page_count": d.get("page_count")} for d in inventory]}, indent=2))
