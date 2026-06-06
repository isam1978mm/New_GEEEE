from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

from app.pipeline.parity import ParityPathError, resolve_run_output_path


PHASE_F_PRIVATE_CLASSIFIER_SCHEMA_VERSION = "phase_f_private_cli_classifier_v1"
PHASE_F_PRIVATE_CLASSIFIER_REPORT_RELATIVE_PATH = (
    "manifests/private_neutral_classifier_report.json"
)
PHASE_F_INPUT_SCHEMA_VERSION = "phase_f_private_classifier_inputs_v1"
EXPERIMENTAL_CLASSIFIER_ENV = "ENABLE_EXPERIMENTAL_CLASSIFIER"
CLASS_IDS: tuple[str, ...] = (
    "Class_A",
    "Class_B",
    "Class_C",
    "Class_D",
    "Class_E",
    "Class_F",
    "Class_G",
    "Class_H",
    "Class_I",
    "Class_J",
    "Class_K",
    "Class_L",
    "Class_M",
    "Class_N",
)

_REPORT_METHOD = "deterministic_private_score_aggregation"
_ALLOWED_ITEM_FIELDS = {
    "class_id",
    "class_label",
    "score",
    "probability",
    "normalized_score",
    "uncertainty",
    "rank",
    "input_family",
    "method",
    "warnings",
    "runtime_output_verified",
    "notebook_value_parity_verified",
}


@dataclass(frozen=True)
class PrivateCliClassifierResult:
    report_path: Path
    status: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool


@dataclass(frozen=True)
class _InputScore:
    input_family: str
    score: float


def run_private_cli_classifier(
    *,
    run_dir: str | Path,
    input_manifest: str | Path,
    run_id: str,
    enable_experimental_classifier: bool = False,
    report_relative_path: str | Path = PHASE_F_PRIVATE_CLASSIFIER_REPORT_RELATIVE_PATH,
) -> PrivateCliClassifierResult:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    enabled = _experimental_enabled(enable_experimental_classifier)
    if not enabled:
        payload = _base_payload(
            run_id=run_id,
            status="disabled",
            enabled=False,
            items=(),
            warnings=("Private CLI classifier disabled by experimental gate.",),
            runtime_output_verified=False,
        )
        _write_report(report_path, payload)
        return PrivateCliClassifierResult(
            report_path=report_path,
            status="disabled",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
        )

    manifest_path = _resolve_private_input_path(run_dir, input_manifest)
    scores = _load_input_scores(manifest_path)
    if not scores:
        payload = _base_payload(
            run_id=run_id,
            status="no_input",
            enabled=True,
            items=(),
            warnings=("No private score rows were available for aggregation.",),
            runtime_output_verified=True,
        )
        _write_report(report_path, payload)
        return PrivateCliClassifierResult(
            report_path=report_path,
            status="no_input",
            runtime_output_verified=True,
            notebook_value_parity_verified=False,
        )

    items = _build_score_items(scores)
    payload = _base_payload(
        run_id=run_id,
        status="scored",
        enabled=True,
        items=items,
        warnings=("Private neutral score aggregation completed.",),
        runtime_output_verified=True,
    )
    _write_report(report_path, payload)
    return PrivateCliClassifierResult(
        report_path=report_path,
        status="scored",
        runtime_output_verified=True,
        notebook_value_parity_verified=False,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a private neutral classifier score report.",
    )
    parser.add_argument("--run-dir", required=True, help="Private run directory.")
    parser.add_argument(
        "--input-manifest",
        required=True,
        help="Private input manifest under the run directory.",
    )
    parser.add_argument("--run-id", required=True, help="Run identifier for the report.")
    parser.add_argument(
        "--enable-experimental-classifier",
        action="store_true",
        help="Enable the private experimental classifier report writer.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_private_cli_classifier(
        run_dir=args.run_dir,
        input_manifest=args.input_manifest,
        run_id=args.run_id,
        enable_experimental_classifier=args.enable_experimental_classifier,
    )
    return 0 if result.status in {"disabled", "no_input", "scored"} else 1


def _experimental_enabled(enable_experimental_classifier: bool) -> bool:
    return enable_experimental_classifier or os.getenv(EXPERIMENTAL_CLASSIFIER_ENV) == "1"


def _resolve_private_input_path(run_dir: str | Path, input_manifest: str | Path) -> Path:
    run_root = Path(run_dir).resolve()
    raw_path = Path(input_manifest)
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
        try:
            resolved.relative_to(run_root)
        except ValueError as exc:
            raise ParityPathError("input_manifest escapes run directory") from exc
        return resolved
    return resolve_run_output_path(run_root, raw_path)


def _load_input_scores(manifest_path: Path) -> tuple[_InputScore, ...]:
    if not manifest_path.is_file():
        raise ValueError("input_manifest does not exist")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input_manifest must be a JSON object")
    if payload.get("schema_version") != PHASE_F_INPUT_SCHEMA_VERSION:
        raise ValueError("input_manifest schema_version is unsupported")

    raw_items = payload.get("items", ())
    if not isinstance(raw_items, list):
        raise ValueError("input_manifest items must be a list")

    scores: list[_InputScore] = []
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise ValueError(f"input_manifest item {index} must be an object")
        input_family = raw_item.get("input_family")
        raw_score = raw_item.get("score")
        if not isinstance(input_family, str) or not input_family.strip():
            raise ValueError(f"input_manifest item {index} requires input_family")
        if not isinstance(raw_score, int | float):
            raise ValueError(f"input_manifest item {index} requires numeric score")
        scores.append(
            _InputScore(
                input_family=input_family,
                score=_clamp_score(float(raw_score)),
            )
        )
    return tuple(scores)


def _build_score_items(scores: Iterable[_InputScore]) -> tuple[dict[str, object], ...]:
    ordered = sorted(scores, key=lambda item: item.score, reverse=True)
    denominator = sum(item.score for item in ordered)
    if denominator <= 0.0:
        denominator = float(len(ordered))

    items: list[dict[str, object]] = []
    for rank, score in enumerate(ordered, start=1):
        class_id = CLASS_IDS[rank - 1]
        normalized_score = _clamp_score(score.score)
        probability = (
            normalized_score / denominator
            if sum(item.score for item in ordered) > 0.0
            else 1.0 / len(ordered)
        )
        item = {
            "class_id": class_id,
            "class_label": class_id,
            "score": round(normalized_score, 6),
            "probability": round(_clamp_score(probability), 6),
            "normalized_score": round(normalized_score, 6),
            "uncertainty": round(1.0 - normalized_score, 6),
            "rank": rank,
            "input_family": score.input_family,
            "method": _REPORT_METHOD,
            "warnings": (),
            "runtime_output_verified": True,
            "notebook_value_parity_verified": False,
        }
        _validate_output_item(item)
        items.append(item)
    return tuple(items)


def _base_payload(
    *,
    run_id: str,
    status: str,
    enabled: bool,
    items: Iterable[dict[str, object]],
    warnings: Iterable[str],
    runtime_output_verified: bool,
) -> dict[str, object]:
    item_list = list(items)
    return {
        "schema_version": PHASE_F_PRIVATE_CLASSIFIER_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "enabled": enabled,
        "method": _REPORT_METHOD,
        "items": item_list,
        "warnings": list(warnings),
        "redacted_summary": {
            "artifact_type": "private neutral classifier report",
            "artifact_class": "FILESYSTEM_ONLY",
            "classification": "EXPERIMENTAL_CLASSIFIER_ARTIFACT",
            "filesystem_only": True,
            "cli_only": True,
            "requires_enable_experimental": True,
            "http_servable": False,
            "frontend_visible": False,
            "downloadable_via_api": False,
            "called_by_api": False,
            "called_by_background_tasks": False,
            "called_by_core_orchestrator": False,
            "item_count": len(item_list),
            "status": status,
        },
        "runtime_output_verified": runtime_output_verified,
        "notebook_value_parity_verified": False,
        "filesystem_only": True,
        "cli_only": True,
        "requires_enable_experimental": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "called_by_api": False,
        "called_by_background_tasks": False,
        "called_by_core_orchestrator": False,
        "phase_f_runtime_changes": False,
        "public_exposure_changes": False,
    }


def _write_report(report_path: Path, payload: dict[str, object]) -> None:
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_output_item(item: dict[str, object]) -> None:
    unexpected = set(item) - _ALLOWED_ITEM_FIELDS
    if unexpected:
        raise ValueError(f"unsupported private classifier fields: {sorted(unexpected)}")
    class_id = item["class_id"]
    if not isinstance(class_id, str) or class_id not in CLASS_IDS:
        raise ValueError("private classifier output requires neutral class_id")


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


if __name__ == "__main__":
    raise SystemExit(main())
