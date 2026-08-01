from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

import ee
import numpy as np
import rasterio

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec, grid_spec_from_manifest
from app.pipeline.stages.sar_rtc import (
    S1_COLLECTION_ID,
    SarFetchDiagnostics,
    apply_local_dem_rtc,
    create_ee_radar_cube_fetcher,
    load_dem_array,
)
from app.services.grid import GridManifest

SUMMARY_FILENAME = "option5_surface_change_summary.json"
INDICATOR_FILENAME = "option5_surface_change_indicator.tif"
DELTA_FILENAME = "option5_logratio_delta_db.tif"
PAIR_DIAGNOSTICS_RELATIVE_PATH = Path("QA") / "sar" / "sar_pair_diagnostics.json"
MIN_WINDOW_DAYS = 28
MIN_VALID_PIXELS = 1_000
MAX_INCIDENCE_DELTA_DEGREES = 1.5
MIN_REVIEW_THRESHOLD_DB = 1.0
ROBUST_SIGMA_MULTIPLIER = 3.0

BeforeCubeFetcher = Callable[..., np.ndarray]


def compute_surface_change_review(
    *,
    before_logratio_db: np.ndarray,
    after_logratio_db: np.ndarray,
    before_incidence: np.ndarray,
    after_incidence: np.ndarray,
    nodata: float,
    min_valid_pixels: int = MIN_VALID_PIXELS,
    max_incidence_delta_degrees: float = MAX_INCIDENCE_DELTA_DEGREES,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    shape = before_logratio_db.shape
    arrays = (after_logratio_db, before_incidence, after_incidence)
    if any(array.shape != shape for array in arrays):
        raise ValueError("Surface-change inputs must share one grid shape.")

    valid = np.ones(shape, dtype=bool)
    for array in (before_logratio_db, after_logratio_db, before_incidence, after_incidence):
        valid &= np.isfinite(array)
        valid &= array != nodata

    incidence_delta = np.abs(after_incidence - before_incidence)
    valid &= incidence_delta <= float(max_incidence_delta_degrees)
    valid_count = int(valid.sum())
    total_count = int(valid.size)

    indicator = np.full(shape, np.float32(nodata), dtype=np.float32)
    delta_output = np.full(shape, np.float32(nodata), dtype=np.float32)
    if valid_count < int(min_valid_pixels):
        return (
            {
                "status": "not_available",
                "reason": "insufficient_compatible_pixels",
                "valid_pixel_count": valid_count,
                "valid_pixel_fraction": valid_count / total_count if total_count else 0.0,
                "minimum_valid_pixels": int(min_valid_pixels),
                "maximum_incidence_delta_degrees": float(max_incidence_delta_degrees),
            },
            indicator,
            delta_output,
        )

    delta = after_logratio_db[valid].astype(np.float64) - before_logratio_db[valid].astype(np.float64)
    median_delta = float(np.median(delta))
    centered = delta - median_delta
    absolute_centered = np.abs(centered)
    mad = float(np.median(absolute_centered))
    robust_scale = max(1.4826 * mad, 0.25)
    review_threshold = max(MIN_REVIEW_THRESHOLD_DB, ROBUST_SIGMA_MULTIPLIER * robust_scale)
    flagged = absolute_centered >= review_threshold

    delta_output[valid] = delta.astype(np.float32)
    indicator_values = absolute_centered / review_threshold
    indicator[valid] = indicator_values.astype(np.float32)

    return (
        {
            "status": "available",
            "method": "dual_window_logratio_robust_review_v1",
            "valid_pixel_count": valid_count,
            "valid_pixel_fraction": valid_count / total_count if total_count else 0.0,
            "change_review_pixel_count": int(flagged.sum()),
            "change_review_pixel_fraction": float(flagged.mean()),
            "median_logratio_delta_db": median_delta,
            "p95_absolute_centered_delta_db": float(np.percentile(absolute_centered, 95)),
            "robust_scale_db": robust_scale,
            "review_threshold_db": review_threshold,
            "maximum_incidence_delta_degrees": float(max_incidence_delta_degrees),
        },
        indicator,
        delta_output,
    )


def _read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as dataset:
        return dataset.read(1).astype(np.float32)


def _load_grid_spec(run_dir: Path) -> GridSpec:
    payload = json.loads((run_dir / "grid_manifest.json").read_text(encoding="utf-8"))
    return grid_spec_from_manifest(GridManifest.model_validate(payload))


def _load_after_diagnostics(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / PAIR_DIAGNOSTICS_RELATIVE_PATH).read_text(encoding="utf-8"))


def _derive_before_window(after_start: str, after_end: str) -> tuple[str, str, int]:
    start = date.fromisoformat(after_start)
    end = date.fromisoformat(after_end)
    duration = end - start
    if duration.days < MIN_WINDOW_DAYS:
        raise ValueError("configured_after_window_too_short")
    before_end = start
    before_start = before_end - duration
    return before_start.isoformat(), before_end.isoformat(), duration.days


def _pair_records_from_diagnostics(diagnostics: SarFetchDiagnostics | None) -> list[dict[str, str]]:
    if diagnostics is None:
        return []
    return [
        {"asc_id": pair.asc_id, "desc_id": pair.desc_id}
        for pair in diagnostics.pairs
    ]


def _orbit_signature(pair_records: list[dict[str, Any]]) -> dict[str, list[int]]:
    signature: dict[str, set[int]] = {"ascending": set(), "descending": set()}
    for record in pair_records:
        for key, direction in (("asc_id", "ascending"), ("desc_id", "descending")):
            image_id = str(record.get(key, "")).strip()
            if not image_id:
                raise ValueError("missing_pair_image_id")
            image = ee.Image(f"{S1_COLLECTION_ID}/{image_id}")
            track = int(image.get("relativeOrbitNumber_start").getInfo())
            pass_direction = str(image.get("orbitProperties_pass").getInfo()).casefold()
            if pass_direction != direction:
                raise ValueError("pair_pass_direction_mismatch")
            signature[direction].add(track)
    return {key: sorted(values) for key, values in signature.items()}


def _write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _unavailable_payload(*, reason: str, after_start: str | None = None, after_end: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "option5_surface_change_summary_v1",
        "status": "not_available",
        "reason": reason,
        "warnings": [
            "not_depth",
            "not_settlement",
            "not_displacement",
            "not_physical_confirmation",
        ],
    }
    if after_start and after_end:
        payload["after_window"] = {"start": after_start, "end": after_end}
    return payload


class SurfaceChangeStage(Stage):
    name = "surface_change"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "New Option 5 product outside notebook parity; uses guarded dual-window radar comparison."

    def __init__(self, *, before_cube_fetcher: BeforeCubeFetcher | None = None) -> None:
        self.before_cube_fetcher = before_cube_fetcher

    async def run(self, context: StageContext) -> StageResult:
        summary_path = context.run_dir / SUMMARY_FILENAME
        indicator_path = context.run_dir / INDICATOR_FILENAME
        delta_path = context.run_dir / DELTA_FILENAME
        summary: dict[str, Any]
        indicator_written = False
        delta_written = False

        after_start: str | None = None
        after_end: str | None = None
        try:
            grid_spec = _load_grid_spec(context.run_dir)
            after_diagnostics = _load_after_diagnostics(context.run_dir)
            after_start = str(after_diagnostics["start_date"])
            after_end = str(after_diagnostics["end_date"])
            before_start, before_end, window_days = _derive_before_window(after_start, after_end)

            after_pairs = list(after_diagnostics.get("pairs") or [])
            if len(after_pairs) < 2:
                raise ValueError("insufficient_after_pairs")

            dem = load_dem_array(context.run_dir)
            fetcher = self.before_cube_fetcher or create_ee_radar_cube_fetcher(
                context.settings,
                grid_spec,
                start_date=before_start,
                end_date=before_end,
            )
            before_cube = fetcher(grid_spec=grid_spec)
            before_fetch_diagnostics = getattr(fetcher, "diagnostics", None)
            before_pairs = _pair_records_from_diagnostics(before_fetch_diagnostics)
            if self.before_cube_fetcher is None and len(before_pairs) < 2:
                raise ValueError("insufficient_before_pairs")

            if self.before_cube_fetcher is None:
                before_signature = _orbit_signature(before_pairs)
                after_signature = _orbit_signature(after_pairs)
                if before_signature != after_signature:
                    raise ValueError("orbit_signature_mismatch")
            else:
                before_signature = {"ascending": [], "descending": []}
                after_signature = {"ascending": [], "descending": []}

            before_outputs = apply_local_dem_rtc(
                before_cube,
                dem,
                nodata=grid_spec.nodata,
                scale_m=float(grid_spec.manifest.scale_m),
            )
            after_logratio = _read_raster(context.run_dir / "logRatio_dB.tif")
            after_incidence = _read_raster(context.run_dir / "incidence.tif")

            metrics, indicator, delta_output = compute_surface_change_review(
                before_logratio_db=before_outputs["logRatio_dB"],
                after_logratio_db=after_logratio,
                before_incidence=before_outputs["incidence"],
                after_incidence=after_incidence,
                nodata=grid_spec.nodata,
            )

            summary = {
                "schema": "option5_surface_change_summary_v1",
                **metrics,
                "before_window": {"start": before_start, "end": before_end},
                "after_window": {"start": after_start, "end": after_end},
                "window_days": window_days,
                "before_pair_count": len(before_pairs) if self.before_cube_fetcher is None else None,
                "after_pair_count": len(after_pairs),
                "orbit_signature": after_signature,
                "indicator_interpretation": "Values at or above 1 meet the within-run robust radar-change review threshold.",
                "warnings": [
                    "radar_backscatter_change_only",
                    "moisture_vegetation_and_surface_roughness_may_contribute",
                    "not_depth",
                    "not_settlement",
                    "not_displacement",
                    "not_physical_confirmation",
                ],
            }

            if metrics.get("status") == "available":
                write_georeferenced_raster(indicator_path, indicator, grid_spec)
                write_raster_sidecar(
                    indicator_path,
                    grid_manifest=grid_spec.manifest,
                    nodata=grid_spec.nodata,
                    dtype="float32",
                    shape=indicator.shape,
                )
                write_georeferenced_raster(delta_path, delta_output, grid_spec)
                write_raster_sidecar(
                    delta_path,
                    grid_manifest=grid_spec.manifest,
                    nodata=grid_spec.nodata,
                    dtype="float32",
                    shape=delta_output.shape,
                )
                indicator_written = True
                delta_written = True
        except (FileNotFoundError, KeyError, TypeError, ValueError, RuntimeError) as exc:
            reason = str(exc) if str(exc) and " " not in str(exc) else "surface_change_prerequisite_failed"
            summary = _unavailable_payload(reason=reason, after_start=after_start, after_end=after_end)
        except Exception:
            summary = _unavailable_payload(
                reason="surface_change_processing_unavailable",
                after_start=after_start,
                after_end=after_end,
            )

        _write_summary(summary_path, summary)
        artifacts = [
            build_stage_artifact(
                name="option5_surface_change_summary",
                relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=summary_path.stat().st_size,
            )
        ]
        if indicator_written:
            artifacts.append(
                build_stage_artifact(
                    name="option5_surface_change_indicator",
                    relative_path=indicator_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=indicator_path.stat().st_size,
                    http_servable=False,
                )
            )
        if delta_written:
            artifacts.append(
                build_stage_artifact(
                    name="option5_logratio_delta_db",
                    relative_path=delta_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=delta_path.stat().st_size,
                    http_servable=False,
                )
            )

        qa_dir = ensure_run_qa_dir(context.run_dir) / "surface_change"
        qa_dir.mkdir(parents=True, exist_ok=True)
        qa_summary_path = qa_dir / SUMMARY_FILENAME
        _write_summary(qa_summary_path, summary)
        artifacts.append(
            build_stage_artifact(
                name="option5_surface_change_qa_summary",
                relative_path=qa_summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=qa_summary_path.stat().st_size,
                http_servable=False,
            )
        )

        return StageResult(
            artifacts=artifacts,
            metadata={
                "status": summary.get("status", "not_available"),
                "method": summary.get("method"),
                "summary_artifact": "option5_surface_change_summary",
                "indicator_written": indicator_written,
                "delta_written": delta_written,
            },
        )
