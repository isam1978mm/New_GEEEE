#!/usr/bin/env python3
"""Metadata-only NISAR coverage feasibility check for Tyrone 3X.

Temporary scientific feasibility helper. It queries the public ASF Search API only.
It does not download NISAR imagery, use Earth Engine, fit a model, create a
calibration row, modify the classifier/NB formula/UI, or enable app depth.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

OUT = Path("artifacts/tyrone_nisar_coverage_feasibility")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
RAW = OUT / "search_response.json"

API = "https://api.daac.asf.alaska.edu/services/search/param"
POINT_WKT = "POINT(-108.415 32.72)"
START = "2026-06-17T00:00:00Z"
END = "2026-08-19T00:00:00Z"
PRODUCTS = ("GSLC", "GCOV")


def search_product(level: str) -> dict[str, Any]:
    params = {
        "dataset": "NISAR",
        "processingLevel": level,
        "intersectsWith": POINT_WKT,
        "start": START,
        "end": END,
        "maxResults": "250",
        "output": "geojson",
    }
    response = requests.get(API, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    features = payload.get("features", []) if isinstance(payload, dict) else []
    rows = []
    for feature in features:
        props = dict(feature.get("properties") or {})
        # Keep only compact metadata required for a coverage/resolution feasibility decision.
        rows.append({
            "granuleName": props.get("granuleName") or props.get("sceneName") or props.get("fileID"),
            "startTime": props.get("startTime"),
            "stopTime": props.get("stopTime"),
            "flightDirection": props.get("flightDirection"),
            "polarization": props.get("polarization"),
            "processingLevel": props.get("processingLevel"),
            "pathNumber": props.get("pathNumber"),
            "frameNumber": props.get("frameNumber"),
            "url": props.get("url"),
            "fileName": props.get("fileName"),
            "bytes": props.get("bytes"),
            "beamModeType": props.get("beamModeType"),
        })
    return {
        "query_url": response.url,
        "http_status": response.status_code,
        "feature_count": len(features),
        "sample": rows[:40],
        "raw": payload,
    }


def main() -> int:
    searches: dict[str, Any] = {}
    raw: dict[str, Any] = {}
    for level in PRODUCTS:
        try:
            result = search_product(level)
            raw[level] = result.pop("raw")
            searches[level] = result
        except Exception as exc:
            searches[level] = {
                "feature_count": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }

    counts = {level: int(searches[level].get("feature_count", 0)) for level in PRODUCTS}
    total = sum(counts.values())
    decision = "NISAR_TYRONE_COVERAGE_FOUND" if total > 0 else "NISAR_TYRONE_COVERAGE_NOT_CONFIRMED"
    result = {
        "status": "complete",
        "decision": decision,
        "site": "Tyrone 3X",
        "point_wkt": POINT_WKT,
        "date_window": [START, END],
        "dataset": "NISAR",
        "product_levels": list(PRODUCTS),
        "counts": counts,
        "searches": searches,
        "public_metadata_query_only": True,
        "imagery_downloaded": False,
        "earth_engine_query_executed": False,
        "model_fitted": False,
        "calibration_record_created": False,
        "classifier_modified": False,
        "nb_formula_modified": False,
        "ui_modified": False,
        "app_depth_enabled": False,
    }
    RAW.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
