from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir

RUN_QUALITY_DIR_NAME = "run_quality"
RUN_QUALITY_SUMMARY_JSON_NAME = "run_quality_summary.json"
LOW_VALID_FRACTION_WARNING = 0.05
QUALITY_STATUSES = {"PASS", "WARNING", "BLOCKED", "UNKNOWN"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "unreadable"
    if not isinstance(payload, dict):
        return None, "invalid_json_object"
    return payload, None


def _check_record(name: str, path: Path, payload: dict[str, Any] | None, issue: str | None) -> dict[str, Any]:
    return {
        "name": name,
        "path": path.as_posix(),
        "present": payload is not None,
        "input_issue": issue,
        "status": "UNKNOWN" if payload is None else "PASS",
        "details": {},
    }


def _add_valid_fraction_gate(
    *,
    check: dict[str, Any],
    label: str,
    value: Any,
    minimum: Any,
    blockers: list[str],
    warnings: list[str],
) -> None:
    fraction = _safe_float(value, default=-1.0)
    minimum_fraction = _safe_float(minimum, default=0.0)
    check["details"][label] = round(float(fraction), 6)
    check["details"][f"{label}_minimum"] = round(float(minimum_fraction), 6)
    if fraction < minimum_fraction:
        blockers.append(f"{label}_below_minimum")
        check["status"] = "BLOCKED"
    elif fraction < LOW_VALID_FRACTION_WARNING:
        warnings.append(f"{label}_low_valid_fraction")
        if check["status"] == "PASS":
            check["status"] = "WARNING"


def build_run_quality_summary(run_dir: Path) -> dict[str, Any]:
    """Build one local/private run quality gate from upstream QA artifacts.

    This gate intentionally does not infer scientific certainty. It only answers whether the
    local run outputs are internally usable enough for downstream classifier/export stages.
    """

    blockers: list[str] = []
    warnings: list[str] = []
    unknowns: list[str] = []
    checks: list[dict[str, Any]] = []

    s2_summary_path = run_dir / "QA" / "stacks" / "s2_indices_summary.json"
    s2_summary, s2_issue = _read_json(s2_summary_path)
    s2_check = _check_record("s2_indices", s2_summary_path, s2_summary, s2_issue)
    checks.append(s2_check)

    s2_mask_manifest_path = run_dir / "S2_MASKS" / "S2_DEM_MATCHED_MASKS_manifest.json"
    s2_mask_manifest, s2_mask_issue = _read_json(s2_mask_manifest_path)
    s2_mask_check = _check_record("s2_masks", s2_mask_manifest_path, s2_mask_manifest, s2_mask_issue)
    checks.append(s2_mask_check)

    zero_shift_path = run_dir / "QA" / "grid_dem" / "zero_shift_summary.json"
    zero_shift_summary, zero_shift_issue = _read_json(zero_shift_path)
    zero_shift_check = _check_record("zero_shift", zero_shift_path, zero_shift_summary, zero_shift_issue)
    checks.append(zero_shift_check)

    alignment_path = run_dir / "alignment_qa.json"
    alignment_summary, alignment_issue = _read_json(alignment_path)
    alignment_check = _check_record("alignment_qa", alignment_path, alignment_summary, alignment_issue)
    checks.append(alignment_check)

    any_inputs_found = any(check["present"] for check in checks)
    if not any_inputs_found:
        return {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "UNKNOWN",
            "is_usable": False,
            "blocking_reasons": [],
            "warnings": [],
            "unknowns": ["no_upstream_qa_summaries_found"],
            "checks": checks,
        }

    for check in checks:
        if not check["present"]:
            reason = f"missing_{check['name']}_summary"
            blockers.append(reason)
            check["status"] = "BLOCKED"
            check["details"]["reason"] = reason

    if s2_summary is not None:
        minimum = s2_summary.get("minimum_valid_fraction", 0.0)
        _add_valid_fraction_gate(
            check=s2_check,
            label="s2_source_valid_fraction",
            value=s2_summary.get("source_valid_fraction"),
            minimum=minimum,
            blockers=blockers,
            warnings=warnings,
        )
        index_summaries = s2_summary.get("index_summaries", {})
        if isinstance(index_summaries, dict):
            low_indices: list[str] = []
            blocked_indices: list[str] = []
            for index_name, index_payload in sorted(index_summaries.items()):
                if not isinstance(index_payload, dict):
                    continue
                fraction = _safe_float(index_payload.get("valid_fraction"), default=-1.0)
                if fraction < _safe_float(minimum, default=0.0):
                    blocked_indices.append(str(index_name))
                elif fraction < LOW_VALID_FRACTION_WARNING:
                    low_indices.append(str(index_name))
            if blocked_indices:
                blockers.append("s2_index_valid_fraction_below_minimum")
                s2_check["status"] = "BLOCKED"
                s2_check["details"]["blocked_indices"] = blocked_indices
            if low_indices:
                warnings.append("s2_index_low_valid_fraction")
                if s2_check["status"] == "PASS":
                    s2_check["status"] = "WARNING"
                s2_check["details"]["low_valid_fraction_indices"] = low_indices

    if s2_mask_manifest is not None:
        masks = s2_mask_manifest.get("masks", {})
        if isinstance(masks, dict):
            low_masks: list[str] = []
            for mask_name, mask_payload in sorted(masks.items()):
                if not isinstance(mask_payload, dict):
                    continue
                fraction = _safe_float(mask_payload.get("valid_fraction"), default=-1.0)
                s2_mask_check["details"][f"{mask_name}_valid_fraction"] = round(float(fraction), 6)
                if fraction < LOW_VALID_FRACTION_WARNING:
                    low_masks.append(str(mask_name))
            if low_masks:
                warnings.append("s2_mask_low_valid_fraction")
                if s2_mask_check["status"] == "PASS":
                    s2_mask_check["status"] = "WARNING"
                s2_mask_check["details"]["low_valid_fraction_masks"] = low_masks

    if zero_shift_summary is not None:
        zero_status = str(zero_shift_summary.get("status", "")).strip()
        zero_shift_check["details"]["zero_shift_status"] = zero_status
        zero_shift_check["details"]["failing_artifacts"] = list(zero_shift_summary.get("failing_artifacts", []))
        if zero_status != "grid_locked":
            blockers.append("zero_shift_not_grid_locked")
            zero_shift_check["status"] = "BLOCKED"

    if alignment_summary is not None:
        alignment_pass = bool(alignment_summary.get("pass"))
        alignment_check["details"]["pass"] = alignment_pass
        alignment_check["details"]["failing_artifacts"] = list(alignment_summary.get("failing_artifacts", []))
        alignment_check["details"]["checked_raster_count"] = int(alignment_summary.get("checked_raster_count", 0))
        if not alignment_pass:
            blockers.append("alignment_qa_failed")
            alignment_check["status"] = "BLOCKED"
        elif int(alignment_summary.get("checked_raster_count", 0)) <= 0:
            blockers.append("alignment_qa_checked_no_rasters")
            alignment_check["status"] = "BLOCKED"

    for check in checks:
        if check["status"] == "UNKNOWN":
            unknowns.append(f"{check['name']}_unknown")

    unique_blockers = sorted(set(blockers))
    unique_warnings = sorted(set(warnings))
    unique_unknowns = sorted(set(unknowns))
    if unique_blockers:
        status = "BLOCKED"
    elif unique_unknowns:
        status = "UNKNOWN"
    elif unique_warnings:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "schema": "run_quality_summary_v1",
        "stage": "run_quality",
        "status": status,
        "is_usable": status in {"PASS", "WARNING"},
        "blocking_reasons": unique_blockers,
        "warnings": unique_warnings,
        "unknowns": unique_unknowns,
        "checks": checks,
    }


def write_run_quality_summary(run_dir: Path) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir) / RUN_QUALITY_DIR_NAME
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / RUN_QUALITY_SUMMARY_JSON_NAME
    summary = build_run_quality_summary(run_dir)
    if summary["status"] not in QUALITY_STATUSES:
        raise ValueError(f"Invalid run quality status: {summary['status']}")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary_path


class RunQualityStage(Stage):
    name = "run_quality"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Adds a local run-quality gate across S2, zero-shift, and alignment QA outputs."

    async def run(self, context: StageContext) -> StageResult:
        summary_path = write_run_quality_summary(context.run_dir)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="run_quality_summary",
                    relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=summary_path.stat().st_size,
                )
            ],
            metadata=summary,
        )
