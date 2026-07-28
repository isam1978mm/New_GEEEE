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

PDF_URL = (
    "https://www.nan.usace.army.mil/Portals/37/docs/civilworks/projects/nj/fusrap/"
    "Middlesex%20Sampling/MSP_Final_Prar_9_8_2010_complete.pdf"
    "?ver=xkMcDgp6X07owwtb3l_MhQ%3D%3D"
)
PDF_PATH = OUT / "MSP_Final_PRAR_2010.pdf"
TEXT_PATH = OUT / "MSP_Final_PRAR_2010.txt"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; public-record evidence recovery)",
    "Accept": "application/pdf,*/*;q=0.8",
})
response = session.get(PDF_URL, timeout=180)
response.raise_for_status()
PDF_PATH.write_bytes(response.content)

subprocess.run(["pdftotext", "-layout", str(PDF_PATH), str(TEXT_PATH)], check=True)
text = TEXT_PATH.read_text(encoding="utf-8", errors="replace")

patterns = [
    r"as[- ]built",
    r"excavat(?:ion|ed).*?(?:depth|elevation|grade)",
    r"final (?:grade|survey|elevation|contour)",
    r"topsoil|seed(?:ed|ing)?|vegetat(?:e|ed|ion)",
    r"survey|coordinate|northing|easting|accuracy|tolerance",
    r"backfill|clean fill|restor(?:e|ed|ation)",
]

hits: list[dict[str, object]] = []
lines = text.splitlines()
for index, line in enumerate(lines):
    lowered = line.lower()
    if any(re.search(pattern, lowered) for pattern in patterns):
        start = max(0, index - 2)
        end = min(len(lines), index + 3)
        hits.append({"line": index + 1, "context": lines[start:end]})

report = {
    "source_url": PDF_URL,
    "pdf_bytes": len(response.content),
    "text_lines": len(lines),
    "keyword_hit_count": len(hits),
    "keyword_hits": hits[:600],
    "safety": {
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    },
}
(OUT / "recovery_report.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(json.dumps({k: report[k] for k in ("pdf_bytes", "text_lines", "keyword_hit_count")}, indent=2))
