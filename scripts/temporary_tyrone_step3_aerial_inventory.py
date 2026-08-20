#!/usr/bin/env python3
"""Temporary research-only inventory probe for Tyrone historical aerial frames.

Downloads the official USGS Aerial Photo Single Frames coverage shapefile and
reports every archived frame/record whose geometry overlaps a small box around
Tyrone Tailing Dam 3X. No imagery is downloaded and no app/runtime code is used.
"""
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import requests
import shapefile

URL = "https://dds.cr.usgs.gov/ee-data/coveragemaps/shp/ee/aerial_combin/aerial_combin.zip"
OUT = Path("artifacts/tyrone_step3_aerial_inventory")
OUT.mkdir(parents=True, exist_ok=True)
ZIP = OUT / "aerial_combin.zip"
EXTRACT = OUT / "coverage"
# Tyrone 3X plus margin, WGS84 degrees.
AOI = (-108.47, 32.67, -108.37, 32.77)


def overlaps(bbox, aoi):
    xmin, ymin, xmax, ymax = bbox
    axmin, aymin, axmax, aymax = aoi
    return not (xmax < axmin or xmin > axmax or ymax < aymin or ymin > aymax)


def main() -> int:
    r = requests.get(URL, timeout=180)
    r.raise_for_status()
    ZIP.write_bytes(r.content)
    EXTRACT.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist()
        z.extractall(EXTRACT)

    shp_files = sorted(EXTRACT.rglob("*.shp"))
    if not shp_files:
        raise RuntimeError("No shapefile found in USGS coverage ZIP")

    summary = {
        "status": "STEP3_USGS_AERIAL_COVERAGE_INVENTORY_COMPLETE",
        "source_url": URL,
        "zip_bytes": len(r.content),
        "zip_members": names,
        "aoi_wgs84": AOI,
        "layers": [],
        "imagery_downloaded": False,
        "depth_calculated": False,
        "production_code_modified": False,
    }
    all_rows = []

    for shp_path in shp_files:
        reader = shapefile.Reader(str(shp_path))
        fields = [f[0] for f in reader.fields[1:]]
        layer = {
            "shapefile": str(shp_path.relative_to(EXTRACT)),
            "shape_type": reader.shapeTypeName,
            "record_count": len(reader),
            "fields": fields,
            "matches": 0,
        }
        for sr in reader.iterShapeRecords():
            shape = sr.shape
            try:
                bbox = list(shape.bbox)
            except Exception:
                pts = shape.points
                if not pts:
                    continue
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            if not overlaps(bbox, AOI):
                continue
            attrs = dict(zip(fields, list(sr.record)))
            attrs["_layer"] = layer["shapefile"]
            attrs["_bbox"] = bbox
            all_rows.append(attrs)
            layer["matches"] += 1
        summary["layers"].append(layer)

    # Preserve all matching fields without guessing their meanings.
    (OUT / "matches.json").write_text(json.dumps(all_rows, indent=2, default=str) + "\n", encoding="utf-8")
    summary["total_matches"] = len(all_rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")

    # Flat CSV for quick inspection.
    keys = sorted({k for row in all_rows for k in row.keys()})
    with (OUT / "matches.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in all_rows:
            w.writerow({k: row.get(k) for k in keys})

    print(json.dumps(summary, indent=2, default=str))
    print("MATCH SAMPLE")
    print(json.dumps(all_rows[:20], indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
