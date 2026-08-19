#!/usr/bin/env python3
"""Metadata-only feasibility check for direct elevation-difference depth at Tyrone 3X.

Temporary research helper. Does not download elevation or imagery data and does not
calculate depth.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

OUT = Path("artifacts/tyrone_direct_elevation_feasibility")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"

# Small box covering Tyrone Tailing Dam 3X and surrounding stable ground.
BBOX = (-108.43, 32.70, -108.40, 32.74)
TNM_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"
M2M_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/dataset-search"


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "title", "publicationDate", "lastUpdated", "dateCreated", "sourceId",
        "sourceName", "downloadURL", "metaUrl", "format", "sizeInBytes",
        "boundingBox", "bestFitIndex", "urls",
    )
    return {k: item.get(k) for k in keys if k in item}


def tnm_query(dataset: str) -> dict[str, Any]:
    params = {
        "bbox": ",".join(str(v) for v in BBOX),
        "datasets": dataset,
        "max": 100,
        "outputFormat": "JSON",
    }
    try:
        r = requests.get(TNM_URL, params=params, timeout=60)
        payload: Any
        try:
            payload = r.json()
        except Exception:
            payload = {"text": r.text[:2000]}
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return {
            "http_status": r.status_code,
            "request_url": r.url,
            "total": payload.get("total") if isinstance(payload, dict) else None,
            "items_returned": len(items),
            "items": [compact_item(x) for x in items[:100]],
            "error": payload.get("error") if isinstance(payload, dict) else None,
        }
    except Exception as exc:
        return {"http_status": None, "error_type": type(exc).__name__, "error": str(exc)}


def m2m_probe() -> dict[str, Any]:
    # This deliberately supplies no API token. The purpose is only to determine
    # whether inventory discovery can proceed without asking the user for another
    # credential. No imagery is requested or downloaded.
    body = {
        "datasetName": "Aerial Photo Single Frames",
        "spatialFilter": {
            "filterType": "mbr",
            "lowerLeft": {"latitude": BBOX[1], "longitude": BBOX[0]},
            "upperRight": {"latitude": BBOX[3], "longitude": BBOX[2]},
        },
        "temporalFilter": {"start": "2000-01-01", "end": "2005-06-01"},
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(M2M_URL, headers=headers, json=body, timeout=60)
        try:
            payload: Any = r.json()
        except Exception:
            payload = {"text": r.text[:2000]}
        return {
            "http_status": r.status_code,
            "request_url": r.url,
            "response": payload,
            "note": "No USGS M2M token was supplied; this is an access-feasibility probe only.",
        }
    except Exception as exc:
        return {"http_status": None, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> int:
    result = {
        "status": "METADATA_ONLY_COMPLETE",
        "site": "Tyrone Tailing Dam 3X",
        "bbox_wgs84": BBOX,
        "depth_calculated": False,
        "elevation_or_imagery_downloaded": False,
        "classifier_modified": False,
        "nb_formula_modified": False,
        "ui_modified": False,
        "tnm": {
            "lidar_point_cloud": tnm_query("Lidar Point Cloud (LPC)"),
            "dem_1m": tnm_query("Digital Elevation Model (DEM) 1 meter"),
        },
        "historical_aerial_inventory_access_probe": m2m_probe(),
    }
    RESULT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
