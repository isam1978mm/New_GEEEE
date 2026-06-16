"""Create private POS-01 I1 training-example rows outside Git.

This script is local/private by design.

Default behavior is dry-run only. It prints aggregate counts and writes nothing.
Use --write to create private output files under an output directory outside the repo.

It does not assemble I2, run the readiness validator, train, infer, call Earth Engine,
or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\POS01_RAW")
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I1_POS01")
DEFAULT_DATASET_ID = "pos01_i1_private_v1"
DEFAULT_SCHEMA_VERSION = "training_example_v1"
DEFAULT_SOURCE_VERSION = "pos01_zenodo_14569340_private_review"

SOURCE_CONFIGS = (
    {
        "file_name": "unesco.csv",
        "date_field": "Date of damage (first reported)",
    },
    {
        "file_name": "science-at-risk.csv",
        "date_field": "Date of damage",
    },
)

INCLUDE_FIELD = "Include or not (Yes/No)"
TYPE_FIELD = "Type of damanged site"
LOCATION_FIELD = "Geo location"
ADDRESS_FIELD = "Address "

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


def main() -> int:
    args = _parse_args()
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)

    _validate_private_input_dir(source_dir)
    _validate_private_output_dir(output_dir)

    rows: list[dict[str, Any]] = []
    file_summaries: list[dict[str, Any]] = []
    held_back_total = 0
    accepted_total = 0

    for config in SOURCE_CONFIGS:
        result = _process_source_file(
            source_dir=source_dir,
            file_name=str(config["file_name"]),
            date_field=str(config["date_field"]),
            dataset_id=args.dataset_id,
            schema_version=args.schema_version,
            source_version=args.source_version,
        )
        rows.extend(result["rows"])
        file_summaries.append(result["summary"])
        accepted_total += int(result["summary"]["accepted_count"])
        held_back_total += int(result["summary"]["held_back_count"])

    summary = {
        "status": "ready_to_write_private_i1_rows" if args.write else "dry_run_only",
        "dataset_id": args.dataset_id,
        "source_version": args.source_version,
        "accepted_total": accepted_total,
        "i1_rows_ready_total": len(rows),
        "held_back_total": held_back_total,
        "planned_label_counts": {"Class_A": len(rows)},
        "planned_label_quality_counts": {"reviewed_independent": len(rows)},
        "planned_evidence_type_counts": {"authoritative_external_dataset": len(rows)},
        "split_counts": {"unassigned": len(rows)},
        "redaction_class_counts": {"LOCAL_SENSITIVE": len(rows)},
        "real_i1_rows_created": len(rows) if args.write else 0,
        "i2_pack_assembled": False,
        "validator_run_on_real_data": False,
        "training_started": False,
        "inference_started": False,
        "file_summaries": file_summaries,
        "notes": (
            "Rows are label/evidence placeholders for private I1 preparation. "
            "Feature references, split policy, I2 assembly, and readiness validation remain pending."
        ),
    }

    if args.write:
        _write_private_outputs(output_dir=output_dir, rows=rows, summary=summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or write private POS-01 I1 rows outside Git."
    )
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--schema-version", default=DEFAULT_SCHEMA_VERSION)
    parser.add_argument("--source-version", default=DEFAULT_SOURCE_VERSION)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write private JSONL and summaries. Without this flag, the script is dry-run only.",
    )
    return parser.parse_args()


def _process_source_file(
    *,
    source_dir: Path,
    file_name: str,
    date_field: str,
    dataset_id: str,
    schema_version: str,
    source_version: str,
) -> dict[str, Any]:
    path = source_dir / file_name
    if not path.is_file():
        raise FileNotFoundError(f"required POS-01 source file missing: {file_name}")

    records = _read_csv(path)
    required_fields = (TYPE_FIELD, LOCATION_FIELD, ADDRESS_FIELD, date_field)

    accepted_count = 0
    held_back_count = 0
    rows: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=1):
        include_value = str(record.get(INCLUDE_FIELD, "")).strip().lower()
        if include_value != "yes":
            continue

        accepted_count += 1
        missing_required = [
            field for field in required_fields if not str(record.get(field, "")).strip()
        ]
        if missing_required:
            held_back_count += 1
            continue

        rows.append(
            _make_i1_row(
                record=record,
                source_file=file_name,
                row_number=row_number,
                dataset_id=dataset_id,
                schema_version=schema_version,
                source_version=source_version,
            )
        )

    return {
        "summary": {
            "file": file_name,
            "accepted_count": accepted_count,
            "i1_candidate_count": len(rows),
            "held_back_count": held_back_count,
        },
        "rows": rows,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path.name}")
        return [dict(row) for row in reader]


def _make_i1_row(
    *,
    record: dict[str, str],
    source_file: str,
    row_number: int,
    dataset_id: str,
    schema_version: str,
    source_version: str,
) -> dict[str, Any]:
    fingerprint = _stable_private_fingerprint(
        {
            "source_file": source_file,
            "row_number": row_number,
            "record": record,
        }
    )
    short_id = fingerprint[:16]
    sample_id = f"pos01_sample_{short_id}"
    area_id = f"pos01_area_{short_id}"
    group_id = f"pos01_group_{short_id}"
    private_ref = f"pos01_private_ref_{short_id}"

    row = {
        "schema_version": schema_version,
        "sample_id": sample_id,
        "dataset_id": dataset_id,
        "area_id": area_id,
        "group_id": group_id,
        "chip_id": f"pending_chip_{short_id}",
        "split": "unassigned",
        "label": "Class_A",
        "label_quality": "reviewed_independent",
        "label_evidence_source": private_ref,
        "evidence_source_type": "authoritative_external_dataset",
        "evidence_source_version": source_version,
        "evidence_review_method": "pos01_private_include_yes_required_fields_review",
        "reviewer_or_source_reference": private_ref,
        "acquisition_window": "pending_feature_build",
        "sensor_sources": ["pending_feature_build"],
        "grid_version": "pending_feature_build",
        "preprocessing_commit": "pending_feature_build",
        "features_ref": f"pending_features_{short_id}",
        "metadata_ref": f"pending_metadata_{short_id}",
        "redaction_class": "LOCAL_SENSITIVE",
        "notes": "POS-01 private label row; features, split policy, and I2 readiness remain pending.",
    }
    missing = [field for field in REQUIRED_I1_FIELDS if field not in row]
    if missing:
        raise ValueError(f"internal error: generated row missing fields: {missing}")
    return row


def _stable_private_fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_private_outputs(
    *,
    output_dir: Path,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "training_examples.pos01.private.jsonl"
    summary_path = output_dir / "training_examples.pos01.private.summary.json"
    lineage_path = output_dir / "source_lineage.pos01.private.json"
    exclusions_path = output_dir / "exclusions.pos01.private.summary.json"

    _write_jsonl(jsonl_path, rows)
    _write_json(summary_path, summary)
    _write_json(
        lineage_path,
        {
            "dataset_id": summary["dataset_id"],
            "source_version": summary["source_version"],
            "lineage_mode": "private_generated_reference_only",
            "row_count": len(rows),
        },
    )
    _write_json(
        exclusions_path,
        {
            "dataset_id": summary["dataset_id"],
            "held_back_total": summary["held_back_total"],
            "reason": "held back by required private review field completeness gate",
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


def _validate_private_input_dir(path: Path) -> None:
    if not path.is_dir():
        raise FileNotFoundError(f"source directory does not exist: {path}")
    if _is_inside_repo(path):
        raise ValueError("source directory must be outside the repository")


def _validate_private_output_dir(path: Path) -> None:
    if _is_inside_repo(path):
        raise ValueError("output directory must be outside the repository")


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
