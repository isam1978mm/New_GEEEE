"""Plan, dry-run, or write private C07 hard-negative I1 rows.

Default behavior is dry-run only and writes nothing.

Write mode requires --write and a private sample manifest outside the repo.
This script does not download C07 data, assemble I2, run the readiness validator,
train, infer, call Earth Engine, or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SAMPLE_MANIFEST = Path(r"C:\Dev\New_GEE_PRIVATE\C07_RAW\c07_sample_manifest.private.jsonl")
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I1_C07")
DEFAULT_DATASET_ID = "c07_i1_private_v1"
DEFAULT_SCHEMA_VERSION = "training_example_v1"
DEFAULT_SOURCE_VERSION = "maus_mining_polygons_operator_selected_local_version"
DEFAULT_TARGET_COUNT = 217
DEFAULT_SEED = 20260616

REQUIRED_I1_FIELDS = (
    "schema_version",
    "sample_id",
    "dataset_id",
    "area_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "label_quality",
    "label_evidence_source",
    "evidence_source_type",
    "evidence_source_version",
    "evidence_review_method",
    "reviewer_or_source_reference",
    "acquisition_window",
    "sensor_sources",
    "grid_version",
    "preprocessing_commit",
    "features_ref",
    "metadata_ref",
    "redaction_class",
    "notes",
)

REQUIRED_SAMPLE_FIELDS = (
    "source_record_ref",
    "hard_negative_class",
)


class C07InputError(ValueError):
    """Raised when the private C07 sample input is missing or invalid."""


def main() -> int:
    args = _parse_args()

    sample_manifest = Path(args.sample_manifest)
    output_dir = Path(args.output_dir)

    _validate_private_path_not_inside_repo(sample_manifest, "sample manifest")
    _validate_private_path_not_inside_repo(output_dir, "output directory")

    sample_rows: list[dict[str, Any]] = []
    input_status = "sample_manifest_missing"
    input_error: str | None = None

    if sample_manifest.is_file():
        try:
            sample_rows = _read_jsonl(sample_manifest)
            _validate_sample_rows(sample_rows)
            input_status = "sample_manifest_valid"
        except C07InputError as exc:
            input_status = "sample_manifest_invalid"
            input_error = str(exc)

    eligible_rows = _eligible_rows(sample_rows)
    selected_rows = _select_deterministic_rows(
        rows=eligible_rows,
        target_count=args.target_count,
        seed=args.seed,
    )

    ready_to_write = (
        input_status == "sample_manifest_valid" and len(selected_rows) == args.target_count
    )

    summary = {
        "status": _status(write=args.write, ready_to_write=ready_to_write, input_status=input_status),
        "source_id": "C07",
        "dataset_id": args.dataset_id,
        "source_version": args.source_version,
        "sample_manifest_present": sample_manifest.is_file(),
        "sample_manifest_status": input_status,
        "sample_manifest_error": input_error,
        "requested_count": args.target_count,
        "seed": args.seed,
        "candidate_count": len(sample_rows),
        "eligible_count": len(eligible_rows),
        "selected_count": len(selected_rows),
        "held_back_count": max(0, len(sample_rows) - len(eligible_rows)),
        "planned_label_counts": {"Class_HardNegative": len(selected_rows)},
        "planned_label_quality_counts": {"reviewed_independent": len(selected_rows)},
        "planned_evidence_type_counts": {"independently_produced_reference": len(selected_rows)},
        "split_counts": {"unassigned": len(selected_rows)},
        "redaction_class_counts": {"LOCAL_SENSITIVE": len(selected_rows)},
        "real_i1_rows_created": 0,
        "i2_pack_assembled": False,
        "validator_run_on_real_data": False,
        "training_started": False,
        "inference_started": False,
        "notes": (
            "C07 is hard-negative only. This writer requires a private sample "
            "manifest before write mode can create local private rows."
        ),
    }

    if args.write:
        if not ready_to_write:
            raise SystemExit(
                "C07 write refused: provide a valid private sample manifest with at least "
                f"{args.target_count} eligible rows outside Git."
            )
        i1_rows = [
            _make_i1_row(
                sample=row,
                dataset_id=args.dataset_id,
                schema_version=args.schema_version,
                source_version=args.source_version,
                seed=args.seed,
            )
            for row in selected_rows
        ]
        summary["real_i1_rows_created"] = len(i1_rows)
        summary["status"] = "private_i1_rows_written"
        _write_private_outputs(output_dir=output_dir, rows=i1_rows, summary=summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or write private C07 hard-negative I1 rows outside Git."
    )
    parser.add_argument("--sample-manifest", default=str(DEFAULT_SAMPLE_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--schema-version", default=DEFAULT_SCHEMA_VERSION)
    parser.add_argument("--source-version", default=DEFAULT_SOURCE_VERSION)
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write private JSONL and summaries. Without this flag, dry-run only.",
    )
    return parser.parse_args()


def _status(*, write: bool, ready_to_write: bool, input_status: str) -> str:
    if write and ready_to_write:
        return "ready_to_write_private_i1_rows"
    if write:
        return "write_refused"
    if input_status == "sample_manifest_valid" and ready_to_write:
        return "dry_run_ready"
    if input_status == "sample_manifest_valid":
        return "dry_run_insufficient_eligible_samples"
    return "dry_run_sample_manifest_required"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except ValueError as exc:
                raise C07InputError(f"invalid JSON on line {line_number}") from exc
            if not isinstance(payload, dict):
                raise C07InputError(f"line {line_number} is not a JSON object")
            rows.append(payload)
    if not rows:
        raise C07InputError("sample manifest is empty")
    return rows


def _validate_sample_rows(rows: list[dict[str, Any]]) -> None:
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_SAMPLE_FIELDS if not _has_text(row.get(field))]
        if missing:
            raise C07InputError(
                f"sample row {index} missing required fields: {','.join(missing)}"
            )


def _eligible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("exclude", "")).strip().lower() in {"1", "true", "yes"}:
            continue
        if not _has_text(row.get("source_record_ref")):
            continue
        if not _has_text(row.get("hard_negative_class")):
            continue
        eligible.append(row)
    return eligible


def _select_deterministic_rows(
    *,
    rows: list[dict[str, Any]],
    target_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    if target_count < 0:
        raise ValueError("target_count must be non-negative")
    keyed = [(_sample_sort_key(row, seed), row) for row in rows]
    keyed.sort(key=lambda item: item[0])
    return [row for _, row in keyed[:target_count]]


def _sample_sort_key(row: dict[str, Any], seed: int) -> str:
    payload = {
        "seed": seed,
        "source_record_ref": str(row.get("source_record_ref", "")),
        "hard_negative_class": str(row.get("hard_negative_class", "")),
    }
    return _stable_hash(payload)


def _make_i1_row(
    *,
    sample: dict[str, Any],
    dataset_id: str,
    schema_version: str,
    source_version: str,
    seed: int,
) -> dict[str, Any]:
    fingerprint = _stable_hash(
        {
            "seed": seed,
            "source_record_ref": sample.get("source_record_ref"),
            "hard_negative_class": sample.get("hard_negative_class"),
        }
    )
    short_id = fingerprint[:16]
    private_ref = f"c07_private_ref_{short_id}"
    row = {
        "schema_version": schema_version,
        "sample_id": f"c07_sample_{short_id}",
        "dataset_id": dataset_id,
        "area_id": f"c07_area_{short_id}",
        "group_id": f"c07_group_{short_id}",
        "chip_id": f"pending_chip_{short_id}",
        "split": "unassigned",
        "label": "Class_HardNegative",
        "label_quality": "reviewed_independent",
        "label_evidence_source": private_ref,
        "evidence_source_type": "independently_produced_reference",
        "evidence_source_version": source_version,
        "evidence_review_method": "c07_private_mining_disturbance_sampling_policy_seeded",
        "reviewer_or_source_reference": private_ref,
        "acquisition_window": "pending_feature_build",
        "sensor_sources": ["pending_feature_build"],
        "grid_version": "pending_feature_build",
        "preprocessing_commit": "pending_feature_build",
        "features_ref": f"pending_features_{short_id}",
        "metadata_ref": f"pending_metadata_{short_id}",
        "redaction_class": "LOCAL_SENSITIVE",
        "notes": "C07 private mining/disturbance hard-negative row; features, split policy, and I2 readiness remain pending.",
    }
    missing = [field for field in REQUIRED_I1_FIELDS if field not in row]
    if missing:
        raise ValueError(f"internal error: generated row missing fields: {missing}")
    return row


def _write_private_outputs(
    *,
    output_dir: Path,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "training_examples.c07.private.jsonl", rows)
    _write_json(output_dir / "training_examples.c07.private.summary.json", summary)
    _write_json(
        output_dir / "source_lineage.c07.private.json",
        {
            "dataset_id": summary["dataset_id"],
            "source_id": "C07",
            "source_version": summary["source_version"],
            "lineage_mode": "private_generated_reference_only",
            "row_count": len(rows),
        },
    )
    _write_json(
        output_dir / "exclusions.c07.private.summary.json",
        {
            "dataset_id": summary["dataset_id"],
            "held_back_count": summary["held_back_count"],
            "reason": "private manifest excluded or ineligible rows",
        },
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temp_path, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
