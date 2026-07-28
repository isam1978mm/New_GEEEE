#!/usr/bin/env python3
"""Recover the official Middlesex Sampling Plant OU1 PRAR for evidence screening.

Public environmental records only. This script does not call Earth Engine, create
calibration rows, train a model, or change app behavior.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

OUT = Path("artifacts/middlesex_sampling_prar")
OUT.mkdir(parents=True, exist_ok=True)
PAGES = OUT / "pages"
PAGES.mkdir(exist_ok=True)

PDF_URLS = [
    (
        "https://www.nan.usace.army.mil/Portals/37/docs/civilworks/projects/nj/fusrap/"
        "Middlesex%20Sampling/MSP_Final_Prar_9_8_2010_complete.pdf"
        "?ver=xkMcDgp6X07owwtb3l_MhQ%3D%3D"
    ),
    (
        "https://www.nan.usace.army.mil/Portals/37/docs/civilworks/projects/nj/fusrap/"
        "Middlesex%20Sampling/MSP_Final_Prar_9_8_2010_complete.pdf"
    ),
]
PDF_PATH = OUT / "MSP_Final_PRAR_2010.pdf"
TEXT_PATH = OUT / "MSP_Final_PRAR_2010.txt"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; public-record evidence recovery)",
    "Accept": "application/pdf,*/*;q=0.8",
})

attempts: list[dict[str, object]] = []
response = None
for url in PDF_URLS:
    candidate = session.get(url, timeout=240, allow_redirects=True)
    body_is_pdf = candidate.content.startswith(b"%PDF-")
    attempts.append({
        "url": url,
        "final_url": candidate.url,
        "status_code": candidate.status_code,
        "content_type": candidate.headers.get("content-type"),
        "bytes": len(candidate.content),
        "body_is_pdf": body_is_pdf,
    })
    if body_is_pdf:
        response = candidate
        break

(OUT / "transport_report.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
if response is None:
    raise RuntimeError("USACE responses did not contain a verified PDF body")
PDF_PATH.write_bytes(response.content)

subprocess.run(["pdftotext", "-layout", str(PDF_PATH), str(TEXT_PATH)], check=True)
info = subprocess.run(["pdfinfo", str(PDF_PATH)], check=True, capture_output=True, text=True).stdout
match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
page_count = int(match.group(1)) if match else 0

keywords = re.compile(
    r"as[- ]built|excavat(?:ion|ed)|final (?:grade|survey|elevation|contour)|"
    r"topsoil|seed(?:ed|ing)?|vegetat(?:e|ed|ion)|survey|coordinate|northing|"
    r"easting|accuracy|tolerance|backfill|clean fill|restor(?:e|ed|ation)|"
    r"depth|thickness|figure|drawing",
    re.IGNORECASE,
)

page_results: list[dict[str, object]] = []
for page in range(1, page_count + 1):
    page_txt = PAGES / f"page-{page:04d}.txt"
    subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(PDF_PATH), str(page_txt)],
        check=True,
    )
    text = page_txt.read_text(encoding="utf-8", errors="replace")
    matches = [line.strip() for line in text.splitlines() if keywords.search(line)]
    if matches:
        page_results.append({"page": page, "matches": matches[:80]})

scored: list[tuple[int, int]] = []
for item in page_results:
    page = int(item["page"])
    matches = item["matches"]
    score = len(matches)
    joined = " ".join(str(value) for value in matches).lower()
    for term in ("as-built", "final survey", "excavation depth", "final grade", "restoration", "figure", "drawing"):
        if term in joined:
            score += 12
    scored.append((score, page))
selected_pages = sorted({page for _, page in sorted(scored, reverse=True)[:30]})
rendered = OUT / "rendered"
rendered.mkdir(exist_ok=True)
for page in selected_pages:
    prefix = rendered / f"page-{page:04d}"
    subprocess.run(
        ["pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "140", str(PDF_PATH), str(prefix)],
        check=True,
    )

report = {
    "source_url": response.url,
    "http_status_code": response.status_code,
    "pdf_bytes": len(response.content),
    "page_count": page_count,
    "keyword_pages": page_results,
    "selected_render_pages": selected_pages,
    "safety": {
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    },
}
(OUT / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"http_status_code": response.status_code, "pdf_bytes": report["pdf_bytes"], "page_count": page_count, "keyword_page_count": len(page_results), "rendered_pages": selected_pages}, indent=2))
