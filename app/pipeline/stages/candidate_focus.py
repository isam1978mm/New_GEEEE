from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from pyproj import Transformer
from rasterio.transform import Affine

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.classifier import CLASSIFICATIONS_CSV_NAME, CLASSIFIER_OUTPUT_DIRNAME
from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.focus_mask import (
    FOCUS_ANALYSIS_BANDS,
    FOCUS_RADIUS_M,
    FOCUS_REPORT_BAND_FILES,
    FOCUS_SECRET_LAYER_FILES,
    build_core_ring_scene_decision_products,
    build_focus_roi_analysis_products,
    build_hard_type_classifier_products,
    load_ai_ready_support_stack,
    load_focus_analysis_bands,
)
from app.pipeline.stages.grid import GridSpec, grid_spec_from_manifest
from app.services.grid import GridManifest

CANDIDATE_FOCUS_DIR_PARTS = ("full_job", "candidate_focus")
CANDIDATE_FOCUS_INDEX_JSON_NAME = "candidate_focus_index.json"
CANDIDATE_FOCUS_INDEX_CSV_NAME = "candidate_focus_index.csv"
CANDIDATE_FOCUS_INDEX_GEOJSON_NAME = "candidate_focus_index.geojson"
CANDIDATE_FOCUS_SUMMARY_NAME = "candidate_focus_summary.json"
CANDIDATE_FOCUS_MASK_NPY_NAME = "candidate_focus_mask.npy"
CANDIDATE_FOCUS_MASK_TIF_NAME = "candidate_focus_mask.tif"
CANDIDATE_FOCUS_WINDOW_NPY_NAME = "candidate_focus_ai_ready_window.npy"
CANDIDATE_FOCUS_PIXEL_REPORT_NAME = "candidate_focus_pixel_report.csv"
CANDIDATE_FOCUS_TARGETS_NAME = "candidate_focus_targets.csv"
CANDIDATE_FOCUS_TARGETS_GEOJSON_NAME = "candidate_focus_targets.geojson"
CANDIDATE_FOCUS_HARD_JSON_NAME = "candidate_focus_hard_classifier.json"
CANDIDATE_FOCUS_HARD_CSV_NAME = "candidate_focus_hard_classifier.csv"
CANDIDATE_FOCUS_CORE_RING_JSON_NAME = "candidate_focus_core_ring_scene.json"
CANDIDATE_FOCUS_CORE_RING_CSV_NAME = "candidate_focus_core_ring_scene.csv"
DEFAULT_CANDIDATE_FOCUS_TOP_N = 3
MAX_CANDIDATE_FOCUS_TOP_N = 10
CANDIDATE_FOCUS_SCHEMA = "candidate_focus_index_v1"
CANDIDATE_FOCUS_GEOMETRY_CONTRACT = "circular_mask_radius_m_centered_on_ranked_candidate"
SCIENTIFIC_WARNING = (
    "Candidate, anomaly and classifier scores are screening evidence only; "
    "they are not physical confirmation of an underground object and do not provide numerical depth."
)


@dataclass(frozen=True, slots=True)
class CandidateSelection:
    rank: int
    candidate_id: str
    object_id: int
    cluster_id: int
    row_min: int
    row_max: int
    col_min: int
    col_max: int
    source_score: float
    review_order: int
    finding_label: str

    @property
    def center_row(self) -> float:
        return (float(self.row_min) + float(self.row_max)) / 2.0

    @property
    def center_col(self) -> float:
        return (float(self.col_min) + float(self.col_max)) / 2.0


def candidate_focus_inputs_ready(run_dir: Path) -> bool:
    required = [
        run_dir / "grid_manifest.json",
        run_dir / CLASSIFIER_OUTPUT_DIRNAME / CLASSIFICATIONS_CSV_NAME,
        run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.npy",
    ]
    required.extend(run_dir / "AI_READY_640" / filename for filename in FOCUS_SECRET_LAYER_FILES.values())
    required.extend(run_dir / filename for filename in FOCUS_REPORT_BAND_FILES.values())
    return all(path.is_file() for path in required)


def _safe_int(value: Any, *, field: str) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError) as exc:
        raise StageError(f"Candidate Focus requires integer classifier field {field}.") from exc


def _safe_float(value: Any, *, field: str) -> float:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError) as exc:
        raise StageError(f"Candidate Focus requires numeric classifier field {field}.") from exc
    if not np.isfinite(parsed):
        raise StageError(f"Candidate Focus requires finite classifier field {field}.")
    return parsed


def _effective_top_n(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_CANDIDATE_FOCUS_TOP_N
    return max(1, min(MAX_CANDIDATE_FOCUS_TOP_N, parsed))


def select_candidate_focuses(run_dir: Path, *, top_n: int) -> list[CandidateSelection]:
    path = run_dir / CLASSIFIER_OUTPUT_DIRNAME / CLASSIFICATIONS_CSV_NAME
    if not path.is_file():
        raise StageError("Candidate Focus requires canonical classifier/classifications.csv.")

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    parsed: list[dict[str, Any]] = []
    for row in rows:
        object_id = _safe_int(row.get("object_id"), field="object_id")
        cluster_id = _safe_int(row.get("cluster_id"), field="cluster_id")
        row_min = _safe_int(row.get("row_min"), field="row_min")
        row_max = _safe_int(row.get("row_max"), field="row_max")
        col_min = _safe_int(row.get("col_min"), field="col_min")
        col_max = _safe_int(row.get("col_max"), field="col_max")
        source_score = _safe_float(row.get("finding_score", row.get("class_score")), field="finding_score")
        review_order = _safe_int(row.get("review_order", object_id), field="review_order")
        parsed.append(
            {
                "object_id": object_id,
                "cluster_id": cluster_id,
                "row_min": row_min,
                "row_max": row_max,
                "col_min": col_min,
                "col_max": col_max,
                "source_score": source_score,
                "review_order": review_order,
                "finding_label": str(row.get("finding_label", row.get("class_id", "candidate"))),
            }
        )

    parsed.sort(key=lambda item: (-float(item["source_score"]), int(item["review_order"]), int(item["object_id"])))
    selections: list[CandidateSelection] = []
    for rank, item in enumerate(parsed[: _effective_top_n(top_n)], start=1):
        selections.append(
            CandidateSelection(
                rank=rank,
                candidate_id=f"object_{int(item['object_id'])}",
                object_id=int(item["object_id"]),
                cluster_id=int(item["cluster_id"]),
                row_min=int(item["row_min"]),
                row_max=int(item["row_max"]),
                col_min=int(item["col_min"]),
                col_max=int(item["col_max"]),
                source_score=float(item["source_score"]),
                review_order=int(item["review_order"]),
                finding_label=str(item["finding_label"]),
            )
        )
    return selections


def load_candidate_focus_grid_spec(run_dir: Path) -> GridSpec:
    path = run_dir / "grid_manifest.json"
    if not path.is_file():
        raise StageError("Candidate Focus requires grid_manifest.json.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = GridManifest.model_validate(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise StageError("Candidate Focus could not read the authoritative grid manifest.") from exc
    return grid_spec_from_manifest(manifest)


def build_candidate_focus_mask(
    *,
    grid_spec: GridSpec,
    center_row: float,
    center_col: float,
    focus_radius_m: float = FOCUS_RADIUS_M,
) -> np.ndarray:
    if focus_radius_m <= 0:
        raise StageError("Candidate Focus radius must be positive.")
    pixel_size_m = float((abs(grid_spec.transform[0]) + abs(grid_spec.transform[4])) / 2.0)
    if pixel_size_m <= 0:
        raise StageError("Candidate Focus requires a positive authoritative pixel size.")
    rows, cols = np.meshgrid(np.arange(grid_spec.size), np.arange(grid_spec.size), indexing="ij")
    radius_px = float(focus_radius_m) / pixel_size_m
    dist_px = np.sqrt(
        (rows.astype(np.float64) - float(center_row)) ** 2
        + (cols.astype(np.float64) - float(center_col)) ** 2
    )
    mask = dist_px <= radius_px
    if not bool(mask.any()):
        raise StageError("Candidate Focus produced an empty focus mask.")
    return mask


def _candidate_center_coordinates(selection: CandidateSelection, grid_spec: GridSpec) -> dict[str, float]:
    affine = Affine(*grid_spec.transform)
    x, y = affine * (selection.center_col + 0.5, selection.center_row + 0.5)
    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(float(x), float(y))
    return {
        "utm_e": round(float(x), 3),
        "utm_n": round(float(y), 3),
        "lon": round(float(lon), 8),
        "lat": round(float(lat), 8),
    }


def _crop_masked_window(stack: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rows, cols = np.where(mask)
    if rows.size == 0:
        raise StageError("Candidate Focus cannot crop an empty mask.")
    row_min, row_max = int(rows.min()), int(rows.max())
    col_min, col_max = int(cols.min()), int(cols.max())
    crop = stack[row_min : row_max + 1, col_min : col_max + 1, :].astype(np.float32)
    crop_mask = mask[row_min : row_max + 1, col_min : col_max + 1, None]
    return np.where(crop_mask, crop, 0.0).astype(np.float32)


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], *, fieldnames: list[str] | None = None) -> None:
    materialized = list(rows)
    if fieldnames is None:
        fieldnames = list(materialized[0].keys()) if materialized else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def _artifact(name: str, path: Path, run_dir: Path):
    return build_stage_artifact(
        name=name,
        relative_path=path.relative_to(run_dir).as_posix(),
        artifact_class=ArtifactClass.FILESYSTEM_ONLY,
        size_bytes=path.stat().st_size,
        http_servable=False,
    )


def _candidate_dir_name(selection: CandidateSelection) -> str:
    return f"candidate_{selection.rank:02d}_{selection.candidate_id}"


def _enrich_target_geojson(payload: dict[str, Any], selection: CandidateSelection) -> dict[str, Any]:
    enriched = json.loads(json.dumps(payload))
    enriched["focus_kind"] = "candidate_focus"
    enriched["candidate_id"] = selection.candidate_id
    enriched["candidate_rank"] = selection.rank
    for feature in enriched.get("features", []):
        props = feature.setdefault("properties", {})
        props["focus_kind"] = "candidate_focus"
        props["candidate_id"] = selection.candidate_id
        props["candidate_rank"] = selection.rank
        props["source_object_id"] = selection.object_id
        props["source_cluster_id"] = selection.cluster_id
        props["source_score"] = selection.source_score
    return enriched


def run_candidate_focus_analysis(
    *,
    context: StageContext,
    top_n: int | None = None,
) -> StageResult:
    run_dir = context.run_dir
    grid_spec = load_candidate_focus_grid_spec(run_dir)
    configured_top_n = _effective_top_n(
        top_n if top_n is not None else getattr(context.settings, "candidate_focus_top_n", DEFAULT_CANDIDATE_FOCUS_TOP_N)
    )
    selections = select_candidate_focuses(run_dir, top_n=configured_top_n)
    output_root = run_dir.joinpath(*CANDIDATE_FOCUS_DIR_PARTS)
    output_root.mkdir(parents=True, exist_ok=True)

    analysis_bands = load_focus_analysis_bands(run_dir, grid_spec=grid_spec) if selections else {}
    support_stack = load_ai_ready_support_stack(run_dir) if selections else None
    if support_stack is not None and support_stack.shape[:2] != (grid_spec.size, grid_spec.size):
        raise StageError("Candidate Focus support stack does not match the authoritative grid.")

    artifacts = []
    index_rows: list[dict[str, Any]] = []
    index_features: list[dict[str, Any]] = []

    for selection in selections:
        mask = build_candidate_focus_mask(
            grid_spec=grid_spec,
            center_row=selection.center_row,
            center_col=selection.center_col,
            focus_radius_m=FOCUS_RADIUS_M,
        )
        coords = _candidate_center_coordinates(selection, grid_spec)
        roi_products = build_focus_roi_analysis_products(
            focus_mask=mask,
            analysis_bands=analysis_bands,
            grid_spec=grid_spec,
        )
        hard_products = build_hard_type_classifier_products(
            focus_mask=mask,
            analysis_bands=analysis_bands,
            grid_spec=grid_spec,
        )
        core_products = build_core_ring_scene_decision_products(
            focus_mask=mask,
            analysis_bands=analysis_bands,
            grid_spec=grid_spec,
        )
        candidate_dir = output_root / _candidate_dir_name(selection)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "schema": "candidate_focus_summary_v1",
            "focus_kind": "candidate_focus",
            "candidate_id": selection.candidate_id,
            "candidate_rank": selection.rank,
            "source_object_id": selection.object_id,
            "source_cluster_id": selection.cluster_id,
            "source_score": selection.source_score,
            "source_review_order": selection.review_order,
            "source_finding_label": selection.finding_label,
            "source_bbox_pixels": {
                "row_min": selection.row_min,
                "row_max": selection.row_max,
                "col_min": selection.col_min,
                "col_max": selection.col_max,
            },
            "center_pixel": {"row": selection.center_row, "col": selection.center_col},
            "center_projected": {"easting": coords["utm_e"], "northing": coords["utm_n"], "crs": grid_spec.crs},
            "center_wgs84": {"lat": coords["lat"], "lon": coords["lon"]},
            "focus_radius_m": float(FOCUS_RADIUS_M),
            "focus_diameter_m": float(FOCUS_RADIUS_M * 2.0),
            "focus_geometry_contract": CANDIDATE_FOCUS_GEOMETRY_CONTRACT,
            "mask_pixel_count": int(mask.sum()),
            "analysis_bands": list(FOCUS_ANALYSIS_BANDS),
            "source_classifier_contract": "existing_classifier_outputs_read_only",
            "scientific_warning": SCIENTIFIC_WARNING,
        }
        summary_path = candidate_dir / CANDIDATE_FOCUS_SUMMARY_NAME
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

        mask_npy_path = candidate_dir / CANDIDATE_FOCUS_MASK_NPY_NAME
        mask_tif_path = candidate_dir / CANDIDATE_FOCUS_MASK_TIF_NAME
        window_npy_path = candidate_dir / CANDIDATE_FOCUS_WINDOW_NPY_NAME
        np.save(mask_npy_path, mask.astype(np.uint8))
        write_georeferenced_raster(mask_tif_path, mask.astype(np.float32), grid_spec)
        write_raster_sidecar(
            mask_tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=mask.shape,
        )
        assert support_stack is not None
        np.save(window_npy_path, _crop_masked_window(support_stack, mask))

        pixel_path = candidate_dir / CANDIDATE_FOCUS_PIXEL_REPORT_NAME
        target_path = candidate_dir / CANDIDATE_FOCUS_TARGETS_NAME
        target_geojson_path = candidate_dir / CANDIDATE_FOCUS_TARGETS_GEOJSON_NAME
        hard_json_path = candidate_dir / CANDIDATE_FOCUS_HARD_JSON_NAME
        hard_csv_path = candidate_dir / CANDIDATE_FOCUS_HARD_CSV_NAME
        core_json_path = candidate_dir / CANDIDATE_FOCUS_CORE_RING_JSON_NAME
        core_csv_path = candidate_dir / CANDIDATE_FOCUS_CORE_RING_CSV_NAME

        pixel_rows = list(roi_products["pixel_records"])
        target_rows = list(roi_products["target_records"])
        _write_csv(pixel_path, pixel_rows)
        _write_csv(target_path, target_rows)
        target_geojson = _enrich_target_geojson(dict(roi_products["target_geojson"]), selection)
        target_geojson_path.write_text(json.dumps(target_geojson, indent=2, sort_keys=True), encoding="utf-8")
        hard_record = dict(hard_products["hard_type_record"])
        hard_payload = dict(hard_products["hard_type_json"])
        hard_payload.update(
            {
                "focus_kind": "candidate_focus",
                "candidate_id": selection.candidate_id,
                "candidate_rank": selection.rank,
                "scientific_warning": SCIENTIFIC_WARNING,
            }
        )
        _write_csv(hard_csv_path, [hard_record])
        hard_json_path.write_text(json.dumps(hard_payload, indent=2, sort_keys=True), encoding="utf-8")
        core_record = dict(core_products["core_ring_scene_record"])
        core_payload = dict(core_products["core_ring_scene_json"])
        core_payload.update(
            {
                "focus_kind": "candidate_focus",
                "candidate_id": selection.candidate_id,
                "candidate_rank": selection.rank,
                "scientific_warning": SCIENTIFIC_WARNING,
            }
        )
        _write_csv(core_csv_path, [core_record])
        core_json_path.write_text(json.dumps(core_payload, indent=2, sort_keys=True), encoding="utf-8")

        candidate_paths = [
            summary_path,
            mask_npy_path,
            mask_tif_path,
            window_npy_path,
            pixel_path,
            target_path,
            target_geojson_path,
            hard_json_path,
            hard_csv_path,
            core_json_path,
            core_csv_path,
        ]
        for path in candidate_paths:
            artifacts.append(_artifact(f"candidate_focus_{selection.rank:02d}_{path.stem}", path, run_dir))

        index_row = {
            "candidate_rank": selection.rank,
            "candidate_id": selection.candidate_id,
            "object_id": selection.object_id,
            "cluster_id": selection.cluster_id,
            "source_score": selection.source_score,
            "source_review_order": selection.review_order,
            "finding_label": selection.finding_label,
            "row_min": selection.row_min,
            "row_max": selection.row_max,
            "col_min": selection.col_min,
            "col_max": selection.col_max,
            "center_row": selection.center_row,
            "center_col": selection.center_col,
            "utm_e": coords["utm_e"],
            "utm_n": coords["utm_n"],
            "lon": coords["lon"],
            "lat": coords["lat"],
            "focus_radius_m": float(FOCUS_RADIUS_M),
            "focus_diameter_m": float(FOCUS_RADIUS_M * 2.0),
            "mask_pixel_count": int(mask.sum()),
            "relative_dir": candidate_dir.relative_to(run_dir).as_posix(),
        }
        index_rows.append(index_row)
        index_features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [coords["lon"], coords["lat"]]},
                "properties": {
                    **{key: value for key, value in index_row.items() if key not in {"lon", "lat"}},
                    "focus_kind": "candidate_focus",
                    "scientific_warning": SCIENTIFIC_WARNING,
                },
            }
        )

    index_payload = {
        "schema": CANDIDATE_FOCUS_SCHEMA,
        "focus_kind": "candidate_focus",
        "source": "classifier/classifications.csv",
        "selection_contract": "descending_finding_score_then_review_order_then_object_id",
        "requested_top_n": configured_top_n,
        "selected_count": len(index_rows),
        "focus_radius_m": float(FOCUS_RADIUS_M),
        "focus_diameter_m": float(FOCUS_RADIUS_M * 2.0),
        "focus_geometry_contract": CANDIDATE_FOCUS_GEOMETRY_CONTRACT,
        "user_focus_unchanged": True,
        "classifier_behavior_changed": False,
        "scientific_warning": SCIENTIFIC_WARNING,
        "candidates": index_rows,
    }
    index_json_path = output_root / CANDIDATE_FOCUS_INDEX_JSON_NAME
    index_csv_path = output_root / CANDIDATE_FOCUS_INDEX_CSV_NAME
    index_geojson_path = output_root / CANDIDATE_FOCUS_INDEX_GEOJSON_NAME
    index_json_path.write_text(json.dumps(index_payload, indent=2, sort_keys=True), encoding="utf-8")
    index_fieldnames = [
        "candidate_rank", "candidate_id", "object_id", "cluster_id", "source_score", "source_review_order",
        "finding_label", "row_min", "row_max", "col_min", "col_max", "center_row", "center_col", "utm_e",
        "utm_n", "lon", "lat", "focus_radius_m", "focus_diameter_m", "mask_pixel_count", "relative_dir",
    ]
    _write_csv(index_csv_path, index_rows, fieldnames=index_fieldnames)
    index_geojson_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": index_features}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    artifacts.extend(
        [
            _artifact("candidate_focus_index_json", index_json_path, run_dir),
            _artifact("candidate_focus_index_csv", index_csv_path, run_dir),
            _artifact("candidate_focus_index_geojson", index_geojson_path, run_dir),
        ]
    )

    return StageResult(
        artifacts=artifacts,
        metadata={
            "candidate_focus_selected_count": len(index_rows),
            "candidate_focus_top_n": configured_top_n,
            "candidate_focus_geometry_contract": CANDIDATE_FOCUS_GEOMETRY_CONTRACT,
            "classifier_behavior_changed": False,
        },
    )


class CandidateFocusStage(Stage):
    name = "candidate_focus"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = (
        "Adds candidate-centered detailed Focus analysis after whole-scene classifier ranking while preserving the existing user Focus."
    )

    async def run(self, context: StageContext) -> StageResult:
        return run_candidate_focus_analysis(context=context)
