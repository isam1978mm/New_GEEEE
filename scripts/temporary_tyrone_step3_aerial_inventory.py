#!/usr/bin/env python3
"""Temporary research-only Tyrone aerial-photo inventory probe.

Loads the public EarthExplorer predefined search for AERIAL_COMBIN at Tyrone 3X,
then inspects EarthExplorer's own public JavaScript for the AJAX endpoints used
to populate datasets/results. No imagery or depth is downloaded/calculated.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse

import requests

OUT = Path("artifacts/tyrone_step3_aerial_inventory")
OUT.mkdir(parents=True, exist_ok=True)
POINT = [32.7215, -108.4193]
BASE = "https://earthexplorer.usgs.gov/criteria"
params = {"node": "EE", "dataset_name": "AERIAL_COMBIN", "aoiFilter": json.dumps([POINT], separators=(",", ":"))}
URL = BASE + "?" + urlencode(params)


def compact(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def nearby(text: str, needle: str, radius: int = 500, limit: int = 30):
    out = []
    for m in re.finditer(needle, text, re.I):
        s = compact(text[max(0, m.start()-radius):min(len(text), m.end()+radius)])
        if s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def main() -> int:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 Tyrone-research/1.0"})
    r = s.get(URL, timeout=120, allow_redirects=True)
    r.raise_for_status()
    html = r.text
    (OUT / "earthexplorer_predefined_response.html").write_text(html, encoding="utf-8")

    script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I)
    same_origin = []
    js_docs = {}
    for src in script_srcs:
        full = urljoin(r.url, src)
        if urlparse(full).netloc != "earthexplorer.usgs.gov":
            continue
        try:
            jr = s.get(full, timeout=120)
            rec = {"url": full, "status": jr.status_code, "chars": len(jr.text)}
            same_origin.append(rec)
            if jr.ok and "javascript" in jr.headers.get("content-type", "").lower() or (jr.ok and full.split("?")[0].endswith(".js")):
                name = re.sub(r"[^A-Za-z0-9_.-]+", "_", urlparse(full).path.strip("/")) or "root.js"
                (OUT / name).write_text(jr.text, encoding="utf-8")
                js_docs[full] = jr.text
        except Exception as exc:
            same_origin.append({"url": full, "error": type(exc).__name__ + ": " + str(exc)})

    combined = "\n\n".join(js_docs.values())
    # Literal local paths and URL strings appearing around AJAX/fetch calls.
    literal_paths = sorted(set(re.findall(r"[\"'](/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+(?:\?[^\"']*)?)[\"']", combined)))
    ajax_snips = nearby(combined, r"\$\.ajax|\.ajax\(|fetch\(|XMLHttpRequest|url\s*:", radius=650, limit=150)
    key_snips = {}
    for key in ["search-results", "show_search_data", "activeDataSet", "dataset", "scene", "result", "metadata", "criteria", "search"]:
        x = nearby(combined, key, radius=450, limit=40)
        if x:
            key_snips[key] = x

    active_dataset = None
    m = re.search(r'id=["\']activeDataSet["\'][^>]*value=["\']([^"\']+)', html, re.I)
    if m:
        active_dataset = m.group(1)

    diag = {
        "status": "STEP3_EARTHEXPLORER_FRONTEND_TRACED",
        "request_url": URL,
        "http_status": r.status_code,
        "final_url": r.url,
        "active_dataset_internal_id": active_dataset,
        "coordinate_loaded": ("32.7215" in html and "-108.4193" in html),
        "summary_says_no_dataset": "No data sets selected" in html,
        "same_origin_scripts": same_origin,
        "literal_local_paths": literal_paths,
        "ajax_snippets": ajax_snips,
        "key_snippets": key_snips,
        "imagery_downloaded": False,
        "depth_calculated": False,
        "production_code_modified": False,
    }
    (OUT / "frontend_trace.json").write_text(json.dumps(diag, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diag, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
