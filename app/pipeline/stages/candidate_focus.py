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
    review_order: str | int
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
        raw_review_order = str(row.get("review_order") or "99_UNSPECIFIED")
        review_order: str | int = int(raw_review_order) if raw_review_order.isdigit() else raw_review_order
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

    parsed.sort(key=lambda item: (-float(item["source_score"]), str(item["review_order"]), int(item["object_id"])))
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
                review_order=item["review_order"],
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
        raise StageError