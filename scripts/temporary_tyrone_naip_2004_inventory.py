#!/usr/bin/env python3
"""Research-only EarthExplorer NAIP inventory for Tyrone 3X.

Queries only public EarthExplorer metadata for a small AOI around Tyrone 3X
from 2004-01-01 through 2004-08-31. No production code, depth code, or paid
order actions are used.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from pathlib import Path
from urllib.parse import urlencode

import requests

OUT = Path("artifacts/tyrone_naip_2004_free_check")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://earthexplorer.usgs.gov/"
ALIAS = "naip"
CENTER = (32.7215, -108.4193)
AOI = [
    (32.7160, -108.4250),
    (32.7160, -108.4130),
    (32.7270, -108.4130),
    (32.7270, -108.4250),
]
DATE_START = "01/01/2004"
DATE_END = "08/31/2004"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def post_tab(session: requests.Session, payload: dict):
    r = session.post(
        ROOT + "tabs/save",
        data={"data": json.dumps(payload, separators=(",", ":"))},
        timeout=120,
    )
    return [r.status_code, compact(r.text)[:500]]


def find_collection(session: requests.Session):
    r = session.get(ROOT + "dataset/categories", timeout=120)
    r.raise_for_status()
    OUT.joinpath("dataset_categories.html").write_text(r.text, encoding="utf-8")
    for m in re.finditer(
        r"<span\b([^>]*class=[\"'][^\"']*collection[^\"']*[\"'][^>]*)>(.*?)</span>",
        r.text,
        re.I | re.S,
    ):
        attrs, body = m.group(1), m.group(2)
        am = re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']", attrs, re.I)
        im = re.search(r"data-datasetId=[\"']([^\"']+)[\"']", attrs, re.I)
        title = compact(re.sub(r"<[^>]+>", " ", body))
        if am and im and am.group(1).lower() == ALIAS:
            return {"alias": am.group(1), "collection_id": im.group(1), "title": title}
    raise RuntimeError("NAIP collection not found")


def parse_rows(text: str, cid: str):
    rows = []
    for m in re.finditer(
        r"<tr\b([^>]*(?:data-entityId|data-entityid)[^>]*)>(.*?)</tr>",
        text,
        re.I | re.S,
    ):
        attrs, body = m.group(1), m.group(2)

        def attr(name: str):
            q = re.search(rf"\b{name}=[\"']([^\"']*)[\"']", attrs, re.I)
            return html_lib.unescape(q.group(1)) if q else None

        eid = attr("data-entityId")
        if eid:
            rows.append(
                {
                    "collection_id": cid,
                    "entity_id": eid,
                    "display_id": attr("data-displayId"),
                    "scene_id": attr("data-scene-id"),
                    "corner_points": attr("data-corner-points"),
                    "row_text": compact(re.sub(r"<[^>]+>", " ", body)),
                }
            )
    return list({r["entity_id"]: r for r in rows}.values())


def metadata(session: requests.Session, cid: str, eid: str):
    url = ROOT + f"scene/metadata/full/{cid}/{eid}/"
    r = session.get(url, timeout=120)
    text = r.text if r.ok else ""
    visible = compact(re.sub(r"<[^>]+>", " ", text))
    keys = [
        "State",
        "NAIP Entity ID",
        "Agency",
        "Vendor",
        "Map Projection",
        "Projection Zone",
        "Datum",
        "Resolution",
        "Units",
        "Number of Bands",
        "Sensor Type",
        "Project Name",
        "Acquisition Date",
    ]
    pairs = {}
    for key in keys:
        mm = re.search(rf"{re.escape(key)}\s*</td>\s*<td[^>]*>\s*(.*?)\s*</td>", text, re.I | re.S)
        if mm:
            pairs[key] = compact(re.sub(r"<[^>]+>", " ", mm.group(1)))
    if not pairs:
        # Fallback against rendered text style: 'Key : value'.
        for key in keys:
            mm = re.search(rf"{re.escape(key)}\s*:?\s+([^|]+?)(?=\s+(?:{'|'.join(map(re.escape, keys))})\s*:|$)", visible, re.I)
            if mm:
                pairs[key] = mm.group(1).strip()
    return {"http_status": r.status_code, "pairs": pairs, "visible_text": visible[:8000]}


def main():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 Tyrone-research/1.0", "Referer": ROOT})
    predefined = ROOT + "criteria?" + urlencode(
        {
            "node": "EE",
            "dataset_name": ALIAS,
            "aoiFilter": json.dumps([[CENTER[0], CENTER[1]]], separators=(",", ":")),
        }
    )
    landing = s.get(predefined, timeout=120, allow_redirects=True)
    landing.raise_for_status()
    collection = find_collection(s)
    cid = collection["collection_id"]

    s.post(ROOT + "tabs/clear", timeout=120)
    coords = [
        {"c": str(i), "a": f"{lat:.4f}", "o": f"{lon:.4f}"}
        for i, (lat, lon) in enumerate(AOI)
    ]
    tab1 = post_tab(
        s,
        {
            "tab": 1,
            "destination": 4,
            "coordinates": coords,
            "format": "dd",
            "dStart": DATE_START,
            "dEnd": DATE_END,
            "searchType": "Std",
            "includeUnknownCC": "1",
            "maxCC": 100,
            "minCC": 0,
            "months": [str(i) for i in range(12)],
            "pType": "polygon",
        },
    )
    tab2 = post_tab(s, {"tab": 2, "destination": 4, "cList": [cid], "selected": cid})
    selected = s.post(ROOT + "dataset/select", data={"datasetId": cid}, timeout=120)
    sr = s.post(ROOT + "scene/search", data={"datasetId": cid, "resultsPerPage": 100}, timeout=300)
    sr.raise_for_status()
    OUT.joinpath("scene_search_page1.html").write_text(sr.text, encoding="utf-8")
    scenes = parse_rows(sr.text, cid)

    nums = [int(x) for x in re.findall(r"(?:data-page|value)=[\"'](\d+)[\"']", sr.text, re.I)]
    max_page = min(max(nums or [1]), 10)
    for page in range(2, max_page + 1):
        x = s.post(
            ROOT + "scene/search",
            data={"datasetId": cid, "resultsPerPage": 100, "pageNum": page},
            timeout=300,
        )
        if x.ok:
            OUT.joinpath(f"scene_search_page{page}.html").write_text(x.text, encoding="utf-8")
            scenes.extend(parse_rows(x.text, cid))
    scenes = list({r["entity_id"]: r for r in scenes}.values())

    for scene in scenes:
        scene["metadata"] = metadata(s, cid, scene["entity_id"])

    result = {
        "status": "TYRONE_NAIP_2004_PUBLIC_METADATA_CHECK_COMPLETE",
        "dataset": collection,
        "aoi_polygon_latlon": AOI,
        "center_wgs84": CENTER,
        "date_start": "2004-01-01",
        "date_end": "2004-08-31",
        "tab1_save": tab1,
        "tab2_save": tab2,
        "dataset_select_status": selected.status_code,
        "scene_search_status": sr.status_code,
        "scene_count": len(scenes),
        "scenes": scenes,
        "paid_order_attempted": False,
        "production_code_modified": False,
        "depth_calculated": False,
    }
    OUT.joinpath("result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
