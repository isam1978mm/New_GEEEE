#!/usr/bin/env python3
"""Probe anonymous Sentinel-1 STAC availability for the Tyrone method screen.

This script performs metadata discovery and a bounded byte-range access test only.
It does not calculate radar statistics, inspect TP5/TP6 ordering, or change the
preregistered scientific thresholds.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import planetary_computer
import pystac_client
import requests

OUT_DIR = Path("artifacts/tyrone_public_s1_source_probe")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "public_sentinel1_source_probe.json"

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
TYRONE_BBOX = [-108.445, 32.695, -108.390, 32.745]
SAMPLE_PERIOD = "2022-01-01/2022-02-01"
MAX_ITEMS_PER_COLLECTION = 3
RANGE_BYTES = 1024

PREFERRED_ASSET_KEYS = (
    "vv",
    "vh",
    "angle",
    "measurement-vv",
    "measurement-vh",
    "data",
)


def bounded_url(value: str) -> str:
    """Return URL without query string so signed tokens are never recorded."""
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def asset_summary(asset: Any) -> dict[str, Any]:
    return {
        "href_without_query": bounded_url(asset.href),
        "host": urlsplit(asset.href).netloc,
        "media_type": asset.media_type,
        "roles": list(asset.roles or []),
        "title": asset.title,
        "extra_field_keys": sorted(asset.extra_fields.keys()),
    }


def choose_probe_asset(item: Any) -> tuple[str | None, Any | None]:
    for key in PREFERRED_ASSET_KEYS:
        if key in item.assets:
            return key, item.assets[key]
    for key, asset in item.assets.items():
        media_type = (asset.media_type or "").lower()
        href = asset.href.lower()
        if "tiff" in media_type or href.endswith((".tif", ".tiff")):
            return key, asset
    return None, None


def range_probe(asset: Any) -> dict[str, Any]:
    try:
        response = requests.get(
            asset.href,
            headers={"Range": f"bytes=0-{RANGE_BYTES - 1}"},
            timeout=90,
            allow_redirects=True,
        )
        return {
            "status_code": response.status_code,
            "content_length_received": len(response.content),
            "content_type": response.headers.get("content-type"),
            "content_range": response.headers.get("content-range"),
            "final_host": urlsplit(response.url).netloc,
            "read_succeeded": response.status_code in {200, 206} and bool(response.content),
        }
    except Exception as exc:  # bounded diagnostic
        return {
            "read_succeeded": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def property_subset(properties: dict[str, Any]) -> dict[str, Any]:
    allowed_exact = {
        "datetime",
        "start_datetime",
        "end_datetime",
        "platform",
        "constellation",
        "instruments",
        "sat:orbit_state",
        "sat:relative_orbit",
        "sar:instrument_mode",
        "sar:polarizations",
        "sar:product_type",
        "s1:datatake_id",
        "s1:instrument_configuration_ID",
        "s1:orbit_source",
        "s1:processing_level",
        "s1:product_timeliness",
        "s1:resolution",
        "proj:epsg",
        "gsd",
    }
    return {key: properties.get(key) for key in sorted(allowed_exact) if key in properties}


def main() -> int:
    result: dict[str, Any] = {
        "status": "probe_started",
        "source": "microsoft_planetary_computer",
        "stac_url": STAC_URL,
        "bbox": TYRONE_BBOX,
        "sample_period": SAMPLE_PERIOD,
        "anonymous_stac_access": False,
        "collection_count": 0,
        "sentinel1_collection_ids": [],
        "collections": {},
        "radar_values_read": False,
        "scientific_query_executed": False,
        "thresholds_changed": False,
        "secret_values_printed": False,
    }

    try:
        catalog = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
        collections = list(catalog.get_collections())
        result["anonymous_stac_access"] = True
        result["collection_count"] = len(collections)
        sentinel_collections = [
            collection
            for collection in collections
            if "sentinel-1" in collection.id.lower()
            or "sentinel 1" in (collection.title or "").lower()
            or "sentinel-1" in (collection.description or "").lower()
        ]
        result["sentinel1_collection_ids"] = sorted(collection.id for collection in sentinel_collections)

        for collection in sentinel_collections:
            collection_row: dict[str, Any] = {
                "title": collection.title,
                "description_prefix": (collection.description or "")[:500],
                "license": collection.license,
                "item_asset_keys": sorted((collection.item_assets or {}).keys()),
                "sample_items": [],
            }
            search = catalog.search(
                collections=[collection.id],
                bbox=TYRONE_BBOX,
                datetime=SAMPLE_PERIOD,
                max_items=MAX_ITEMS_PER_COLLECTION,
            )
            items = list(search.items())
            collection_row["sample_item_count"] = len(items)
            for item_index, item in enumerate(items):
                item_row: dict[str, Any] = {
                    "id": item.id,
                    "bbox": item.bbox,
                    "properties": property_subset(item.properties),
                    "asset_keys": sorted(item.assets.keys()),
                    "assets": {key: asset_summary(asset) for key, asset in item.assets.items()},
                }
                if item_index == 0:
                    asset_key, asset = choose_probe_asset(item)
                    item_row["range_probe_asset_key"] = asset_key
                    item_row["range_probe"] = range_probe(asset) if asset is not None else {
                        "read_succeeded": False,
                        "error": "no raster-like asset found",
                    }
                collection_row["sample_items"].append(item_row)
            result["collections"][collection.id] = collection_row

        usable_collections = []
        for collection_id, row in result["collections"].items():
            for item in row.get("sample_items", []):
                if item.get("range_probe", {}).get("read_succeeded"):
                    usable_collections.append(collection_id)
                    break
        result["usable_collection_ids"] = sorted(set(usable_collections))
        result["status"] = "source_ready" if usable_collections else "source_unavailable"
    except Exception as exc:
        result["status"] = "probe_error"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:1000]

    OUT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
