#!/usr/bin/env python3
"""Recover the primary 1994 Syncrude oil-sands tailings capping report.

Public technical records only. No Earth Engine request, calibration row, model
training, or app-depth change is performed.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

OUT = Path("artifacts/syncrude_1990_capping_study")
OUT.mkdir(parents=True, exist_ok=True)

URLS = [
    "https://era.library.ualberta.ca/items/00e3e5a6-dc96-4c9a-879b-3c62950cd579/view/d0b41245-7cf3-4c10-bb86-55dd40e12b2e/RRTAC-20OF-6-20Oil-20sands-20tailings-20capping-20study.pdf",
    "https://era.library.ualberta.ca/items/00e3e5a6-dc96-4c9a-879b-3c62950cd579/view/d0b41245-7cf3-4c10-bb86-55dd40e12b2e/RRTAC-20OF-6-20Oil-20sands-20tailings-20capping-20study.pdf?download=1",
    "https://era.library.ualberta.ca/public/view/item/uuid:00e3e5a6-dc96-4c9a-879b-3c62950cd579",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
    "Referer": "https://era.library.ualberta.ca/items/00e3e5a6-dc96-4c9a-879b-3c62950cd579",
})

attempts: list[dict[str, object]] = []
response = None
for url in URLS:
    candidate = session.get(url, timeout=240, allow_redirects=True)
    is_pdf = candidate.content.startswith(b"%PDF-")
    attempts.append({
        "url": url,
        "final_url": candidate.url,
        "status_code": candidate.status_code,
        "content_type": candidate.headers.get("content-type"),
        "bytes": len(candidate.content),
        "body_is_pdf": is_pdf,
    })
    if is_pdf:
        response = candidate
        break

(OUT / "transport_report.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
if response is None:
    # Preserve the last response for diagnosis.
    if attempts:
        (OUT / "last_response.bin").write_bytes(candidate.content)
    raise RuntimeError("No verified PDF body recovered from ERA endpoints")

pdf_path = OUT / "oil_sands_tailings_capping_study_1994.pdf"
text_path = OUT / "oil_sands_tailings_capping_study_1994.txt"
pdf_path.write_bytes(response.content)
subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], check=True)
info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True).stdout
match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
page_count = int(match.group(1)) if match else 0

keywords = re.compile(
    r"plot|dimension|metre|meter|feet|acre|hectare|thickness|depth|cap|"
    r"as[- ]built|constructed|placement|control|sample|survey|coordinate|"
    r"northing|easting|accuracy|tolerance|standard deviation|confidence|"
    r"seedling|planting|vegetation|figure|table|layout|map",
    re.IGNORECASE,
)

page_hits: list[dict[str, object]] = []
pages = OUT / "pages"
pages.mkdir(exist_ok=True)
for page in range(1, page_count + 1):
    page_txt = pages / f"page-{page:04d}.txt"
    subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf_path), str(page_txt)],
        check=True,
    )
    text = page_txt.read_text(encoding="utf-8", errors="replace")
    hits = [line.strip() for line in text.splitlines() if keywords.search(line)]
    if hits:
        page_hits.append({"page": page, "hits": hits[:140]})

scored: list[tuple[int, int]] = []
for item in page_hits:
    page = int(item["page"])
    joined = " ".join(str(v) for v in item["hits"]).lower()
    score = len(item["hits"])
    for term in (
        "plot layout", "plot size", "thickness", "placement", "good control",
        "survey", "coordinate", "standard deviation", "table", "figure",
    ):
        if term in joined:
            score += 20
    scored.append((score, page))
selected = sorted({page for _, page in sorted(scored, reverse=True)[:25]})
rendered = OUT / "rendered"
rendered.mkdir(exist_ok=True)
for page in selected:
    subprocess.run(
        [
            "pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "180",
            str(pdf_path), str(rendered / f"page-{page:04d}"),
        ],
        check=True,
    )

report = {
    "source_url": response.url,
    "status_code": response.status_code,
    "pdf_bytes": len(response.content),
    "page_count": page_count,
    "keyword_pages": page_hits,
    "selected_render_pages": selected,
    "safety": {
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    },
}
(OUT / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({
    "status_code": response.status_code,
    "pdf_bytes": len(response.content),
    "page_count": page_count,
    "selected_render_pages": selected,
}, indent=2))
