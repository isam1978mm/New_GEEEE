from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom

from app.pipeline.depth.interpolation import OPERATOR_CANDIDATES_SCHEMA

SIGNAL_NAME = "run_logRatio_dB_mean"
SIGNAL_UNITS = "dB"
CANONICAL_RASTER_NAME = "logRatio_dB.tif"
RUN_QUALITY_RELATIVE_PATH = Path("QA") / "run_quality" / "run_quality_summary.json"
EXTRACTION_SCHEMA = "operator_depth_signal_extraction_v1"


class OperatorSignalExtractionError(ValueError):
    """Raised when reviewed local signal extraction cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class ExtractedSignal:
    feature_id: str
    role: str
    signal_value: float
    signal_uncertainty: float
    valid_pixel_count: int
    mask_pixel_count: int
    raw_mask_pixel_count: int
    signal_median: float
    signal_minimum: float
    signal_maximum: float
    depth_min_m: float | None = None
    depth_best_m: float | None = None
    depth_max_m: float | None = None


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{description} does not exist")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatorSignalExtractionError(f"{description} is not readable JSON") from exc
    if not isinstance(payload, dict):
        raise OperatorSignalExtractionError(f"{description} must be a JSON object")
    return payload


def _prepare_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)


def _read_run_quality(run_dir: Path, *, allow_warning: bool) -> str:
    payload = _load_json_object(
        run_dir / RUN_QUALITY_RELATIVE_PATH,
        description="run-quality summary",
    )
    status = str(payload.get("status") or "UNKNOWN").strip().upper()
    is_usable = bool(payload.get("is_usable", False))
    supported = status == "PASS" and is_usable
    if allow_warning and status == "WARNING" and is_usable:
        supported = True
    if not supported:
        raise OperatorSignalExtractionError("run quality does not support signal extraction")
    return status


def _canonical_raster_path(run_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    raster_path = (run_dir / CANONICAL_RASTER_NAME).resolve()
    if run_dir not in raster_path.parents:
        raise OperatorSignalExtractionError("canonical signal raster escapes run directory")
    if not raster_path.is_file():
        raise FileNotFoundError(f"missing canonical signal raster: {CANONICAL_RASTER_NAME}")
    return raster_path


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise OperatorSignalExtractionError(f"missing feature property: {key}")
    return value


def _required_depth(payload: dict[str, Any], key: str) -> float:
    try:
        value = float(payload[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise OperatorSignalExtractionError(f"invalid anchor property: {key}") from exc
    if not isfinite(value) or value < 0:
        raise OperatorSignalExtractionError(f"anchor property must be finite and nonnegative: {key}")
    return value


def _validate_depth_range(properties: dict[str, Any]) -> tuple[float, float, float]:
    minimum = _required_depth(properties, "depth_min_m")
    best = _required_depth(properties, "depth_best_m")
    maximum = _required_depth(properties, "depth_max_m")
    if not minimum <= best <= maximum:
        raise OperatorSignalExtractionError(
            "anchor depth range must satisfy depth_min_m <= depth_best_m <= depth_max_m"
        )
    return minimum, best, maximum


def _erode_mask(mask: np.ndarray, pixels: int) -> np.ndarray:
    if pixels < 0:
        raise OperatorSignalExtractionError("erosion_pixels must be nonnegative")
    result = np.asarray(mask, dtype=bool).copy()
    height, width = result.shape
    for _ in range(pixels):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        neighbours = [
            padded[row_offset : row_offset + height, col_offset : col_offset + width]
            for row_offset in range(3)
            for col_offset in range(3)
        ]
        result = np.logical_and.reduce(neighbours)
    return result


def _normalise_geometry(geometry: Any, *, source_crs: str, target_crs: str) -> dict[str, Any]:
    if not isinstance(geometry, dict):
        raise OperatorSignalExtractionError("feature geometry must be a GeoJSON object")
    geometry_type = str(geometry.get("type") or "")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise OperatorSignalExtractionError("only Polygon and MultiPolygon features are supported")
    try:
        transformed = transform_geom(
            source_crs,
            target_crs,
            geometry,
            antimeridian_cutting=True,
            precision=9,
        )
    except Exception as exc:
        raise OperatorSignalExtractionError("feature geometry could not be transformed") from exc
    if not isinstance(transformed, dict):
        raise OperatorSignalExtractionError("transformed feature geometry is invalid")
    return transformed


def _parse_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("type") != "FeatureCollection":
        raise OperatorSignalExtractionError("polygon input must be a GeoJSON FeatureCollection")
    raw_features = payload.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise OperatorSignalExtractionError("polygon input must contain at least one feature")

    features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    anchor_count = 0
    for raw_feature in raw_features:
        if not isinstance(raw_feature, dict) or raw_feature.get("type") != "Feature":
            raise OperatorSignalExtractionError("invalid GeoJSON feature entry")
        properties = raw_feature.get("properties")
        if not isinstance(properties, dict):
            raise OperatorSignalExtractionError("feature properties must be a JSON object")
        feature_id = _required_text(properties, "feature_id")
        if feature_id in seen_ids:
            raise OperatorSignalExtractionError(f"duplicate feature_id: {feature_id}")
        seen_ids.add(feature_id)
        role = _required_text(properties, "role").lower()
        if role not in {"anchor", "candidate"}:
            raise OperatorSignalExtractionError("feature role must be anchor or candidate")
        depth_range = _validate_depth_range(properties) if role == "anchor" else None
        if role == "anchor":
            anchor_count += 1
        features.append(
            {
                "feature_id": feature_id,
                "role": role,
                "geometry": raw_feature.get("geometry"),
                "depth_range": depth_range,
            }
        )
    if anchor_count < 2:
        raise OperatorSignalExtractionError("at least two anchor polygons are required")
    return features


def _extract_one(
    *,
    feature: dict[str, Any],
    raster: np.ndarray,
    valid_raster: np.ndarray,
    transform: Any,
    raster_crs: str,
    source_crs: str,
    erosion_pixels: int,
    minimum_valid_pixels: int,
) -> tuple[ExtractedSignal, np.ndarray]:
    transformed_geometry = _normalise_geometry(
        feature["geometry"],
        source_crs=source_crs,
        target_crs=raster_crs,
    )
    raw_mask = geometry_mask(
        [transformed_geometry],
        out_shape=raster.shape,
        transform=transform,
        invert=True,
        all_touched=False,
    )
    raw_count = int(raw_mask.sum())
    eroded = _erode_mask(raw_mask, erosion_pixels)
    mask_count = int(eroded.sum())
    supported_mask = eroded & valid_raster
    values = raster[supported_mask].astype(np.float64, copy=False)
    valid_count = int(values.size)
    if raw_count <= 0:
        raise OperatorSignalExtractionError(
            f"feature does not intersect the raster grid: {feature['feature_id']}"
        )
    if mask_count < minimum_valid_pixels:
        raise OperatorSignalExtractionError(
            f"feature has fewer than {minimum_valid_pixels} pixels after erosion: "
            f"{feature['feature_id']}"
        )
    if valid_count < minimum_valid_pixels:
        raise OperatorSignalExtractionError(
            f"feature has fewer than {minimum_valid_pixels} valid signal pixels: "
            f"{feature['feature_id']}"
        )

    signal_value = float(values.mean())
    signal_uncertainty = float(values.std(ddof=1)) if values.size > 1 else 0.0
    depth_range = feature["depth_range"]
    extracted = ExtractedSignal(
        feature_id=feature["feature_id"],
        role=feature["role"],
        signal_value=signal_value,
        signal_uncertainty=signal_uncertainty,
        valid_pixel_count=valid_count,
        mask_pixel_count=mask_count,
        raw_mask_pixel_count=raw_count,
        signal_median=float(np.median(values)),
        signal_minimum=float(values.min()),
        signal_maximum=float(values.max()),
        depth_min_m=None if depth_range is None else depth_range[0],
        depth_best_m=None if depth_range is None else depth_range[1],
        depth_max_m=None if depth_range is None else depth_range[2],
    )
    return extracted, eroded


def _check_nonoverlap(masks: dict[str, np.ndarray]) -> None:
    feature_ids = list(masks)
    for left_index, left_id in enumerate(feature_ids):
        for right_id in feature_ids[left_index + 1 :]:
            overlap = int(np.logical_and(masks[left_id], masks[right_id]).sum())
            if overlap > 0:
                raise OperatorSignalExtractionError(
                    f"eroded feature interiors overlap: {left_id} and {right_id}"
                )


def _write_csv(path: Path, extracted: list[ExtractedSignal]) -> None:
    fields = [
        "feature_id",
        "role",
        "signal_name",
        "signal_units",
        "signal_value",
        "signal_uncertainty",
        "valid_pixel_count",
        "mask_pixel_count",
        "raw_mask_pixel_count",
        "signal_median",
        "signal_minimum",
        "signal_maximum",
        "depth_min_m",
        "depth_best_m",
        "depth_max_m",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in extracted:
            writer.writerow(
                {
                    "feature_id": row.feature_id,
                    "role": row.role,
                    "signal_name": SIGNAL_NAME,
                    "signal_units": SIGNAL_UNITS,
                    "signal_value": f"{row.signal_value:.9f}",
                    "signal_uncertainty": f"{row.signal_uncertainty:.9f}",
                    "valid_pixel_count": row.valid_pixel_count,
                    "mask_pixel_count": row.mask_pixel_count,
                    "raw_mask_pixel_count": row.raw_mask_pixel_count,
                    "signal_median": f"{row.signal_median:.9f}",
                    "signal_minimum": f"{row.signal_minimum:.9f}",
                    "signal_maximum": f"{row.signal_maximum:.9f}",
                    "depth_min_m": "" if row.depth_min_m is None else row.depth_min_m,
                    "depth_best_m": "" if row.depth_best_m is None else row.depth_best_m,
                    "depth_max_m": "" if row.depth_max_m is None else row.depth_max_m,
                }
            )


def extract_operator_depth_signals(
    *,
    run_dir: Path,
    polygons_path: Path,
    output_dir: Path,
    site_id: str,
    method_version: str,
    calibration_dataset_version: str,
    input_crs: str = "EPSG:4326",
    erosion_pixels: int = 2,
    minimum_valid_pixels: int = 20,
    allow_run_quality_warning: bool = False,
) -> dict[str, Any]:
    run_dir = Path(run_dir)
    polygons_path = Path(polygons_path)
    output_dir = Path(output_dir)
    if not run_dir.is_dir():
        raise FileNotFoundError("run directory does not exist")
    if not str(site_id).strip():
        raise OperatorSignalExtractionError("site_id is required")
    if not str(method_version).strip():
        raise OperatorSignalExtractionError("method_version is required")
    if not str(calibration_dataset_version).strip():
        raise OperatorSignalExtractionError("calibration_dataset_version is required")
    if minimum_valid_pixels <= 0:
        raise OperatorSignalExtractionError("minimum_valid_pixels must be positive")

    run_quality_status = _read_run_quality(
        run_dir,
        allow_warning=allow_run_quality_warning,
    )
    raster_path = _canonical_raster_path(run_dir)
    polygon_payload = _load_json_object(
        polygons_path,
        description="operator polygon input",
    )
    features = _parse_features(polygon_payload)
    _prepare_output_dir(output_dir)

    with rasterio.open(raster_path) as source:
        if source.count != 1:
            raise OperatorSignalExtractionError("canonical signal raster must contain one band")
        if source.crs is None:
            raise OperatorSignalExtractionError("canonical signal raster has no CRS")
        raster = source.read(1).astype(np.float64, copy=False)
        nodata = source.nodata
        valid_raster = np.isfinite(raster)
        if nodata is not None:
            valid_raster &= raster != nodata
        raster_crs = source.crs.to_string()
        raster_transform = source.transform
        raster_metadata = {
            "width": source.width,
            "height": source.height,
            "crs": raster_crs,
            "transform": list(source.transform)[:6],
            "nodata": nodata,
            "dtype": source.dtypes[0],
            "pixel_size_x": abs(float(source.transform.a)),
            "pixel_size_y": abs(float(source.transform.e)),
        }

    extracted: list[ExtractedSignal] = []
    masks: dict[str, np.ndarray] = {}
    for feature in features:
        row, mask = _extract_one(
            feature=feature,
            raster=raster,
            valid_raster=valid_raster,
            transform=raster_transform,
            raster_crs=raster_crs,
            source_crs=input_crs,
            erosion_pixels=erosion_pixels,
            minimum_valid_pixels=minimum_valid_pixels,
        )
        extracted.append(row)
        masks[row.feature_id] = mask
    _check_nonoverlap(masks)

    anchors = [row for row in extracted if row.role == "anchor"]
    candidates = [row for row in extracted if row.role == "candidate"]
    config = {
        "method_version": str(method_version).strip(),
        "calibration_dataset_version": str(calibration_dataset_version).strip(),
        "site_id": str(site_id).strip(),
        "validation_status": "provisional",
        "allow_run_quality_warning": allow_run_quality_warning,
        "signal_name": SIGNAL_NAME,
        "signal_units": SIGNAL_UNITS,
        "default_signal_uncertainty": 0.0,
        "warnings": [
            "operator_review_required",
            "signals_extracted_from_completed_run",
            "within_polygon_standard_deviation_used_for_candidate_uncertainty",
        ],
        "anchors": [
            {
                "anchor_id": row.feature_id,
                "signal_value": row.signal_value,
                "depth_min_m": row.depth_min_m,
                "depth_best_m": row.depth_best_m,
                "depth_max_m": row.depth_max_m,
                "warnings": [
                    "measured_local_anchor",
                    "signal_extracted_from_canonical_logRatio_dB",
                ],
            }
            for row in anchors
        ],
    }
    candidate_payload = {
        "schema_version": OPERATOR_CANDIDATES_SCHEMA,
        "candidates": [
            {
                "candidate_id": row.feature_id,
                "signal_name": SIGNAL_NAME,
                "signal_value": row.signal_value,
                "signal_uncertainty": row.signal_uncertainty,
            }
            for row in candidates
        ],
    }
    summary = {
        "schema_version": EXTRACTION_SCHEMA,
        "status": "signals_extracted_review_required",
        "source_raster": CANONICAL_RASTER_NAME,
        "signal_name": SIGNAL_NAME,
        "signal_units": SIGNAL_UNITS,
        "run_quality_status": run_quality_status,
        "input_crs": input_crs,
        "erosion_pixels": erosion_pixels,
        "minimum_valid_pixels": minimum_valid_pixels,
        "feature_count": len(extracted),
        "anchor_count": len(anchors),
        "candidate_count": len(candidates),
        "raster": raster_metadata,
        "geometry_copied_to_outputs": False,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "depth_estimation_executed": False,
        "package_built": False,
        "operator_review_required": True,
        "outputs": [
            "extracted_signals.csv",
            "operator_depth_config.json",
            "operator_depth_candidates.json",
            "extraction_summary.json",
        ],
    }

    _write_csv(output_dir / "extracted_signals.csv", extracted)
    (output_dir / "operator_depth_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "operator_depth_candidates.json").write_text(
        json.dumps(candidate_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "extraction_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract reviewed local anchor/candidate signals from a completed run's "
            "canonical logRatio_dB raster."
        )
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--polygons", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--method-version", required=True)
    parser.add_argument("--calibration-dataset-version", required=True)
    parser.add_argument("--input-crs", default="EPSG:4326")
    parser.add_argument("--erosion-pixels", type=int, default=2)
    parser.add_argument("--minimum-valid-pixels", type=int, default=20)
    parser.add_argument("--allow-run-quality-warning", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = extract_operator_depth_signals(
        run_dir=args.run_dir,
        polygons_path=args.polygons,
        output_dir=args.output_dir,
        site_id=args.site_id,
        method_version=args.method_version,
        calibration_dataset_version=args.calibration_dataset_version,
        input_crs=args.input_crs,
        erosion_pixels=args.erosion_pixels,
        minimum_valid_pixels=args.minimum_valid_pixels,
        allow_run_quality_warning=args.allow_run_quality_warning,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
