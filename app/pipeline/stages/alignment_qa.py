from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio

from app.db.models.enums import ArtifactClass
from app.errors import GridDriftError, StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec, pixel_center_from_transform
from app.services.storage import read_manifest

ALIGNMENT_QA_JSON_NAME = "alignment_qa.json"
ALIGNMENT_AUDIT_CSV_NAME = "alignment_audit.csv"
ALIGNMENT_MASK_SELECTION_NAME = "alignment_mask_selection.json"
ALIGNMENT_SUMMARY_REDACTED_NAME = "alignment_summary_redacted.json"
ALIGNMENT_MAX_CENTER_OFFSET_PX = 0.25
ALIGNMENT_EXCLUDED_NAMES = {"hypercube.tif"}
ALIGNMENT_EXCLUDED_DIR_PARTS = {"PRIVATE", "experimental"}


def collect_raster_sidecars(run_dir: Path) -> list[tuple[Path, Path | None]]:
    raster_pairs: list[tuple[Path, Path | None]] = []
    for raster_path in sorted(run_dir.rglob("*.tif")):
        if _is_alignment_excluded_raster(run_dir=run_dir, raster_path=raster_path):
            continue
        sidecar_path = raster_sidecar_path(raster_path)
        raster_pairs.append((raster_path, sidecar_path if sidecar_path.is_file() else None))
    if not raster_pairs:
        raise StageError("Alignment QA requires raster outputs.")
    return raster_pairs


def _is_alignment_excluded_raster(*, run_dir: Path, raster_path: Path) -> bool:
    if raster_path.name in ALIGNMENT_EXCLUDED_NAMES:
        return True
    try:
        relative_parts = raster_path.relative_to(run_dir).parts
    except ValueError:
        return True
    return any(part in ALIGNMENT_EXCLUDED_DIR_PARTS for part in relative_parts)


def _safe_artifact_label(run_dir: Path, raster_path: Path) -> str:
    try:
        return raster_path.relative_to(run_dir).as_posix()
    except ValueError:
        return raster_path.name


def _read_alignment_raster_and_metadata(path: Path) -> tuple[np.ndarray, dict[str, object]]:
    """Read a representative 2D band and real GeoTIFF metadata for grid QA."""

    with rasterio.open(path) as dataset:
        if dataset.count < 1:
            raise StageError(f"Alignment QA raster has no bands: {path.name}")
        transform = dataset.transform
        metadata = {
            "crs": dataset.crs.to_string() if dataset.crs is not None else "",
            "dtype": str(dataset.dtypes[0]),
            "height": int(dataset.height),
            "width": int(dataset.width),
            "nodata": dataset.nodata,
            "transform": [
                float(transform.a),
                float(transform.b),
                float(transform.c),
                float(transform.d),
                float(transform.e),
                float(transform.f),
            ],
        }
        return dataset.read(1).astype(np.float32, copy=False), metadata


def _raster_nodata_matches_alignment_contract(raster_metadata: dict[str, object], grid_spec: GridSpec) -> bool:
    """Mask rasters use uint8/0 semantics; analytic rasters use the grid nodata sentinel."""
    dtype = str(raster_metadata.get("dtype", "")).casefold()
    if dtype in {"uint8", "bool", "boolean"}:
        return True
    nodata = raster_metadata.get("nodata")
    return nodata is not None and float(nodata) == float(grid_spec.nodata)


def _metadata_nodata_value(raster_metadata: dict[str, object], grid_spec: GridSpec) -> float | None:
    nodata = raster_metadata.get("nodata")
    if nodata is None:
        return 0.0 if str(raster_metadata.get("dtype", "")).casefold() in {"uint8", "bool", "boolean"} else float(grid_spec.nodata)
    return float(nodata)


def _edge_valid_fraction(array: np.ndarray, nodata: float | None) -> float:
    top = array[0, :]
    bottom = array[-1, :]
    left = array[:, 0]
    right = array[:, -1]
    edge = np.concatenate([top, bottom, left, right]).astype(np.float32)
    valid = np.isfinite(edge)
    if nodata is not None:
        valid &= edge != nodata
    return float(valid.mean()) if valid.size else 0.0


def build_alignment_reports(run_dir: Path, grid_spec: GridSpec) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    audit_rows: list[dict[str, object]] = []
    failing_files: list[str] = []
    best_anchor_name = ""
    best_anchor_score = -1.0

    expected_center = pixel_center_from_transform(grid_spec.transform, row=0, col=0)
    for raster_path, sidecar_path in collect_raster_sidecars(run_dir):
        artifact_label = _safe_artifact_label(run_dir, raster_path)
        sidecar_present = sidecar_path is not None
        if sidecar_path is not None:
            read_manifest(sidecar_path)
        try:
            array, raster_metadata = _read_alignment_raster_and_metadata(raster_path)
        except Exception as exc:
            raise StageError(f"Failed to inspect raster for alignment QA: {artifact_label}") from exc

        raster_transform = tuple(float(value) for value in raster_metadata["transform"])
        raster_center = pixel_center_from_transform(raster_transform, row=0, col=0)
        scale_x = float(grid_spec.transform[0])
        scale_y = abs(float(grid_spec.transform[4]))
        row_offset_px = abs(raster_center[1] - expected_center[1]) / max(scale_y, 1e-12)
        col_offset_px = abs(raster_center[0] - expected_center[0]) / max(abs(scale_x), 1e-12)
        center_offset_px = max(row_offset_px, col_offset_px)
        nodata_matches = _raster_nodata_matches_alignment_contract(raster_metadata, grid_spec)

        passes = (
            raster_metadata["crs"] == grid_spec.crs
            and (int(raster_metadata["height"]), int(raster_metadata["width"])) == (grid_spec.size, grid_spec.size)
            and [float(value) for value in raster_metadata["transform"]] == [float(value) for value in grid_spec.manifest.crs_transform]
            and nodata_matches
            and center_offset_px <= ALIGNMENT_MAX_CENTER_OFFSET_PX
        )
        if not passes:
            failing_files.append(artifact_label)

        nodata = _metadata_nodata_value(raster_metadata, grid_spec)
        finite = np.isfinite(array)
        valid = finite if nodata is None else finite & (array != nodata)
        valid_fraction = float(valid.mean()) if valid.size else 0.0
        edge_valid_fraction = _edge_valid_fraction(array, nodata)
        if valid_fraction > best_anchor_score:
            best_anchor_score = valid_fraction
            best_anchor_name = artifact_label

        audit_rows.append(
            {
                "artifact_name": artifact_label,
                "metadata_source": "real_geotiff",
                "sidecar_present": str(sidecar_present).lower(),
                "dtype": str(raster_metadata["dtype"]),
                "height": int(raster_metadata["height"]),
                "width": int(raster_metadata["width"]),
                "valid_fraction": round(valid_fraction, 6),
                "edge_valid_fraction": round(edge_valid_fraction, 6),
                "center_offset_px": round(center_offset_px, 6),
                "passes_alignment": str(passes).lower(),
            }
        )

    summary = {
        "pass": not failing_files,
        "checked_raster_count": len(audit_rows),
        "failing_artifacts": failing_files,
        "max_center_offset_px": max(float(row["center_offset_px"]) for row in audit_rows),
        "threshold_px": ALIGNMENT_MAX_CENTER_OFFSET_PX,
        "metadata_source": "real_geotiff",
    }
    mask_selection = {
        "anchor_artifact": best_anchor_name,
        "anchor_valid_fraction": round(best_anchor_score, 6),
        "selection_rule": "highest_valid_fraction",
    }
    return audit_rows, summary, mask_selection


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_alignment_outputs(
    run_dir: Path,
    audit_rows: list[dict[str, object]],
    summary: dict[str, object],
    mask_selection: dict[str, object],
) -> dict[str, Path]:
    audit_path = run_dir / ALIGNMENT_AUDIT_CSV_NAME
    summary_path = run_dir / ALIGNMENT_QA_JSON_NAME
    mask_selection_path = run_dir / ALIGNMENT_MASK_SELECTION_NAME
    redacted_summary_path = ensure_run_qa_dir(run_dir) / "alignment" / ALIGNMENT_SUMMARY_REDACTED_NAME
    redacted_summary_path.parent.mkdir(parents=True, exist_ok=True)

    redacted_summary = {
        "pass": bool(summary["pass"]),
        "checked_raster_count": int(summary["checked_raster_count"]),
        "failing_artifacts": list(summary["failing_artifacts"]),
        "max_center_offset_px": float(summary["max_center_offset_px"]),
        "threshold_px": float(summary["threshold_px"]),
        "metadata_source": str(summary.get("metadata_source", "")),
        "anchor_artifact": str(mask_selection["anchor_artifact"]),
        "anchor_valid_fraction": float(mask_selection["anchor_valid_fraction"]),
        "selection_rule": str(mask_selection["selection_rule"]),
    }

    _write_csv(audit_path, list(audit_rows[0].keys()), audit_rows)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    mask_selection_path.write_text(json.dumps(mask_selection, indent=2, sort_keys=True), encoding="utf-8")
    redacted_summary_path.write_text(json.dumps(redacted_summary, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "audit_csv": audit_path,
        "summary_json": summary_path,
        "mask_selection_json": mask_selection_path,
        "redacted_summary_json": redacted_summary_path,
    }


class AlignmentQaStage(Stage):
    name = "alignment_qa"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        audit_rows, summary, mask_selection = build_alignment_reports(context.run_dir, self.grid_spec)
        outputs = write_alignment_outputs(context.run_dir, audit_rows, summary, mask_selection)

        artifacts = [
            build_stage_artifact(
                name="alignment_qa",
                relative_path=outputs["summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=outputs["summary_json"].stat().st_size,
            ),
            build_stage_artifact(
                name="alignment_audit",
                relative_path=outputs["audit_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=outputs["audit_csv"].stat().st_size,
            ),
            build_stage_artifact(
                name="alignment_mask_selection",
                relative_path=outputs["mask_selection_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=outputs["mask_selection_json"].stat().st_size,
            ),
            build_stage_artifact(
                name="alignment_summary_redacted",
                relative_path=outputs["redacted_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["redacted_summary_json"].stat().st_size,
            ),
        ]
        if not bool(summary["pass"]):
            raise GridDriftError(f"Alignment QA failed for: {', '.join(summary['failing_artifacts'])}")
        return StageResult(artifacts=artifacts, metadata=summary)
