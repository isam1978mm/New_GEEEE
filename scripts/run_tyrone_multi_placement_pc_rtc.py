#!/usr/bin/env python3
"""Run preregistered Tyrone protocol v2 with public Planetary Computer RTC."""
from __future__ import annotations

import csv
import json
import math
import time
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as geom_transform

from scripts import run_tyrone_multi_placement_sensitivity as v1

OUT = Path("artifacts/tyrone_multi_placement_pc_rtc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "tyrone_pc_rtc_sensitivity_result.json"
MONTHLY = OUT / "monthly_differences.csv"
PLACEMENTS = OUT / "placement_summary.csv"
SOURCES = OUT / "selected_source_items.csv"

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-1-rtc"
START = "2018-01-01"
END = "2024-01-01"
BBOX = [-108.445, 32.695, -108.390, 32.745]
CRS = "EPSG:32613"
RESOLUTION = 10.0
NODATA = -32768.0


def item_time(item: Any) -> datetime:
    value = item.datetime
    if value is None:
        raw = item.properties.get("datetime") or item.properties.get("start_datetime")
        if not raw:
            raise ValueError(f"item {item.id} has no datetime")
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def orbit_selection(items: list[Any]) -> tuple[dict[str, Any], list[Any]]:
    groups: dict[tuple[str, int], list[Any]] = defaultdict(list)
    for item in items:
        props = item.properties
        pols = {str(x).upper() for x in props.get("sar:polarizations", [])}
        state = str(props.get("sat:orbit_state") or "").lower()
        orbit = props.get("sat:relative_orbit")
        if (
            props.get("sar:instrument_mode") == "IW"
            and {"VV", "VH"}.issubset(pols)
            and "vv" in item.assets
            and "vh" in item.assets
            and state
            and orbit is not None
        ):
            groups[(state, int(orbit))].append(item)
    if not groups:
        raise RuntimeError("no usable Sentinel-1 RTC orbit groups")
    ranking = []
    for (state, orbit), rows in groups.items():
        months = {item_time(item).strftime("%Y-%m") for item in rows}
        ranking.append(
            {
                "orbit_state": state,
                "relative_orbit": orbit,
                "distinct_months": len(months),
                "acquisition_count": len(rows),
            }
        )
    ranking.sort(
        key=lambda r: (
            -r["distinct_months"],
            -r["acquisition_count"],
            r["orbit_state"],
            r["relative_orbit"],
        )
    )
    best = ranking[0]
    chosen = sorted(
        groups[(best["orbit_state"], best["relative_orbit"])], key=item_time
    )
    return {**best, "ranking": ranking}, chosen


def geometry_and_grid() -> tuple[list[dict[str, Any]], dict[tuple[str, str], np.ndarray], dict[str, Any]]:
    hypotheses = v1.build_hypotheses()
    to_target = Transformer.from_crs("EPSG:4326", "EPSG:32613", always_xy=True)
    polygons: dict[tuple[str, str], Polygon] = {}
    for hypothesis in hypotheses:
        for zone in ("tp5", "tp6"):
            polygon = Polygon(hypothesis["polygons"][zone])
            polygon = geom_transform(to_target.transform, polygon).buffer(-v1.EDGE_BUFFER_M)
            if polygon.is_empty or not polygon.is_valid:
                raise RuntimeError(f"invalid buffered polygon: {hypothesis['hypothesis_id']} {zone}")
            polygons[(hypothesis["hypothesis_id"], zone)] = polygon

    minx = min(p.bounds[0] for p in polygons.values())
    miny = min(p.bounds[1] for p in polygons.values())
    maxx = max(p.bounds[2] for p in polygons.values())
    maxy = max(p.bounds[3] for p in polygons.values())
    left = math.floor(minx / RESOLUTION) * RESOLUTION
    bottom = math.floor(miny / RESOLUTION) * RESOLUTION
    right = math.ceil(maxx / RESOLUTION) * RESOLUTION
    top = math.ceil(maxy / RESOLUTION) * RESOLUTION
    width = int(round((right - left) / RESOLUTION))
    height = int(round((top - bottom) / RESOLUTION))
    transform = Affine(RESOLUTION, 0, left, 0, -RESOLUTION, top)
    if width <= 0 or height <= 0 or width * height > 2_000_000:
        raise RuntimeError(f"invalid fixed grid: {width}x{height}")

    masks: dict[tuple[str, str], np.ndarray] = {}
    counts: list[int] = []
    for key, polygon in polygons.items():
        mask = geometry_mask(
            [mapping(polygon)],
            out_shape=(height, width),
            transform=transform,
            invert=True,
            all_touched=False,
        )
        count = int(mask.sum())
        if count < v1.MIN_VALID_PIXELS:
            raise RuntimeError(f"too few fixed-grid pixels for {key}: {count}")
        masks[key] = mask
        counts.append(count)

    grid = {
        "crs": CRS,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": (left, bottom, right, top),
        "minimum_mask_pixels": min(counts),
        "maximum_mask_pixels": max(counts),
    }
    return hypotheses, masks, grid


def signed_item(item: Any) -> Any:
    clone = item.clone()
    planetary_computer.sign_inplace(clone)
    return clone


def read_cog(href: str, grid: dict[str, Any]) -> np.ndarray:
    with rasterio.open(href, sharing=False) as src:
        src_nodata = src.nodata if src.nodata is not None else NODATA
        with WarpedVRT(
            src,
            crs=grid["crs"],
            transform=grid["transform"],
            width=grid["width"],
            height=grid["height"],
            resampling=Resampling.nearest,
            src_nodata=src_nodata,
            nodata=NODATA,
        ) as vrt:
            array = np.asarray(vrt.read(1, masked=True).filled(np.nan), dtype=np.float64)
    out = np.full(array.shape, np.nan, dtype=np.float64)
    valid = np.isfinite(array) & (array > 0) & (array != NODATA)
    out[valid] = 10.0 * np.log10(array[valid])
    return out


def read_pair(item: Any, grid: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    last: Exception | None = None
    for attempt in range(3):
        try:
            signed = signed_item(item)
            return read_cog(signed.assets["vv"].href, grid), read_cog(
                signed.assets["vh"].href, grid
            )
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
    assert last is not None
    raise last


def masked_mean(array: np.ndarray, mask: np.ndarray) -> tuple[float | None, int]:
    values = array[mask]
    values = values[np.isfinite(values)]
    if values.size < v1.MIN_VALID_PIXELS:
        return None, int(values.size)
    return float(values.mean()), int(values.size)


def write_tables(monthly: list[dict[str, Any]], summaries: list[Any], sources: list[dict[str, Any]]) -> None:
    monthly_fields = [
        "hypothesis_id", "month", "season", "acquisition_count",
        "tp5_log_ratio_db", "tp6_log_ratio_db", "difference_tp6_minus_tp5",
        "sign", "tp5_valid_pixels", "tp6_valid_pixels",
        "tp5_vv_db", "tp6_vv_db", "tp5_vh_db", "tp6_vh_db",
    ]
    with MONTHLY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=monthly_fields)
        writer.writeheader()
        for row in monthly:
            writer.writerow({k: row.get(k) for k in monthly_fields})

    placement_fields = [
        "hypothesis_id", "transform_id", "translation_x", "translation_y",
        "usable_months", "positive_months", "negative_months", "zero_months",
        "dominant_sign", "dominant_fraction", "passed", "failure_reasons",
        "season_support_json",
    ]
    with PLACEMENTS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=placement_fields)
        writer.writeheader()
        for s in summaries:
            writer.writerow(
                {
                    "hypothesis_id": s.hypothesis_id,
                    "transform_id": s.transform_id,
                    "translation_x": s.translation_x,
                    "translation_y": s.translation_y,
                    "usable_months": s.usable_months,
                    "positive_months": s.positive_months,
                    "negative_months": s.negative_months,
                    "zero_months": s.zero_months,
                    "dominant_sign": s.dominant_sign or "",
                    "dominant_fraction": "" if s.dominant_fraction is None else s.dominant_fraction,
                    "passed": s.passed,
                    "failure_reasons": "|".join(s.failure_reasons),
                    "season_support_json": json.dumps(s.season_support, sort_keys=True),
                }
            )

    source_fields = [
        "item_id", "datetime", "month", "orbit_state", "relative_orbit",
        "read_status", "error_type", "error",
    ]
    with SOURCES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=source_fields)
        writer.writeheader()
        for row in sources:
            writer.writerow({k: row.get(k) for k in source_fields})


def main() -> int:
    warnings.filterwarnings("ignore", message="All-NaN slice encountered")
    result: dict[str, Any] = {
        "status": "source_unavailable",
        "protocol": "tyrone_multi_placement_pc_rtc_v2",
        "source": {
            "stac_url": STAC,
            "collection": COLLECTION,
            "period_start": START,
            "period_end_exclusive": END,
            "asset_scale": "linear_intensity",
            "linear_to_db_formula": "10*log10(value)",
        },
        "primary_feature": "monthly_median_VV_dB_minus_monthly_median_VH_dB",
        "geometry_hypothesis_count": 36,
        "edge_buffer_m": v1.EDGE_BUFFER_M,
        "minimum_valid_pixels": v1.MIN_VALID_PIXELS,
        "minimum_usable_months": v1.MIN_USABLE_MONTHS,
        "required_passing_placements": v1.MIN_PASSING_PLACEMENTS,
        "incidence_angle_available": False,
        "incidence_gate_applied": False,
        "scientific_query_executed": False,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "unknown_aoi_depth_enabled": False,
        "thresholds_changed_after_value_inspection": False,
        "secret_values_printed": False,
    }

    try:
        hypotheses, masks, grid = geometry_and_grid()
        result["fixed_grid"] = {
            "crs": grid["crs"],
            "pixel_size_m": RESOLUTION,
            "width": grid["width"],
            "height": grid["height"],
            "bounds": list(grid["bounds"]),
            "minimum_mask_pixel_count": grid["minimum_mask_pixels"],
            "maximum_mask_pixel_count": grid["maximum_mask_pixels"],
        }

        catalog = pystac_client.Client.open(STAC)
        items = list(
            catalog.search(
                collections=[COLLECTION], bbox=BBOX, datetime=f"{START}/{END}"
            ).items()
        )
        result["catalog_item_count"] = len(items)
        if not items:
            raise RuntimeError("public RTC catalog returned no Tyrone items")

        selected, selected_items = orbit_selection(items)
        result["selected_orbit"] = {
            k: selected[k]
            for k in ("orbit_state", "relative_orbit", "distinct_months", "acquisition_count")
        }
        result["orbit_ranking"] = selected["ranking"]

        by_month: dict[str, list[Any]] = defaultdict(list)
        for item in selected_items:
            by_month[item_time(item).strftime("%Y-%m")].append(item)

        rows_by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
        monthly_rows: list[dict[str, Any]] = []
        source_rows: list[dict[str, Any]] = []
        successful = 0
        failed = 0

        for month in sorted(by_month):
            vv_stack: list[np.ndarray] = []
            vh_stack: list[np.ndarray] = []
            for item in by_month[month]:
                dt = item_time(item)
                source_row = {
                    "item_id": item.id,
                    "datetime": dt.isoformat(),
                    "month": month,
                    "orbit_state": selected["orbit_state"],
                    "relative_orbit": selected["relative_orbit"],
                    "read_status": "failed",
                    "error_type": "",
                    "error": "",
                }
                try:
                    vv, vh = read_pair(item, grid)
                    vv_stack.append(vv)
                    vh_stack.append(vh)
                    source_row["read_status"] = "success"
                    successful += 1
                except Exception as exc:
                    source_row["error_type"] = type(exc).__name__
                    source_row["error"] = str(exc)[:500]
                    failed += 1
                source_rows.append(source_row)

            if not vv_stack:
                continue
            vv_month = np.nanmedian(np.stack(vv_stack), axis=0)
            vh_month = np.nanmedian(np.stack(vh_stack), axis=0)
            ratio = vv_month - vh_month
            season = v1.SEASONS[int(month.split("-")[1])]

            for hypothesis in hypotheses:
                hid = hypothesis["hypothesis_id"]
                tp5, n5 = masked_mean(ratio, masks[(hid, "tp5")])
                tp6, n6 = masked_mean(ratio, masks[(hid, "tp6")])
                if tp5 is None or tp6 is None:
                    continue
                vv5, _ = masked_mean(vv_month, masks[(hid, "tp5")])
                vv6, _ = masked_mean(vv_month, masks[(hid, "tp6")])
                vh5, _ = masked_mean(vh_month, masks[(hid, "tp5")])
                vh6, _ = masked_mean(vh_month, masks[(hid, "tp6")])
                difference = tp6 - tp5
                row = {
                    "hypothesis_id": hid,
                    "month": month,
                    "season": season,
                    "acquisition_count": len(vv_stack),
                    "tp5_log_ratio_db": tp5,
                    "tp6_log_ratio_db": tp6,
                    "difference_tp6_minus_tp5": difference,
                    "sign": v1.sign_of(difference),
                    "tp5_valid_pixels": n5,
                    "tp6_valid_pixels": n6,
                    "tp5_vv_db": vv5,
                    "tp6_vv_db": vv6,
                    "tp5_vh_db": vh5,
                    "tp6_vh_db": vh6,
                }
                monthly_rows.append(row)
                rows_by_hypothesis[hid].append(row)

        summaries = [
            v1.summarize_placement(h, rows_by_hypothesis[h["hypothesis_id"]])
            for h in hypotheses
        ]
        passing = [s for s in summaries if s.passed]
        sign_counts = Counter(s.dominant_sign for s in passing if s.dominant_sign)
        shared_sign = sign_counts.most_common(1)[0][0] if sign_counts else None
        same_sign = [s for s in passing if s.dominant_sign == shared_sign]

        if all(s.usable_months < v1.MIN_USABLE_MONTHS for s in summaries):
            status = "insufficient_data"
        elif len(same_sign) >= v1.MIN_PASSING_PLACEMENTS and len(same_sign) == len(passing):
            status = "ordering_supported"
        else:
            status = "ordering_inconsistent"

        write_tables(monthly_rows, summaries, source_rows)
        result.update(
            {
                "status": status,
                "scientific_query_executed": True,
                "successful_source_item_count": successful,
                "failed_source_item_count": failed,
                "months_with_usable_arrays": len({r["month"] for r in monthly_rows}),
                "monthly_usable_row_count": len(monthly_rows),
                "passing_placement_count": len(passing),
                "same_sign_passing_placement_count": len(same_sign),
                "shared_dominant_sign": shared_sign,
                "placement_summaries": [
                    {
                        "hypothesis_id": s.hypothesis_id,
                        "transform_id": s.transform_id,
                        "translation_x": s.translation_x,
                        "translation_y": s.translation_y,
                        "usable_months": s.usable_months,
                        "positive_months": s.positive_months,
                        "negative_months": s.negative_months,
                        "zero_months": s.zero_months,
                        "dominant_sign": s.dominant_sign,
                        "dominant_fraction": s.dominant_fraction,
                        "season_support": s.season_support,
                        "passed": s.passed,
                        "failure_reasons": list(s.failure_reasons),
                    }
                    for s in summaries
                ],
            }
        )
    except Exception as exc:
        result["status"] = "query_error"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:1000]

    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
