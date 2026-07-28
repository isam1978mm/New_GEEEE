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
from typing import Any

import requests

OUT = Path("artifacts/syncrude_1990_capping_study")
OUT.mkdir(parents=True, exist_ok=True)

OLD_ITEM = "00e3e5a6-dc96-4c9a-879b-3c62950cd579"
NEW_ITEM = "6f0a285b-9bab-443c-833f-9afb54588aae"
BASE = "https://ualberta.scholaris.ca"
DIRECT_URLS = [
    "https://era.library.ualberta.ca/items/00e3e5a6-dc96-4c9a-879b-3c62950cd579/view/d0b41245-7cf3-4c10-bb86-55dd40e12b2e/RRTAC-20OF-6-20Oil-20sands-20tailings-20capping-20study.pdf",
    "https://era.library.ualberta.ca/items/00e3e5a6-dc96-4c9a-879b-3c62950cd579/view/d0b41245-7cf3-4c10-bb86-55dd40e12b2e/RRTAC-20OF-6-20Oil-20sands-20tailings-20capping-20study.pdf?download=1",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/json,application/hal+json,application/pdf,text/html;q=0.8,*/*;q=0.5",
    "Referer": f"{BASE}/items/{NEW_ITEM}",
})

attempts: list[dict[str, Any]] = []
response: requests.Response | None = None


def record_attempt(kind: str, url: str, candidate: requests.Response) -> bool:
    is_pdf = candidate.content.startswith(b"%PDF-")
    attempts.append({
        "kind": kind,
        "url": url,
        "final_url": candidate.url,
        "status_code": candidate.status_code,
        "content_type": candidate.headers.get("content-type"),
        "bytes": len(candidate.content),
        "body_is_pdf": is_pdf,
    })
    return is_pdf


# 1. Preserve the original direct-link attempt and redirected item page.
for url in DIRECT_URLS:
    candidate = session.get(url, timeout=240, allow_redirects=True)
    if record_attempt("legacy_direct", url, candidate):
        response = candidate
        break
    if "scholaris.ca/items/" in candidate.url:
        (OUT / "scholaris_item_page.html").write_bytes(candidate.content)

# 2. Use the public DSpace REST API exposed by Scholaris.
api_report: dict[str, Any] = {}
if response is None:
    item_url = f"{BASE}/server/api/core/items/{NEW_ITEM}"
    item_resp = session.get(item_url, timeout=120)
    record_attempt("api_item", item_url, item_resp)
    try:
        item_json = item_resp.json()
    except Exception:
        item_json = None
    api_report["item"] = item_json if item_json is not None else {
        "status_code": item_resp.status_code,
        "body_prefix": item_resp.text[:500],
    }

    bundle_urls = [
        f"{BASE}/server/api/core/bundles/search/byItem?uuid={NEW_ITEM}",
        f"{BASE}/server/api/core/items/{NEW_ITEM}/bundles",
    ]
    bundle_records: list[dict[str, Any]] = []
    bundle_uuids: list[str] = []
    for bundle_url in bundle_urls:
        bundle_resp = session.get(bundle_url, timeout=120)
        record_attempt("api_bundles", bundle_url, bundle_resp)
        try:
            bundle_json = bundle_resp.json()
        except Exception:
            bundle_json = None
        bundle_records.append({"url": bundle_url, "json": bundle_json})
        if isinstance(bundle_json, dict):
            embedded = bundle_json.get("_embedded", {})
            bundles = embedded.get("bundles", []) if isinstance(embedded, dict) else []
            for bundle in bundles:
                if isinstance(bundle, dict) and bundle.get("uuid"):
                    bundle_uuids.append(str(bundle["uuid"]))
        if bundle_uuids:
            break
    api_report["bundles"] = bundle_records

    bitstream_records: list[dict[str, Any]] = []
    bitstream_candidates: list[dict[str, Any]] = []
    for bundle_uuid in dict.fromkeys(bundle_uuids):
        bit_urls = [
            f"{BASE}/server/api/core/bitstreams/search/byBundle?uuid={bundle_uuid}",
            f"{BASE}/server/api/core/bundles/{bundle_uuid}/bitstreams",
        ]
        for bit_url in bit_urls:
            bit_resp = session.get(bit_url, timeout=120)
            record_attempt("api_bitstreams", bit_url, bit_resp)
            try:
                bit_json = bit_resp.json()
            except Exception:
                bit_json = None
            bitstream_records.append({"url": bit_url, "json": bit_json})
            if isinstance(bit_json, dict):
                embedded = bit_json.get("_embedded", {})
                bitstreams = embedded.get("bitstreams", []) if isinstance(embedded, dict) else []
                for bitstream in bitstreams:
                    if isinstance(bitstream, dict) and bitstream.get("uuid"):
                        bitstream_candidates.append(bitstream)
            if bitstream_candidates:
                break
    api_report["bitstreams"] = bitstream_records

    # Prefer PDF-looking bitstreams, but test every public bitstream if names are opaque.
    ordered = sorted(
        bitstream_candidates,
        key=lambda b: (
            0 if str(b.get("name", "")).lower().endswith(".pdf") else 1,
            0 if "capping" in str(b.get("name", "")).lower() else 1,
        ),
    )
    for bitstream in ordered:
        uuid = str(bitstream.get("uuid"))
        content_urls = [
            f"{BASE}/server/api/core/bitstreams/{uuid}/content",
            f"{BASE}/server/api/core/bitstreams/{uuid}",
        ]
        for content_url in content_urls:
            content_resp = session.get(content_url, timeout=240, allow_redirects=True)
            if record_attempt("api_bitstream_content", content_url, content_resp):
                response = content_resp
                api_report["selected_bitstream"] = bitstream
                break
        if response is not None:
            break

(OUT / "transport_report.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
(OUT / "api_report.json").write_text(json.dumps(api_report, indent=2), encoding="utf-8")
if response is None:
    raise RuntimeError("No verified PDF body recovered from legacy or Scholaris API endpoints")

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
        page_hits.append({"page": page, "hits": hits[:160]})

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
