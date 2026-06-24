from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio
from rasterio.transform import Affine

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.feature_stacks import SCIENCE_CORE_BANDS
from app.pipeline.stages.grid import GridSpec

FOCUS_MASK_TIF_NAME = "focus_zone_17m.tif"
FOCUS_MASK_NPY_NAME = "focus_zone_17m.npy"
FOCUS_WINDOW_NPY_NAME = "focus_zone_ai_ready_window.npy"
FOCUS_SUMMARY_JSON_NAME = "focus_zone_summary.json"
FOCUS_BAND_SUMMARY_CSV_NAME = "focus_zone_band_summary.csv"
FOCUS_PIXEL_REPORT_CSV_NAME = "AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv"
FOCUS_TARGET_REPORT_CSV_NAME = "AI_FOCUS_17M_TARGETS_V7_2.csv"
FOCUS_TARGET_GEOJSON_NAME = "AI_FOCUS_17M_TARGETS_V7_2.geojson"
FOCUS_DIR_PARTS = ("full_job", "focus")
FOCUS_SIZE_M = 17.0

FOCUS_ANALYSIS_BANDS = (
    "Secret_Gold_Halo",
    "Secret_Silver_Oxide",
    "Secret_Tunnel_Ceiling",
    "Secret_Thermal_Inertia",
    "Secret_Chemical_Protector",
    "Secret_Hidden_Doors",
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)

FOCUS_SECRET_LAYER_FILES = {
    "Secret_Gold_Halo": "AI_READY_640_Secret_Gold_Halo.tif",
    "Secret_Silver_Oxide": "AI_READY_640_Secret_Silver_Oxide.tif",
    "Secret_Tunnel_Ceiling": "AI_READY_640_Secret_Tunnel_Ceiling.tif",
    "Secret_Thermal_Inertia": "AI_READY_640_Secret_Thermal_Inertia.tif",
    "Secret_Chemical_Protector": "AI_READY_640_Secret_Chemical_Protector.tif",
    "Secret_Hidden_Doors": "AI_READY_640_Secret_Hidden_Doors.tif",
}

FOCUS_REPORT_BAND_FILES = {
    "REPORT_640_FINAL_Zero_Point_Targets": "REPORT_640_FINAL_Zero_Point_Targets_640.npy",
    "REPORT_640_Mass_Report": "REPORT_640_Mass_Report_640.npy",
    "REPORT_640_Pottery_Report": "REPORT_640_Pottery_Report_640.npy",
}


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(fieldnames=fieldnames, f=handle)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_ai_ready_support_stack(run_dir: Path) -> np.ndarray:
    path = run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.npy"
    if not path.is_file():
        raise StageError("Focus-mask stage requires ai_ready_support_stack.npy from feature_stacks.")
    return np.load(path).astype(np.float32)


def _load_tif(path: Path, *, grid_spec: GridSpec) -> np.ndarray:
    if not path.is_file():
        raise StageError(f"ROI focus analysis requires missing raster: {path.as_posix()}")
    with rasterio.open(path) as dataset:
        arr = dataset.read(1).astype(np.float32)
    if arr.shape != (grid_spec.size, grid_spec.size):
        raise StageError(f"ROI focus analysis raster {path.name} has shape {arr.shape}, expected {(grid_spec.size, grid_spec.size)}.")
    return arr


def _load_npy(path: Path, *, grid_spec: GridSpec) -> np.ndarray:
    if not path.is_file():
        raise StageError(f"ROI focus analysis requires missing array: {path.as_posix()}")
    arr = np.load(path).astype(np.float32)
    if arr.shape != (grid_spec.size, grid_spec.size):
        raise StageError(f"ROI focus analysis array {path.name} has shape {arr.shape}, expected {(grid_spec.size, grid_spec.size)}.")
    return arr


def load_focus_analysis_bands(run_dir: Path, *, grid_spec: GridSpec) -> dict[str, np.ndarray]:
    bands: dict[str, np.ndarray] = {}

    for notebook_name, filename in FOCUS_SECRET_LAYER_FILES.items():
        bands[notebook_name] = _load_tif(run_dir / "AI_READY_640" / filename, grid_spec=grid_spec)

    for notebook_name, filename in FOCUS_REPORT_BAND_FILES.items():
        bands[notebook_name] = _load_npy(run_dir / "NPY_RADAR_BANDS" / filename, grid_spec=grid_spec)

    return bands


def build_focus_mask_products(
    ai_ready_stack: np.ndarray,
    *,
    grid_spec: GridSpec,
    focus_size_m: float = FOCUS_SIZE_M,
) -> dict[str, object]:
    if ai_ready_stack.ndim != 3:
        raise StageError("Focus-mask stage requires a 3D ai_ready support stack.")
    if ai_ready_stack.shape[0] != grid_spec.size or ai_ready_stack.shape[1] != grid_spec.size:
        raise StageError("Focus-mask stage requires ai_ready support stack on the authoritative grid.")

    transform = grid_spec.transform
    pixel_size_m = float((abs(transform[0]) + abs(transform[4])) / 2.0)
    radius_px = float(focus_size_m) / pixel_size_m
    center_row = float(grid_spec.size) / 2.0
    center_col = float(grid_spec.size) / 2.0

    rows, cols = np.meshgrid(np.arange(grid_spec.size), np.arange(grid_spec.size), indexing="ij")
    dist_px = np.sqrt((rows.astype(np.float64) - center_row) ** 2 + (cols.astype(np.float64) - center_col) ** 2)
    mask = (dist_px <= radius_px).astype(np.float32)
    row_indices, col_indices = np.where(mask == 1.0)

    if row_indices.size == 0 or col_indices.size == 0:
        raise StageError("Focus-mask stage could not derive a non-empty focus zone from the configured grid.")

    row_min = int(row_indices.min())
    row_max = int(row_indices.max())
    col_min = int(col_indices.min())
    col_max = int(col_indices.max())
    cropped_window = ai_ready_stack[row_min : row_max + 1, col_min : col_max + 1, :].astype(np.float32)
    masked_window = cropped_window * mask[row_min : row_max + 1, col_min : col_max + 1, None]

    band_summary_rows: list[dict[str, object]] = []
    for index in range(ai_ready_stack.shape[-1]):
        channel = ai_ready_stack[:, :, index]
        values = channel[mask == 1.0]
        band_summary_rows.append(
            {
                "band_index": index,
                "band_name": SCIENCE_CORE_BANDS[index] if index < len(SCIENCE_CORE_BANDS) else f"band_{index}",
                "focus_mean": float(values.mean()) if values.size else "",
                "focus_min": float(values.min()) if values.size else "",
                "focus_max": float(values.max()) if values.size else "",
            }
        )

    summary = {
        "stage": "focus_mask",
        "focus_size_m": float(focus_size_m),
        "mask_pixel_count": int(mask.sum()),
        "window_shape": [int(masked_window.shape[0]), int(masked_window.shape[1]), int(masked_window.shape[2])],
        "analysis_source": "ai_ready_support_stack",
        "public_safe": False,
    }
    return {
        "mask": mask,
        "masked_window": masked_window,
        "summary": summary,
        "band_summary_rows": band_summary_rows,
    }


def _robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros_like(values, dtype=np.float64)

    med = np.nanmedian(finite)
    mad = np.nanmedian(np.abs(finite - med))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < 1e-9:
        std = np.nanstd(finite)
        if not np.isfinite(std) or std < 1e-9:
            return np.zeros_like(values, dtype=np.float64)
        result = (values - np.nanmean(finite)) / std
    else:
        result = (values - med) / scale

    result[~np.isfinite(result)] = 0.0
    return result.astype(np.float64, copy=False)


def _mask_values(arr: np.ndarray, mask: np.ndarray, *, nodata: float) -> np.ndarray:
    values = arr[mask].astype(np.float64)
    values[~np.isfinite(values)] = np.nan
    values[values == float(nodata)] = np.nan
    return values


def _score_confidence(score: float, scores: list[float]) -> str:
    if not scores:
        return "0.0%"
    finite_scores = [s for s in scores if np.isfinite(s)]
    if not finite_scores:
        return "0.0%"
    rank_fraction = sum(s <= score for s in finite_scores) / float(len(finite_scores))
    return f"{rank_fraction * 100.0:.1f}%"


def _classify_target(row: dict[str, object], medians: dict[str, float]) -> str:
    g = float(row["Secret_Gold_Halo"])
    td = float(row["Secret_Tunnel_Ceiling"])
    th = float(row["Secret_Thermal_Inertia"])
    hd = float(row["Secret_Hidden_Doors"])
    ms = float(row["REPORT_640_Mass_Report"])
    pt = float(row["REPORT_640_Pottery_Report"])

    if g >= medians["Secret_Gold_Halo"] and ms >= medians["REPORT_640_Mass_Report"]:
        return "Priority A ? Metallic/High-density focus"
    if hd >= medians["Secret_Hidden_Doors"] and td >= medians["Secret_Tunnel_Ceiling"]:
        return "Priority B ? Structural/void-related focus"
    if pt >= medians["REPORT_640_Pottery_Report"]:
        return "Priority C ? Pottery/material concentration"
    if th >= medians["Secret_Thermal_Inertia"]:
        return "Priority D ? Thermal contrast focus"
    return "Priority E ? Comparative anomaly inside 17m"


def build_focus_roi_analysis_products(
    *,
    focus_mask: np.ndarray,
    analysis_bands: dict[str, np.ndarray],
    grid_spec: GridSpec,
) -> dict[str, object]:
    mask_bool = focus_mask.astype(bool)
    rows, cols = np.where(mask_bool)
    if rows.size == 0:
        raise StageError("ROI-constrained focus analysis requires a non-empty 17m focus mask.")

    missing = [name for name in FOCUS_ANALYSIS_BANDS if name not in analysis_bands]
    if missing:
        raise StageError(f"ROI-constrained focus analysis is missing required bands: {', '.join(missing)}")

    z_bands: dict[str, np.ndarray] = {}
    for name in FOCUS_ANALYSIS_BANDS:
        arr = analysis_bands[name].astype(np.float32, copy=False)
        vals = _mask_values(arr, mask_bool, nodata=grid_spec.nodata)
        zvals = _robust_z(vals)
        tmp = np.full(arr.shape, np.nan, dtype=np.float64)
        tmp[mask_bool] = zvals
        z_bands[name] = tmp

    score = (
        1.20 * np.nan_to_num(z_bands["Secret_Gold_Halo"], nan=0.0)
        + 1.00 * np.nan_to_num(z_bands["Secret_Silver_Oxide"], nan=0.0)
        + 0.90 * np.nan_to_num(z_bands["Secret_Hidden_Doors"], nan=0.0)
        + 0.90 * np.nan_to_num(z_bands["Secret_Tunnel_Ceiling"], nan=0.0)
        + 0.80 * np.nan_to_num(z_bands["Secret_Thermal_Inertia"], nan=0.0)
        + 0.60 * np.nan_to_num(z_bands["Secret_Chemical_Protector"], nan=0.0)
        + 0.80 * np.nan_to_num(z_bands["REPORT_640_Mass_Report"], nan=0.0)
        + 0.60 * np.nan_to_num(z_bands["REPORT_640_Pottery_Report"], nan=0.0)
        + 0.50 * np.nan_to_num(z_bands["REPORT_640_FINAL_Zero_Point_Targets"], nan=0.0)
    )
    score[~mask_bool] = np.nan

    affine = Affine(*grid_spec.transform)
    pixel_records: list[dict[str, object]] = []
    for r, c in zip(rows, cols):
        x, y = rasterio.transform.xy(affine, int(r), int(c), offset="center")
        record: dict[str, object] = {
            "row": int(r),
            "col": int(c),
            "UTM_E": round(float(x), 3),
            "UTM_N": round(float(y), 3),
        }
        for name in FOCUS_ANALYSIS_BANDS:
            record[name] = float(analysis_bands[name][r, c])
        record["ROI_Composite_Score"] = float(score[r, c])
        pixel_records.append(record)

    pixel_records.sort(key=lambda item: float(item["ROI_Composite_Score"]), reverse=True)
    target_source = pixel_records[: min(5, len(pixel_records))]
    medians = {
        name: float(np.nanmedian([float(row[name]) for row in target_source])) if target_source else 0.0
        for name in FOCUS_ANALYSIS_BANDS
    }
    scores = [float(row["ROI_Composite_Score"]) for row in target_source]

    target_records: list[dict[str, object]] = []
    for index, source in enumerate(target_source, start=1):
        target = {
            "Target_ID": index,
            "row": source["row"],
            "col": source["col"],
            "UTM_E": source["UTM_E"],
            "UTM_N": source["UTM_N"],
            "Classification": _classify_target(source, medians),
            "Confidence": _score_confidence(float(source["ROI_Composite_Score"]), scores),
            "ROI_Composite_Score": source["ROI_Composite_Score"],
        }
        for name in FOCUS_ANALYSIS_BANDS:
            target[name] = source[name]
        target_records.append(target)

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["UTM_E"]), float(row["UTM_N"])]},
            "properties": {
                "Target_ID": int(row["Target_ID"]),
                "Classification": row["Classification"],
                "Confidence": row["Confidence"],
                "ROI_Composite_Score": float(row["ROI_Composite_Score"]),
            },
        }
        for row in target_records
    ]

    return {
        "pixel_records": pixel_records,
        "target_records": target_records,
        "target_geojson": {"type": "FeatureCollection", "features": features},
    }


def write_focus_mask_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    mask = products["mask"]
    masked_window = products["masked_window"]
    summary = products["summary"]
    band_summary_rows = products["band_summary_rows"]
    pixel_records = products["pixel_records"]
    target_records = products["target_records"]
    target_geojson = products["target_geojson"]
    assert isinstance(mask, np.ndarray)
    assert isinstance(masked_window, np.ndarray)
    assert isinstance(summary, dict)
    assert isinstance(band_summary_rows, list)
    assert isinstance(pixel_records, list)
    assert isinstance(target_records, list)
    assert isinstance(target_geojson, dict)

    focus_dir = run_dir.joinpath(*FOCUS_DIR_PARTS)
    focus_dir.mkdir(parents=True, exist_ok=True)

    mask_tif_path = focus_dir / FOCUS_MASK_TIF_NAME
    mask_npy_path = focus_dir / FOCUS_MASK_NPY_NAME
    focus_window_path = focus_dir / FOCUS_WINDOW_NPY_NAME
    summary_path = focus_dir / FOCUS_SUMMARY_JSON_NAME
    band_summary_path = focus_dir / FOCUS_BAND_SUMMARY_CSV_NAME
    pixel_report_path = focus_dir / FOCUS_PIXEL_REPORT_CSV_NAME
    target_report_path = focus_dir / FOCUS_TARGET_REPORT_CSV_NAME
    target_geojson_path = focus_dir / FOCUS_TARGET_GEOJSON_NAME

    _write_focus_mask_tif(mask_tif_path, mask, grid_spec)
    np.save(mask_npy_path, mask.astype(np.float32))
    np.save(focus_window_path, masked_window.astype(np.float32))
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(band_summary_path, ["band_index", "band_name", "focus_mean", "focus_min", "focus_max"], band_summary_rows)

    pixel_fields = ["row", "col", "UTM_E", "UTM_N", *FOCUS_ANALYSIS_BANDS, "ROI_Composite_Score"]
    target_fields = [
        "Target_ID",
        "row",
        "col",
        "UTM_E",
        "UTM_N",
        "Classification",
        "Confidence",
        "ROI_Composite_Score",
        *FOCUS_ANALYSIS_BANDS,
    ]
    _write_csv(pixel_report_path, pixel_fields, pixel_records)
    _write_csv(target_report_path, target_fields, target_records)
    target_geojson_path.write_text(json.dumps(target_geojson, indent=2, sort_keys=True), encoding="utf-8")

    write_raster_sidecar(
        mask_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=0.0,
        dtype="uint8",
        shape=mask.shape,
    )

    return {
        "focus_mask_tif": mask_tif_path,
        "focus_mask_npy": mask_npy_path,
        "focus_window_npy": focus_window_path,
        "focus_summary_json": summary_path,
        "focus_band_summary_csv": band_summary_path,
        "focus_pixel_report_csv": pixel_report_path,
        "focus_target_report_csv": target_report_path,
        "focus_target_geojson": target_geojson_path,
    }


def _write_focus_mask_tif(path: Path, mask: np.ndarray, grid_spec: GridSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=int(mask.shape[0]),
        width=int(mask.shape[1]),
        count=1,
        dtype="uint8",
        crs=grid_spec.crs,
        transform=Affine(*grid_spec.transform),
        nodata=0,
        compress="deflate",
    ) as dataset:
        dataset.write(mask.astype(np.uint8, copy=False), 1)


class FocusMaskStage(Stage):
    name = "focus_mask"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook location-bearing 17m focus-region outputs with local-only FILESYSTEM_ONLY mask and ROI analysis products."

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        ai_ready_stack = load_ai_ready_support_stack(context.run_dir)
        products = build_focus_mask_products(ai_ready_stack, grid_spec=self.grid_spec)
        analysis_bands = load_focus_analysis_bands(context.run_dir, grid_spec=self.grid_spec)
        products.update(
            build_focus_roi_analysis_products(
                focus_mask=products["mask"],
                analysis_bands=analysis_bands,
                grid_spec=self.grid_spec,
            )
        )
        outputs = write_focus_mask_outputs(context.run_dir, self.grid_spec, products)
        artifacts = [
            build_stage_artifact(
                name="focus_zone_17m_tif",
                relative_path=outputs["focus_mask_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_17m_npy",
                relative_path=outputs["focus_mask_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_ai_ready_window",
                relative_path=outputs["focus_window_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_window_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_summary",
                relative_path=outputs["focus_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_band_summary",
                relative_path=outputs["focus_band_summary_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_band_summary_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_pixel_report_v7_2",
                relative_path=outputs["focus_pixel_report_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_pixel_report_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_targets_v7_2",
                relative_path=outputs["focus_target_report_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_target_report_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_targets_geojson_v7_2",
                relative_path=outputs["focus_target_geojson"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_target_geojson"].stat().st_size,
                http_servable=False,
            ),
        ]
        summary = products["summary"]
        assert isinstance(summary, dict)
        target_records = products["target_records"]
        assert isinstance(target_records, list)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "focus_size_m": float(summary["focus_size_m"]),
                "mask_pixel_count": int(summary["mask_pixel_count"]),
                "window_shape": summary["window_shape"],
                "roi_pixel_report": FOCUS_PIXEL_REPORT_CSV_NAME,
                "roi_target_report": FOCUS_TARGET_REPORT_CSV_NAME,
                "roi_target_geojson": FOCUS_TARGET_GEOJSON_NAME,
                "target_count": len(target_records),
            },
        )
