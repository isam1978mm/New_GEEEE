#!/usr/bin/env python3
"""Recover primary Detour Lake Mine cover-trial construction and monitoring records.

Public technical records only. No Earth Engine request, calibration row, model
training, or app-depth change is performed.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

OUT = Path("artifacts/detour_lake_cover_trial_records")
OUT.mkdir(parents=True, exist_ok=True)

DOCS = {
    "2022_design_construction": [
        "https://open.library.ubc.ca/media/stream/pdf/59367/1.0421799/5",
        "https://open.library.ubc.ca/media/download/pdf/59367/1.0421799/5",
    ],
    "2025_five_year_review": [
        "https://papers.acg.uwa.edu.au/d/2515_98_Cash/98_Cash.pdf",
    ],
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; public technical evidence recovery)",
    "Accept": "application/pdf,*/*;q=0.8",
})

keyword_re = re.compile(
    r"as[- ]built|cover thickness|thickness|plot|sub[- ]plot|treatment|"
    r"coordinate|northing|easting|survey|accuracy|tolerance|dimension|"
    r"hectare|metre|meter|reveget|seed|plant|peat|grading|ripping|"
    r"erosion|gully|sinkhole|repair|test pit|disturb|Figure|Table",
    re.IGNORECASE,
)

inventory: list[dict[str, object]] = []
for name, urls in DOCS.items():
    doc_dir = OUT / name
    doc_dir.mkdir(exist_ok=True)
    attempts: list[dict[str, object]] = []
    response = None
    for url in urls:
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
    (doc_dir / "transport_report.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
    entry: dict[str, object] = {"name": name, "attempts": attempts, "body_is_pdf": response is not None}
    if response is None:
        inventory.append(entry)
        continue

    pdf_path = doc_dir / f"{name}.pdf"
    text_path = doc_dir / f"{name}.txt"
    pdf_path.write_bytes(response.content)
    subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], check=True)
    info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    page_count = int(match.group(1)) if match else 0
    entry.update({
        "source_url": response.url,
        "status_code": response.status_code,
        "pdf_bytes": len(response.content),
        "page_count": page_count,
    })

    page_hits: list[dict[str, object]] = []
    pages = doc_dir / "pages"
    pages.mkdir(exist_ok=True)
    for page in range(1, page_count + 1):
        page_txt = pages / f"page-{page:04d}.txt"
        subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf_path), str(page_txt)],
            check=True,
        )
        text = page_txt.read_text(encoding="utf-8", errors="replace")
        hits = [line.strip() for line in text.splitlines() if keyword_re.search(line)]
        if hits:
            page_hits.append({"page": page, "hits": hits[:120]})
    entry["keyword_pages"] = page_hits

    scored: list[tuple[int, int]] = []
    for item in page_hits:
        page = int(item["page"])
        joined = " ".join(str(v) for v in item["hits"]).lower()
        score = len(item["hits"])
        for term in (
            "as-built", "cover thickness", "plot", "design drawing", "survey",
            "dimension", "0.3 m", "0.7 m", "1.0 m", "peat", "test pit",
            "erosion", "sinkhole", "repair",
        ):
            if term in joined:
                score += 18
        scored.append((score, page))
    selected = sorted({page for _, page in sorted(scored, reverse=True)[:25]})
    entry["selected_render_pages"] = selected
    rendered = doc_dir / "rendered"
    rendered.mkdir(exist_ok=True)
    for page in selected:
        subprocess.run(
            [
                "pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "170",
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
print(json.dumps({
    "documents": [
        {
            "name": item["name"],
            "body_is_pdf": item["body_is_pdf"],
            "page_count": item.get("page_count"),
            "selected_render_pages": item.get("selected_render_pages"),
        }
        for item in inventory
    ]
}, indent=2))
