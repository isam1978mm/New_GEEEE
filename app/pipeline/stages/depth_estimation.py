from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.depth.package import LocalDepthPackage, LocalDepthPackageError, load_local_depth_package
from app.pipeline.depth.schema import (
    DEPTH_STATUS_CALIBRATED_RANGE,
    DEPTH_STATUS_INSUFFICIENT_DATA,
    DEPTH_STATUS_NOT_AVAILABLE,
    DEPTH_STATUS_VALIDATED_RANGE,
    CandidateDepthEstimate,
    CandidateDepthInput,
)

DEPTH_MODE_OFF = "off"
DEPTH_MODE_LOCAL_CALIBRATED = "local_calibrated"
DEPTH_CANDIDATES_SCHEMA = "local_depth_candidates_v1"
DEPTH_SUMMARY_SCHEMA = "depth_summary_v1"
DEPTH_DIR_NAME = "depth"
DEPTH_INPUT_RELATIVE_PATH = Path("depth_inputs") / "candidates.json"
RUN_QUALITY_RELATIVE_PATH = Path("QA") / "run_quality" / "run_quality_summary.json"

CSV_FIELDNAMES = [
    "candidate_id",
    "depth_status",
    "estimated_depth_min_m",
    "estimated_depth_best_m",
    "estimated_depth_max_m",
    "depth_quality",
    "zone_id",
    "warnings",
]


@dataclass(frozen=True, slots=True)
class DepthOutputPaths:
    estimates_csv: Path
    summary_json: Path
    method_manifest_json: Path


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_candidate_inputs(run_dir: Path) -> tuple[list[CandidateDepthInput], str | None]:
    payload = _read_json_object(run_dir / DEPTH_INPUT_RELATIVE_PATH)
    if payload is None:
        return [], "missing_or_unreadable_depth_candidate_inputs"
    if payload.get("schema_version") != DEPTH_CANDIDATES_SCHEMA:
        return [], "unsupported_depth_candidate_input_schema"
    raw_candidates = payload.get("candidates")
    if not isinstance(raw_candidates, list):
        return [], "invalid_depth_candidate_list"

    candidates: list[CandidateDepthInput] = []
    seen_ids: set[str] = set()
    try:
        for raw_candidate in raw_candidates:
            if not isinstance(raw_candidate, dict):
                return [], "invalid_depth_candidate_entry"
            candidate = CandidateDepthInput.from_mapping(raw_candidate)
            if candidate.candidate_id in seen_ids:
                return [], "duplicate_depth_candidate_id"
            seen_ids.add(candidate.candidate_id)
            candidates.append(candidate)
    except ValueError:
        return [], "invalid_depth_candidate_entry"
    return candidates, None


def _read_run_quality(run_dir: Path) -> tuple[str, bool]:
    payload = _read_json_object(run_dir / RUN_QUALITY_RELATIVE_PATH)
    if payload is None:
        return "UNKNOWN", False
    status = str(payload.get("status") or "UNKNOWN").strip().upper()
    return status, bool(payload.get("is_usable", False))


def _write_estimates_csv(path: Path, estimates: list[CandidateDepthEstimate]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for estimate in estimates:
            writer.writerow(estimate.as_csv_row())


def _summary_status(estimates: list[CandidateDepthEstimate]) -> str:
    statuses = {estimate.depth_status for estimate in estimates}
    if DEPTH_STATUS_VALIDATED_RANGE in statuses:
        return DEPTH_STATUS_VALIDATED_RANGE
    if DEPTH_STATUS_CALIBRATED_RANGE in statuses:
        return DEPTH_STATUS_CALIBRATED_RANGE
    if estimates and statuses == {DEPTH_STATUS_NOT_AVAILABLE}:
        return DEPTH_STATUS_NOT_AVAILABLE
    return DEPTH_STATUS_INSUFFICIENT_DATA


def _count_status(estimates: list[CandidateDepthEstimate], status: str) -> int:
    return sum(1 for estimate in estimates if estimate.depth_status == status)


def _recoverable_package_load(package_dir: Path | None) -> tuple[LocalDepthPackage | None, str | None]:
    if package_dir is None:
        return None, "local_depth_package_not_configured"
    try:
        return load_local_depth_package(package_dir), None
    except LocalDepthPackageError:
        return None, "local_depth_package_invalid"


def _build_estimates(
    *,
    candidates: list[CandidateDepthInput],
    package: LocalDepthPackage | None,
    package_issue: str | None,
    run_quality_status: str,
    run_quality_usable: bool,
) -> list[CandidateDepthEstimate]:
    if package is None:
        warning = package_issue or "local_depth_package_unavailable"
        return [
            CandidateDepthEstimate.unavailable(
                candidate_id=candidate.candidate_id,
                zone_id=candidate.zone_id,
                status=DEPTH_STATUS_NOT_AVAILABLE,
                warnings=[warning],
            )
            for candidate in candidates
        ]

    quality_supported = run_quality_usable and run_quality_status == "PASS"
    if run_quality_status == "WARNING" and package.allow_run_quality_warning and run_quality_usable:
        quality_supported = True
    if not quality_supported:
        return [
            CandidateDepthEstimate.unavailable(
                candidate_id=candidate.candidate_id,
                zone_id=candidate.zone_id,
                status=DEPTH_STATUS_INSUFFICIENT_DATA,
                warnings=["run_quality_not_supported"],
            )
            for candidate in candidates
        ]

    estimates: list[CandidateDepthEstimate] = []
    for candidate in candidates:
        zone = package.zone(candidate.zone_id)
        if zone is None:
            estimates.append(
                CandidateDepthEstimate.unavailable(
                    candidate_id=candidate.candidate_id,
                    zone_id=candidate.zone_id,
                    status=DEPTH_STATUS_INSUFFICIENT_DATA,
                    warnings=["candidate_outside_local_calibration_support"],
                )
            )
            continue
        warnings = [
            "local_calibration_only",
            "not_transferable",
            "not_global_model",
            *package.warnings,
            *zone.warnings,
        ]
        if run_quality_status == "WARNING":
            warnings.append("run_quality_warning_allowed_by_package")
        estimates.append(
            CandidateDepthEstimate.ranged(
                candidate_id=candidate.candidate_id,
                status=package.output_status,
                depth_range=zone.depth_range,
                depth_quality=package.depth_quality,
                zone_id=candidate.zone_id,
                warnings=warnings,
            )
        )
    return estimates


def write_depth_outputs(
    *,
    run_dir: Path,
    package_dir: Path | None,
) -> tuple[DepthOutputPaths, dict[str, Any]]:
    run_dir = Path(run_dir)
    depth_dir = run_dir / DEPTH_DIR_NAME
    depth_dir.mkdir(parents=True, exist_ok=True)

    candidates, candidate_issue = _read_candidate_inputs(run_dir)
    run_quality_status, run_quality_usable = _read_run_quality(run_dir)
    package, package_issue = _recoverable_package_load(package_dir)

    warnings: list[str] = []
    if candidate_issue:
        warnings.append(candidate_issue)
    if package_issue:
        warnings.append(package_issue)
    if run_quality_status not in {"PASS", "WARNING"} or not run_quality_usable:
        warnings.append("run_quality_not_supported")

    estimates = _build_estimates(
        candidates=candidates,
        package=package,
        package_issue=package_issue,
        run_quality_status=run_quality_status,
        run_quality_usable=run_quality_usable,
    )

    status = _summary_status(estimates)
    method_version = package.method_version if package else ""
    calibration_version = package.calibration_dataset_version if package else ""
    summary = {
        "schema_version": DEPTH_SUMMARY_SCHEMA,
        "stage": "depth_estimation",
        "mode": DEPTH_MODE_LOCAL_CALIBRATED,
        "status": status,
        "candidate_count": len(candidates),
        "estimated_count": _count_status(estimates, DEPTH_STATUS_CALIBRATED_RANGE)
        + _count_status(estimates, DEPTH_STATUS_VALIDATED_RANGE),
        "calibrated_range_count": _count_status(estimates, DEPTH_STATUS_CALIBRATED_RANGE),
        "validated_range_count": _count_status(estimates, DEPTH_STATUS_VALIDATED_RANGE),
        "insufficient_data_count": _count_status(estimates, DEPTH_STATUS_INSUFFICIENT_DATA),
        "not_available_count": _count_status(estimates, DEPTH_STATUS_NOT_AVAILABLE),
        "method_version": method_version,
        "calibration_dataset_version": calibration_version,
        "run_quality_status": run_quality_status,
        "warnings": sorted(set(warnings)),
    }

    estimates_path = depth_dir / "depth_estimates.csv"
    summary_path = depth_dir / "depth_summary.json"
    method_manifest_path = depth_dir / "depth_method_manifest.json"
    _write_estimates_csv(estimates_path, estimates)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    method_manifest = (
        package.public_manifest()
        if package is not None
        else {
            "schema_version": "local_depth_package_public_v1",
            "status": "not_available",
            "warnings": [package_issue or "local_depth_package_unavailable"],
        }
    )
    method_manifest_path.write_text(
        json.dumps(method_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return (
        DepthOutputPaths(
            estimates_csv=estimates_path,
            summary_json=summary_path,
            method_manifest_json=method_manifest_path,
        ),
        summary,
    )


class DepthEstimationStage(Stage):
    name = "depth_estimation"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = (
        "Adds a private local calibrated range stage without reusing unsupported depth-named proxies."
    )

    async def run(self, context: StageContext) -> StageResult:
        mode = str(getattr(context.settings, "local_depth_mode", DEPTH_MODE_OFF)).strip().lower()
        if mode == DEPTH_MODE_OFF:
            return StageResult(
                metadata={
                    "schema_version": DEPTH_SUMMARY_SCHEMA,
                    "stage": self.name,
                    "mode": DEPTH_MODE_OFF,
                    "status": DEPTH_STATUS_NOT_AVAILABLE,
                    "candidate_count": 0,
                    "estimated_count": 0,
                    "warnings": ["local_depth_mode_disabled"],
                }
            )
        if mode != DEPTH_MODE_LOCAL_CALIBRATED:
            return StageResult(
                metadata={
                    "schema_version": DEPTH_SUMMARY_SCHEMA,
                    "stage": self.name,
                    "mode": mode,
                    "status": DEPTH_STATUS_NOT_AVAILABLE,
                    "candidate_count": 0,
                    "estimated_count": 0,
                    "warnings": ["unsupported_local_depth_mode"],
                }
            )

        package_dir = getattr(context.settings, "local_depth_package_dir", None)
        paths, summary = write_depth_outputs(
            run_dir=context.run_dir,
            package_dir=package_dir,
        )
        artifacts = []
        for name, path in (
            ("depth_estimates", paths.estimates_csv),
            ("depth_summary", paths.summary_json),
            ("depth_method_manifest", paths.method_manifest_json),
        ):
            artifacts.append(
                build_stage_artifact(
                    name=name,
                    relative_path=path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=path.stat().st_size,
                    http_servable=False,
                )
            )
        return StageResult(artifacts=artifacts, metadata=summary)
