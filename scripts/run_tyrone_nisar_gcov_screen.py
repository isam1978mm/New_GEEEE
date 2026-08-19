#!/usr/bin/env python3
"""Run the frozen Tyrone NISAR GCOV Frequency-A screen.

Temporary experiment only. Scientific rules are frozen on main in
`data/tyrone_nisar_gcov_preregistration_2026-08-18.json`.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import fsspec
import numpy as np
import xarray as xr
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from shapely.geometry import mapping, shape
from shapely.ops import transform as geom_transform

OUT = Path("artifacts/tyrone_nisar_gcov_screen")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
VALUES = OUT / "plot_values.csv"
GEOMETRY_SOURCE = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
COLLECTION = "NISAR_L2_GCOV_PROVISIONAL_V1"
BASE = "https://nisar.asf.earthdatacloud.nasa.gov/NISAR"
GROUP = "/science/LSAR/GCOV/grids/frequencyA"
PLOTS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")
OUTSLOPE = ("TP1", "TP2", "TP3")
TOP = ("TP5", "TP6", "TP7")
PAIRS = (("TP1", "TP5"), ("TP2", "TP6"), ("TP3", "TP7"))
FEATURES = ("HH_DB", "HV_DB", "HH_MINUS_HV_DB")
MIN_VALID = 15
BUFFER_M = 10.0
GRANULES = (
    ("NISAR_L2_PR_GCOV_023_048_A_018_4005_DHDH_A_20260617T122615_20260617T122650_P05023_N_F_J_001", "ASCENDING"),
    ("NISAR_L2_PR_GCOV_024_027_D_072_4005_DHDH_A_20260628T015933_20260628T020007_P05023_N_F_J_001", "DESCENDING"),
    ("NISAR_L2_PR_GCOV_024_048_A_018_4005_DHDH_A_20260629T122615_20260629T122649_P05023_N_F_J_001", "ASCENDING"),
    ("NISAR_L2_PR_GCOV_025_027_D_072_4005_DHDH_A_20260710T015932_20260710T020007_P05023_N_F_J_001", "DESCENDING"),
    ("NISAR_L2_PR_GCOV_025_048_A_018_4005_DHDH_A_20260711T122614_20260711T122649_P05023_N_F_J_001", "ASCENDING"),
    ("NISAR_L2_PR_GCOV_026_027_D_072_4005_DHDH_A_20260722T015931_20260722T020006_P05023_N_F_J_001", "DESCENDING"),
    ("NISAR_L2_PR_GCOV_026_048_A_018_4005_DHDH_A_20260723T122613_20260723T122648_P05023_N_F_J_001", "ASCENDING"),
)


def save(obj: dict[str, Any]) -> None:
    RESULT.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def load_polygons() -> dict[str, Any]:
    src = json.loads(GEOMETRY_SOURCE.read_text(encoding="utf-8"))
    out = {}
    for feature in src["features"]:
        pid = str(feature.get("properties", {}).get("plot_id", ""))
        if pid in PLOTS:
            out[pid] = shape(feature["geometry"])
    if set(out) != set(PLOTS):
        raise RuntimeError("six-plot WGS84 geometry incomplete")
    return out


def url(granule: str) -> str:
    return f"{BASE}/{COLLECTION}/{granule}/{granule}.h5"


def epsg_from(ds: xr.Dataset) -> int:
    p = ds["projection"]
    value = p.attrs.get("epsg_code")
    if value is None:
        value = np.asarray(p.values).reshape(-1)[0]
    if isinstance(value, bytes):
        value = value.decode()
    return int(value)


def project_and_erode(polygons: dict[str, Any], epsg: int) -> dict[str, Any]:
    tx = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    out = {}
    for pid, poly in polygons.items():
        inner = geom_transform(tx.transform, poly).buffer(-BUFFER_M)
        if inner.is_empty or not inner.is_valid:
            raise RuntimeError(f"{pid}: invalid 10 m eroded polygon")
        out[pid] = inner
    return out


def axis_slice(axis: np.ndarray, lo: float, hi: float) -> slice:
    axis = np.asarray(axis, dtype=float)
    hit = np.flatnonzero((axis >= min(lo, hi)) & (axis <= max(lo, hi)))
    if not hit.size:
        a = int(np.argmin(np.abs(axis - lo)))
        b = int(np.argmin(np.abs(axis - hi)))
        i0, i1 = sorted((a, b))
    else:
        i0, i1 = int(hit.min()), int(hit.max())
    return slice(max(0, i0 - 2), min(axis.size, i1 + 3))


def north_up(arr: np.ndarray, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if x[0] > x[-1]:
        x = x[::-1]
        arr = arr[:, ::-1]
    if y[0] < y[-1]:
        y = y[::-1]
        arr = arr[::-1, :]
    return arr, x, y


def transform_from_centers(x: np.ndarray, y: np.ndarray) -> Affine:
    dx = float(np.median(np.diff(x)))
    dy = float(np.median(np.diff(y)))
    if dx <= 0 or dy >= 0:
        raise RuntimeError("unexpected GCOV coordinate orientation")
    return Affine(dx, 0, float(x[0] - dx / 2), 0, dy, float(y[0] - dy / 2))


def ordering(values: dict[str, float | None]) -> str:
    if any(values.get(p) is None for p in PLOTS):
        return "not_usable"
    a = [float(values[p]) for p in OUTSLOPE]
    b = [float(values[p]) for p in TOP]
    if a[0] < a[1] < a[2] and b[0] < b[1] < b[2]:
        return "increasing"
    if a[0] > a[1] > a[2] and b[0] > b[1] > b[2]:
        return "decreasing"
    return "no_support"


def read_acquisition(fs: Any, granule: str, flight: str, wgs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    h = fs.open(url(granule), cache_type="background", block_size=16 * 1024 * 1024)
    ds = None
    try:
        ds = xr.open_dataset(
            h,
            engine="h5netcdf",
            group=GROUP,
            phony_dims="sort",
            drop_variables=["listOfCovarianceTerms", "listOfPolarizations"],
            decode_timedelta=False,
        )
        for name in ("projection", "xCoordinates", "yCoordinates", "HHHH", "HVHV"):
            if name not in ds:
                raise RuntimeError(f"{granule}: missing {name}")
        epsg = epsg_from(ds)
        polys = project_and_erode(wgs, epsg)
        bounds = (
            min(g.bounds[0] for g in polys.values()), min(g.bounds[1] for g in polys.values()),
            max(g.bounds[2] for g in polys.values()), max(g.bounds[3] for g in polys.values()),
        )
        xall = np.asarray(ds.xCoordinates.values, dtype=float)
        yall = np.asarray(ds.yCoordinates.values, dtype=float)
        xs, ys = axis_slice(xall, bounds[0], bounds[2]), axis_slice(yall, bounds[1], bounds[3])
        x = np.asarray(ds.xCoordinates.isel(xCoordinates=xs).values, dtype=float)
        y = np.asarray(ds.yCoordinates.isel(yCoordinates=ys).values, dtype=float)
        hh = np.asarray(ds.HHHH.isel(yCoordinates=ys, xCoordinates=xs).values, dtype=float)
        hv = np.asarray(ds.HVHV.isel(yCoordinates=ys, xCoordinates=xs).values, dtype=float)
        hh, x, y = north_up(hh, x, y)
        hv, x2, y2 = north_up(hv, np.asarray(ds.xCoordinates.isel(xCoordinates=xs).values, dtype=float), np.asarray(ds.yCoordinates.isel(yCoordinates=ys).values, dtype=float))
        if not (np.array_equal(x, x2) and np.array_equal(y, y2)):
            raise RuntimeError("HH/HV coordinate mismatch")
        affine = transform_from_centers(x, y)
        hh_db = np.where(np.isfinite(hh) & (hh > 0), 10.0 * np.log10(hh), np.nan)
        hv_db = np.where(np.isfinite(hv) & (hv > 0), 10.0 * np.log10(hv), np.nan)
        arrays = {"HH_DB": hh_db, "HV_DB": hv_db, "HH_MINUS_HV_DB": hh_db - hv_db}
        rows, medians, counts = [], {f: {} for f in FEATURES}, {f: {} for f in FEATURES}
        for pid in PLOTS:
            mask = geometry_mask([mapping(polys[pid])], out_shape=hh.shape, transform=affine, invert=True, all_touched=False)
            for feature in FEATURES:
                v = arrays[feature][mask]
                v = v[np.isfinite(v)]
                n = int(v.size)
                median = float(np.median(v)) if n >= MIN_VALID else None
                medians[feature][pid] = median
                counts[feature][pid] = n
                rows.append({"granule": granule, "flight_direction": flight, "epsg": epsg, "feature": feature, "plot_id": pid, "valid_pixel_count": n, "median": median})
        directions = {f: ordering(medians[f]) for f in FEATURES}
        offsets = {}
        for feature in FEATURES:
            offsets[feature] = {}
            for out_pid, top_pid in PAIRS:
                a, b = medians[feature][out_pid], medians[feature][top_pid]
                offsets[feature][f"{top_pid}_minus_{out_pid}"] = None if a is None or b is None else float(b) - float(a)
        return rows, {"granule": granule, "flight_direction": flight, "epsg": epsg, "feature_directions": directions, "plot_medians": medians, "valid_pixel_counts": counts, "matched_depth_surface_offsets": offsets}
    finally:
        if ds is not None:
            ds.close()
        h.close()


def decide(feature: str, acquisitions: list[dict[str, Any]]) -> dict[str, Any]:
    dirs = [a["feature_directions"][feature] for a in acquisitions]
    if len(acquisitions) != 7 or any(d == "not_usable" for d in dirs):
        return {"feature": feature, "decision": "NISAR_GCOV_INSUFFICIENT_SUPPORT", "direction_counts": {d: dirs.count(d) for d in sorted(set(dirs))}}
    gates = []
    for selected in ("increasing", "decreasing"):
        overall = sum(d == selected for d in dirs)
        asc = sum(a["feature_directions"][feature] == selected for a in acquisitions if a["flight_direction"] == "ASCENDING")
        desc = sum(a["feature_directions"][feature] == selected for a in acquisitions if a["flight_direction"] == "DESCENDING")
        gates.append({"direction": selected, "overall_support": overall, "ascending_support": asc, "descending_support": desc, "passed": overall >= 5 and asc >= 3 and desc >= 2})
    passed = [g for g in gates if g["passed"]]
    return {"feature": feature, "decision": "NISAR_GCOV_DIRECT_CANDIDATE" if passed else "NISAR_GCOV_DIRECT_FAILED_CLOSE", "selected_direction": passed[0]["direction"] if passed else None, "direction_counts": {d: dirs.count(d) for d in sorted(set(dirs))}, "gate_evaluations": gates}


def main() -> int:
    base: dict[str, Any] = {
        "protocol": "tyrone_nisar_gcov_frequency_a_six_plot_screen_v1",
        "preregistration": "data/tyrone_nisar_gcov_preregistration_2026-08-18.json",
        "classifier_used": False, "nb_depth_used": False, "earth_engine_query_executed": False,
        "model_fitted": False, "calibration_record_created": False, "ui_modified": False,
        "app_depth_enabled": False,
    }
    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        base.update({"status": "AUTH_REQUIRED", "decision": "NISAR_GCOV_NOT_RUN_AUTH_REQUIRED", "reason": "EARTHDATA_TOKEN is not configured", "backscatter_values_inspected": False})
        save(base)
        print(json.dumps(base, indent=2))
        return 0
    wgs = load_polygons()
    try:
        # Implementation-only authentication path: pass the already-issued Earthdata
        # bearer token directly to the HTTPS range reader. This avoids the optional
        # earthaccess profile lookup and does not change any scientific rule.
        fs = fsspec.filesystem("https", headers={"Authorization": f"Bearer {token}"})
        rows, acquisitions = [], []
        for granule, flight in GRANULES:
            r, a = read_acquisition(fs, granule, flight, wgs)
            rows.extend(r)
            acquisitions.append(a)
        fields = ["granule", "flight_direction", "epsg", "feature", "plot_id", "valid_pixel_count", "median"]
        with VALUES.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        feature_results = {feature: decide(feature, acquisitions) for feature in FEATURES}
        candidates = [f for f, r in feature_results.items() if r["decision"] == "NISAR_GCOV_DIRECT_CANDIDATE"]
        if any(r["decision"] == "NISAR_GCOV_INSUFFICIENT_SUPPORT" for r in feature_results.values()):
            decision = "NISAR_GCOV_INSUFFICIENT_SUPPORT"
        elif candidates:
            decision = "NISAR_GCOV_DIRECT_CANDIDATE"
        else:
            decision = "NISAR_GCOV_DIRECT_FAILED_CLOSE"
        base.update({"status": "complete", "decision": decision, "backscatter_values_inspected": True, "candidate_features": candidates, "feature_results": feature_results, "acquisitions": acquisitions})
        save(base)
        print(json.dumps({"status": "complete", "decision": decision, "candidate_features": candidates, "feature_results": feature_results}, indent=2))
        return 0
    except Exception as exc:
        base.update({"status": "TECHNICAL_FAILURE", "decision": "NISAR_GCOV_NOT_EVALUATED_TECHNICAL_FAILURE", "backscatter_values_inspected": False, "error_type": type(exc).__name__, "error": str(exc)[:2000]})
        save(base)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
