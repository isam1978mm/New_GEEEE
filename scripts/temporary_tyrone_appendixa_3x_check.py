#!/usr/bin/env python3
"""Research-only visual inspection package for official Tyrone Appendix A drawings.

Downloads the public 2007 Appendix A PDF, records its sparse text layer, and
renders all pages into contact sheets for manual visual inspection. No OCR,
production code, depth calculation, purchase, order, or payment is used.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw

URL = "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/GR010RE_20071011_Closeout_Plan_Update_AppendixA_Design_Drawings.pdf"
OUT = Path("artifacts/tyrone_appendixa_3x_check")
PAGES = OUT / "pages"
OUT.mkdir(parents=True, exist_ok=True)
PAGES.mkdir(parents=True, exist_ok=True)
PDF = OUT / "appendix_a_design_drawings.pdf"
TXT = OUT / "appendix_a_design_drawings.txt"
TERMS = ["3X", "existing grade", "proposed grade", "final grade", "subgrade", "profile", "section", "grading", "tailing impoundment"]


def main():
    r = requests.get(URL, timeout=180)
    r.raise_for_status()
    PDF.write_bytes(r.content)
    subprocess.run(["pdftotext", "-layout", str(PDF), str(TXT)], check=True)
    text = TXT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for idx, line in enumerate(lines):
        matched = [t for t in TERMS if t.lower() in line.lower()]
        if matched:
            hits.append({"line_number": idx + 1, "matched_terms": matched, "context": "\n".join(lines[max(0, idx-2):min(len(lines), idx+3)])})

    info = subprocess.check_output(["pdfinfo", str(PDF)], text=True, errors="replace")
    m = re.search(r"^Pages:\s+(\d+)", info, re.M)
    page_count = int(m.group(1)) if m else None

    # Render scanned drawings at moderate resolution. This is for human title/content review, not OCR.
    subprocess.run(["pdftoppm", "-jpeg", "-r", "90", str(PDF), str(PAGES / "page")], check=True)
    page_files = sorted(PAGES.glob("page-*.jpg"))

    # Six pages per contact sheet, each thumbnail 900 px wide, with page labels.
    thumb_w = 900
    gap = 20
    label_h = 40
    per_sheet = 6
    contact_sheets = []
    for group_idx in range(math.ceil(len(page_files) / per_sheet)):
        group = page_files[group_idx*per_sheet:(group_idx+1)*per_sheet]
        thumbs = []
        for page_num, p in enumerate(group, start=group_idx*per_sheet + 1):
            im = Image.open(p).convert("RGB")
            h = max(1, round(im.height * thumb_w / im.width))
            im.thumbnail((thumb_w, h))
            thumbs.append((page_num, im.copy()))
        col_w = thumb_w
        row_heights = []
        for row in range(3):
            pair = thumbs[row*2:(row+1)*2]
            if pair:
                row_heights.append(max(im.height for _, im in pair) + label_h)
        sheet_w = 2*col_w + 3*gap
        sheet_h = sum(row_heights) + (len(row_heights)+1)*gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        draw = ImageDraw.Draw(sheet)
        y = gap
        for row in range(3):
            pair = thumbs[row*2:(row+1)*2]
            if not pair:
                break
            rh = row_heights[row]
            for col, (page_num, im) in enumerate(pair):
                x = gap + col*(col_w+gap)
                draw.text((x, y), f"PDF page {page_num}", fill="black")
                sheet.paste(im, (x, y+label_h))
            y += rh + gap
        out = OUT / f"contact_sheet_{group_idx+1:02d}.jpg"
        sheet.save(out, quality=88)
        contact_sheets.append(out.name)

    result = {
        "status": "TYRONE_APPENDIX_A_VISUAL_PACKAGE_COMPLETE",
        "source_url": URL,
        "http_status": r.status_code,
        "pdf_bytes": len(r.content),
        "text_chars": len(text),
        "page_count": page_count,
        "term_hit_counts": {t: sum(1 for h in hits if t in h["matched_terms"]) for t in TERMS},
        "hits": hits[:500],
        "contact_sheets": contact_sheets,
        "production_code_modified": False,
        "depth_calculated": False,
        "paid_action_attempted": False,
        "ocr_used": False,
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
