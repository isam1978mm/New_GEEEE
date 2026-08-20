#!/usr/bin/env python3
"""Temporary research-only Tyrone aerial-photo inventory probe.

Uses the official EarthExplorer predefined-link mechanism for dataset alias
AERIAL_COMBIN (Aerial Photo Single Frames) at the Tyrone 3X point. Saves only
HTML/search diagnostics; no imagery, depth, model, or production code is used.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode

import requests

OUT = Path("artifacts/tyrone_step3_aerial_inventory")
OUT.mkdir(parents=True, exist_ok=True)
POINT = [32.7215, -108.4193]
BASE = "https://earthexplorer.usgs.gov/criteria"
params = {
    "node": "EE",
    "dataset_name": "AERIAL_COMBIN",
    "aoiFilter": json.dumps([POINT], separators=(",", ":")),
}
URL = BASE + "?" + urlencode(params)


def snippets(text: str, pattern: str, radius: int = 350):
    out = []
    for m in re.finditer(pattern, text, re.I):
        a = max(0, m.start() - radius)
        b = min(len(text), m.end() + radius)
        s = re.sub(r"\s+", " ", text[a:b])
        if s not in out:
            out.append(s)
        if len(out) >= 20:
            break
    return out


def main() -> int:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 Tyrone-research/1.0"})
    r = s.get(URL, timeout=120, allow_redirects=True)
    r.raise_for_status()
    text = r.text
    (OUT / "earthexplorer_predefined_response.html").write_text(text, encoding="utf-8")

    patterns = [
        "AERIAL_COMBIN", "Aerial Photo Single Frames", "32.7215", "-108.4193",
        "result", "entity", "dataset", "scene", "search", "api", "ajax",
        "acquisition", "frame", "roll", "stereo", "2004",
    ]
    diag = {
        "status": "STEP3_EARTHEXPLORER_PREDEFINED_PROBED",
        "request_url": URL,
        "http_status": r.status_code,
        "final_url": r.url,
        "html_chars": len(text),
        "cookies": sorted(s.cookies.keys()),
        "pattern_counts": {p: len(re.findall(p, text, re.I)) for p in patterns},
        "snippets": {p: snippets(text, p) for p in patterns if re.search(p, text, re.I)},
        "links_or_endpoints": sorted(set(re.findall(r"(?:https?://[^\"'<> ]+|/[A-Za-z0-9_./?=&%-]{4,})", text)))[:500],
        "imagery_downloaded": False,
        "depth_calculated": False,
        "production_code_modified": False,
    }
    (OUT / "predefined_diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diag, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
