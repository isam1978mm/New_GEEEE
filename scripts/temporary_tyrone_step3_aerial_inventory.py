#!/usr/bin/env python3
"""Temporary research-only EarthExplorer scene inventory for Tyrone 3X.

Replicates EarthExplorer's public browser AJAX flow for AERIAL_COMBIN at a
single Tyrone point, restricted to 2000-01-01 through 2004-08-31. It records
scene/result metadata and download-option metadata only. It does not download
imagery, calculate depth, fit a model, or touch production application code.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from pathlib import Path
from urllib.parse import urlencode

import requests

OUT = Path("artifacts/tyrone_step3_aerial_inventory")
OUT.mkdir(parents=True, exist_ok=True)
LAT = 32.7215
LON = -108.4193
ALIAS = "AERIAL_COMBIN"
ROOT = "https://earthexplorer.usgs.gov/"
PREDEFINED = ROOT + "criteria?" + urlencode({
    "node": "EE",
    "dataset_name": ALIAS,
    "aoiFilter": json.dumps([[LAT, LON]], separators=(",", ":")),
})


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def save(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8")


def post_save(session: requests.Session, payload: dict) -> dict:
    r = session.post(ROOT + "tabs/save", data={"data": json.dumps(payload, separators=(",", ":"))}, timeout=120)
    return {"status": r.status_code, "text": compact(r.text)[:1000], "url": r.url}


def parse_rows(result_html: str, collection_id: str):
    rows = []
    # EarthExplorer result rows expose IDs and corner points in data attributes.
    for m in re.finditer(r"<tr\b([^>]*(?:data-entityId|data-entityid)[^>]*)>(.*?)</tr>", result_html, re.I | re.S):
        attrs, body = m.group(1), m.group(2)
        def attr(name):
            mm = re.search(rf"\b{name}=[\"']([^\"']*)[\"']", attrs, re.I)
            return html_lib.unescape(mm.group(1)) if mm else None
        row = {
            "collection_id": collection_id,
            "entity_id": attr("data-entityId"),
            "display_id": attr("data-displayId"),
            "scene_id": attr("data-scene-id"),
            "corner_points": attr("data-corner-points"),
            "row_text": compact(re.sub(r"<[^>]+>", " ", body)),
        }
        if row["entity_id"]:
            rows.append(row)
    # Fallback: capture attributes even if table markup differs.
    if not rows:
        for m in re.finditer(r"data-entityId=[\"']([^\"']+)[\"']", result_html, re.I):
            start = max(0, result_html.rfind("<tr", 0, m.start()))
            end = result_html.find("</tr>", m.end())
            chunk = result_html[start:(end + 5 if end >= 0 else m.end() + 3000)]
            def find_attr(name):
                mm = re.search(rf"\b{name}=[\"']([^\"']*)[\"']", chunk, re.I)
                return html_lib.unescape(mm.group(1)) if mm else None
            rows.append({
                "collection_id": collection_id,
                "entity_id": m.group(1),
                "display_id": find_attr("data-displayId"),
                "scene_id": find_attr("data-scene-id"),
                "corner_points": find_attr("data-corner-points"),
                "row_text": compact(re.sub(r"<[^>]+>", " ", chunk)),
            })
    # Deduplicate.
    uniq = {}
    for row in rows:
        uniq[row["entity_id"]] = row
    return list(uniq.values())


def metadata_pairs(text: str):
    clean = html_lib.unescape(text)
    pairs = {}
    # Common metadata markup is a label/value table; preserve all visible lines too.
    for m in re.finditer(r"<tr[^>]*>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*</tr>", clean, re.I | re.S):
        k = compact(re.sub(r"<[^>]+>", " ", m.group(1))).rstrip(":")
        v = compact(re.sub(r"<[^>]+>", " ", m.group(2)))
        if k and v:
            pairs[k] = v
    return pairs


def main() -> int:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 Tyrone-research/1.0", "Referer": ROOT})

    landing = s.get(PREDEFINED, timeout=120, allow_redirects=True)
    landing.raise_for_status()
    save("landing.html", landing.text)

    categories = s.get(ROOT + "dataset/categories", timeout=120)
    categories.raise_for_status()
    save("dataset_categories.html", categories.text)

    # Find span carrying the AERIAL_COMBIN alias, regardless of attribute order.
    collection_id = None
    collection_tag = None
    for tag in re.findall(r"<span\b[^>]*class=[\"'][^\"']*collection[^\"']*[\"'][^>]*>", categories.text, re.I):
        alias_m = re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']", tag, re.I)
        if alias_m and alias_m.group(1).upper() == ALIAS:
            id_m = re.search(r"data-datasetId=[\"']([^\"']+)[\"']", tag, re.I)
            if id_m:
                collection_id = id_m.group(1)
                collection_tag = tag
                break
    if not collection_id:
        # Alternate attribute order/class formatting fallback.
        pos = categories.text.upper().find(ALIAS)
        snippet = categories.text[max(0, pos-1000):pos+1000] if pos >= 0 else categories.text[:3000]
        save("dataset_alias_context.html", snippet)
        ids = re.findall(r"data-datasetId=[\"']([^\"']+)[\"']", snippet, re.I)
        if ids:
            collection_id = ids[-1]
    if not collection_id:
        raise RuntimeError("Could not resolve AERIAL_COMBIN numeric collection id from /dataset/categories")

    criteria = s.get(ROOT + "dataset/criteria", params={"datasetName": ALIAS}, timeout=120)
    criteria.raise_for_status()
    save("dataset_criteria.html", criteria.text)

    # Clear any old session state, then save a frozen point/date search.
    clear = s.post(ROOT + "tabs/clear", timeout=120)
    coordinates = [{"c": 0, "a": f"{LAT:.4f}", "o": f"{LON:.4f}"}]
    tab1 = post_save(s, {
        "tab": 1,
        "destination": 4,
        "coordinates": coordinates,
        "format": "dd",
        "dStart": "01/01/2000",
        "dEnd": "08/31/2004",
        "searchType": "Std",
        "includeUnknownCC": "1",
        "maxCC": 100,
        "minCC": 0,
        "months": list(range(1, 13)),
        "pType": "point",
    })
    tab2 = post_save(s, {
        "tab": 2,
        "destination": 4,
        "cList": [collection_id],
        "selected": collection_id,
    })
    # Select dataset explicitly as the browser does on tab 4.
    select = s.post(ROOT + "dataset/select", data={"datasetId": collection_id}, timeout=120)

    search = s.post(ROOT + "scene/search", data={"datasetId": collection_id, "resultsPerPage": 100}, timeout=300)
    search.raise_for_status()
    save("scene_search_page1.html", search.text)
    rows = parse_rows(search.text, collection_id)

    # Determine page count from result HTML and fetch any additional pages.
    page_nums = [int(x) for x in re.findall(r"(?:data-page|value)=[\"'](\d+)[\"']", search.text, re.I)]
    max_page = min(max(page_nums or [1]), 30)
    for page in range(2, max_page + 1):
        rr = s.post(ROOT + "scene/search", data={"datasetId": collection_id, "resultsPerPage": 100, "pageNum": page}, timeout=300)
        if not rr.ok:
            continue
        save(f"scene_search_page{page}.html", rr.text)
        rows.extend(parse_rows(rr.text, collection_id))
    rows = list({r["entity_id"]: r for r in rows}.values())

    enriched = []
    for i, row in enumerate(rows):
        entity = row["entity_id"]
        mr = s.get(ROOT + f"scene/metadata/info/{collection_id}/{entity}/", timeout=120)
        metadata_html = mr.text if mr.ok else ""
        pairs = metadata_pairs(metadata_html)
        visible = compact(re.sub(r"<[^>]+>", " ", metadata_html))
        dr = s.post(ROOT + f"scene/downloadoptions/{collection_id}/{entity}", data={}, timeout=120)
        download_html = dr.text if dr.ok else ""
        download_visible = compact(re.sub(r"<[^>]+>", " ", download_html))
        rec = dict(row)
        rec.update({
            "metadata_http": mr.status_code,
            "metadata": pairs,
            "metadata_text": visible,
            "download_options_http": dr.status_code,
            "download_options_text": download_visible,
            "download_product_ids": sorted(set(re.findall(r"(?:productId|product-id|data-product-id)[=:\"' ]+([A-Za-z0-9_.-]+)", download_html, re.I))),
            "download_links": sorted(set(html_lib.unescape(x) for x in re.findall(r"href=[\"']([^\"']+)[\"']", download_html, re.I))),
        })
        enriched.append(rec)
        if i < 50:
            save(f"metadata_{i+1:03d}_{re.sub(r'[^A-Za-z0-9_.-]+','_',entity)}.html", metadata_html)
            save(f"download_{i+1:03d}_{re.sub(r'[^A-Za-z0-9_.-]+','_',entity)}.html", download_html)

    result = {
        "status": "STEP3_SCENE_INVENTORY_COMPLETE",
        "dataset_alias": ALIAS,
        "collection_id": collection_id,
        "collection_tag": collection_tag,
        "point_wgs84": [LAT, LON],
        "date_start": "2000-01-01",
        "date_end": "2004-08-31",
        "clear_status": clear.status_code,
        "tab1_save": tab1,
        "tab2_save": tab2,
        "dataset_select_status": select.status_code,
        "dataset_select_text": compact(select.text)[:1000],
        "scene_search_status": search.status_code,
        "scene_search_chars": len(search.text),
        "scene_count": len(enriched),
        "scenes": enriched,
        "imagery_downloaded": False,
        "depth_calculated": False,
        "known_depth_values_read": False,
        "production_code_modified": False,
    }
    (OUT / "scene_inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
