#!/usr/bin/env python3
"""Research-only inspection of official Tyrone 2007 Appendix A design drawings.

Downloads the public EMNRD PDF and extracts any existing text layer. Searches for
3X / grade / subgrade / profiles and writes a small evidence JSON. No production
code or depth calculations are touched.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

URL = "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/GR010RE_20071011_Closeout_Plan_Update_AppendixA_Design_Drawings.pdf"
OUT = Path("artifacts/tyrone_appendixa_3x_check")
OUT.mkdir(parents=True, exist_ok=True)
PDF = OUT / "appendix_a_design_drawings.pdf"
TXT = OUT / "appendix_a_design_drawings.txt"
TERMS = [
    "3X",
    "existing grade",
    "proposed grade",
    "final grade",
    "subgrade",
    "profile",
    "section",
    "grading",
    "tailing impoundment",
]


def main():
    r = requests.get(URL, timeout=180)
    r.raise_for_status()
    PDF.write_bytes(r.content)
    subprocess.run(["pdftotext", "-layout", str(PDF), str(TXT)], check=True)
    text = TXT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for idx, line in enumerate(lines):
        low = line.lower()
        matched = [t for t in TERMS if t.lower() in low]
        if matched:
            lo = max(0, idx - 2)
            hi = min(len(lines), idx + 3)
            hits.append({
                "line_number": idx + 1,
                "matched_terms": matched,
                "context": "\n".join(lines[lo:hi]),
            })
    result = {
        "status": "TYRONE_APPENDIX_A_TEXT_CHECK_COMPLETE",
        "source_url": URL,
        "http_status": r.status_code,
        "pdf_bytes": len(r.content),
        "text_chars": len(text),
        "page_count": None,
        "term_hit_counts": {t: sum(1 for h in hits if t in h["matched_terms"]) for t in TERMS},
        "hits": hits[:500],
        "production_code_modified": False,
        "depth_calculated": False,
        "paid_action_attempted": False,
    }
    try:
        info = subprocess.check_output(["pdfinfo", str(PDF)], text=True, errors="replace")
        m = re.search(r"^Pages:\s+(\d+)", info, re.M)
        if m:
            result["page_count"] = int(m.group(1))
    except Exception:
        pass
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
