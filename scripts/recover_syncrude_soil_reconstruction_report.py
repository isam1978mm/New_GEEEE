#!/usr/bin/env python3
"""Recover the 1992 Syncrude Oil Sands Soil Reconstruction Project report.

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

OUT = Path("artifacts/syncrude_soil_reconstruction_report")
OUT.mkdir(parents=True, exist_ok=True)

OLD_ITEM = "97623d12-9b03-4765-ad4f-ccb6945c0b9b"
OLD_BITSTREAM = "5d1e30b0-0963-4569-bb49-fd013d494e18"
BASE = "https://ualberta.scholaris.ca"
LEGACY_URLS = [
    f"https://era.library.ualberta.ca/items/{OLD_ITEM}",
    f"https://era.library.ualberta.ca/items/{OLD_ITEM}/download/{OLD_BITSTREAM}",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/json,application/hal+json,application/pdf,text/html;q=0.8,*/*;q=0.5",
})

attempts: list[dict[str, Any]] = []
response: requests.Response | None = None
new_item: str | None = None


def record(kind: str, url: str, resp: requests.Response) -> bool:
    is_pdf = resp.content.startswith(b"%PDF-")
    attempts.append({
        "kind": kind,
        "url": url,
        "final_url": resp.url,
        "status_code": resp.status_code,
        "content_type": resp.headers.get("content-type"),
        "bytes": len(resp.content),
        "body_is_pdf": is_pdf,
    })
    return is_pdf


for url in LEGACY_URLS:
    resp = session.get(url, timeout=240, allow_redirects=True)
    if record("legacy", url, resp):
        response = resp
        break
    match = re.search(r"/items/([0-9a-f-]{36})", resp.url)
    if match and "scholaris.ca" in resp.url:
        new_item = match.group(1)
        (OUT / "scholaris_item_page.html").write_bytes(resp.content)

api_report: dict[str, Any] = {"new_item_uuid": new_item}
if response is None and new_item:
    item_url = f"{BASE}/server/api/core/items/{new_item}"
    item_resp = session.get(item_url, timeout=120)
    record("api_item", item_url, item_resp)
    try:
        api_report["item"] = item_resp.json()
    except Exception:
        api_report["item"] = {"body_prefix": item_resp.text[:500]}

    bundle_urls = [
        f"{BASE}/server/api/core/bundles/search/byItem?uuid={new_item}",
        f"{BASE}/server/api/core/items/{new_item}/bundles",
    ]
    bundle_uuids: list[str] = []
    api_report["bundle_responses"] = []
    for url in bundle_urls:
        resp = session.get(url, timeout=120)
        record("api_bundles", url, resp)
        try:
            data = resp.json()
        except Exception:
            data = None
        api_report["bundle_responses"].append({"url": url, "json": data})
        if isinstance(data, dict):
            embedded = data.get("_embedded", {})
            for bundle in embedded.get("bundles", []) if isinstance(embedded, dict) else []:
                if isinstance(bundle, dict) and bundle.get("uuid"):
                    bundle_uuids.append(str(bundle["uuid"]))
        if bundle_uuids:
            break

    bitstreams: list[dict[str, Any]] = []
    api_report["bitstream_responses"] = []
    for bundle_uuid in dict.fromkeys(bundle_uuids):
        urls = [
            f"{BASE}/server/api/core/bitstreams/search/byBundle?uuid={bundle_uuid}",
            f"{BASE}/server/api/core/bundles/{bundle_uuid}/bitstreams",
        ]
        for url in urls:
            resp = session.get(url, timeout=120)
            record("api_bitstreams", url, resp)
            try:
                data = resp.json()
            except Exception:
                data = None
            api_report["bitstream_responses"].append({"url": url, "json": data})
            if isinstance(data, dict):
                embedded = data.get("_embedded", {})
                for bitstream in embedded.get("bitstreams", []) if isinstance(embedded, dict) else []:
                    if isinstance(bitstream, dict) and bitstream.get("uuid"):
                        bitstreams.append(bitstream)
            if bitstreams:
                break

    ordered = sorted(
        bitstreams,
        key=lambda b: (
            0 if str(b.get("name", "")).lower().endswith(".pdf") else 1,
            0 if "reconstruction" in str(b.get("name", "")).lower() else 1,
        ),
    )
    for bitstream in ordered:
        uuid = str(bitstream["uuid"])
        url = f"{BASE}/server/api/core/bitstreams/{uuid}/content"
        resp = session.get(url, timeout=300, allow_redirects=True)
        if record("api_bitstream_content", url, resp):
            response = resp
            api_report["selected_bitstream"] = bitstream
            break

(OUT / "transport_report.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
(OUT / "api_report.json").write_text(json.dumps(api_report, indent=2), encoding="utf-8")
if response is None:
    raise RuntimeError("No verified PDF body recovered")

pdf_path = OUT / "oil_sands_soil_reconstruction_five_year_summary_1992.pdf"
text_path = OUT / "oil_sands_soil_reconstruction_five_year_summary_1992.txt"
pdf_path.write_bytes(response.content)
subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], check=True)
info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True).stdout
match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
page_count = int(match.group(1)) if match else 0

keywords = re.compile(
    r"plot|layout|dimension|metre|meter|acre|hectare|20 cm|40 cm|thickness|depth|"
    r"constructed|as[- ]built|measurement|survey|coordinate|northing|easting|"
    r"accuracy|tolerance|standard deviation|standard error|confidence|"
    r"peat|overburden|tailings sand|vegetation|planting|figure|table",
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
        page_hits.append({"page": page, "hits": hits[:180]})

scored: list[tuple[int, int]] = []
for item in page_hits:
    page = int(item["page"])
    joined = " ".join(str(v) for v in item["hits"]).lower()
    score = len(item["hits"])
    for term in (
        "plot layout", "plot dimension", "20 cm", "40 cm", "thickness",
        "as-built", "survey", "coordinate", "standard error", "figure",
    ):
        if term in joined:
            score += 20
    scored.append((score, page))
selected = sorted({page for _, page in sorted(scored, reverse=True)[:35]})
rendered = OUT / "rendered"
rendered.mkdir(exist_ok=True)
for page in selected:
    subprocess.run(
        [
            "pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "170",
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
    "new_item_uuid": new_item,
    "pdf_bytes": len(response.content),
    "page_count": page_count,
    "selected_render_pages": selected,
}, indent=2))
