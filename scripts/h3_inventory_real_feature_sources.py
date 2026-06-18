"""Inventory local private sources for the H3 real feature matrix path.

Default behavior is dry-run only and writes nothing.

This script checks whether required and optional private feature sources exist
outside Git. It prints aggregate-only JSON and does not expose private row
contents, private identifiers, spatial payloads, or source records.

It does not build a feature matrix, train a model, write model artifacts, run
inference, call Earth Engine, or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path(r"C:\Dev\New_GEE_PRIVATE")
DEFAULT_I2_DIR = PRIVATE_ROOT / "I2_PRIVATE"
DEFAULT_C06_DIR = PRIVATE_ROOT / "C06_RAW"
DEFAULT_C07_DIR = PRIVATE_ROOT / "C07_RAW"
DEFAULT_FEATURES_DIR = PRIVATE_ROOT / "FEATURES"
DEFAULT_OUTPUT_DIR = PRIVATE_ROOT / "H3_REAL_FEATURES"

I2_ROWS_FILE = "i2_training_examples.private.jsonl"
DYNAMIC_WORLD_FILE = "dynamic_world.tif"
C07_MINING_FILE = "maus_mining_polygons.gpkg"
EXPECTED_I2_ROWS = 868

RASTER_EXTENSIONS = {".tif", ".tiff"}
VECTOR_EXTENSIONS = {".gpkg", ".geojson", ".json", ".shp"}
TABLE_EXTENSIONS = {".csv", ".jsonl", ".parquet"}


class InventoryError(ValueError):
    """Raised when the inventory cannot safely inspect inputs."""


def main() -> int:
    args = _parse_args()
    i2_dir = Path(args.i2_dir)
    c06_dir = Path(args.c06_dir)
    c07_dir = Path(args.c07_dir)
    features_dir = Path(args.features_dir)
    output_dir = Path(args.output_dir)

    for label, path in (
        ("I2 directory", i2_dir),
        ("C06 directory", c06_dir),
        ("C07 directory", c07_dir),
        ("features directory", features_dir),
        ("output directory", output_dir),
    ):
        _validate_private_path_not_inside_repo(path, label)

    i2_path = i2_dir / I2_ROWS_FILE
    dynamic_world_path = c06_dir / DYNAMIC_WORLD_FILE
    c07_mining_path = c07_dir / C07_MINING_FILE

    input_errors: dict[str, str] = {}
    i2_row_count = 0
    i2_rows_by_split: dict[str, int] = {}
    i2_rows_by_label: dict[str, int] = {}
    i2_rows_by_source: dict[str, int] = {}

    try:
        i2_rows = _read_i2_rows(i2_path)
        i2_row_count = len(i2_rows)
        i2_rows_by_split = _count(i2_rows, "split")
        i2_rows_by_label = _count(i2_rows, "label")
        i2_rows_by_source = _count(i2_rows, "source_id")
    except Exception as exc:  # noqa: BLE001 - aggregate reporting only
        input_errors["i2_rows"] = str(exc)

    required_sources = {
        "private_i2_rows": _source_status(i2_path),
        "dynamic_world_raster": _source_status(dynamic_world_path),
        "c07_mining_polygons": _source_status(c07_mining_path),
    }
    optional_sources = {
        "features_dir_present": features_dir.is_dir(),
        "h3_real_features_output_dir_present": output_dir.is_dir(),
    }
    features_dir_inventory = _directory_inventory(features_dir)

    missing_required_sources = [name for name, status in required_sources.items() if not status["present"]]
    row_count_matches = i2_row_count == EXPECTED_I2_ROWS
    inventory_ready = not input_errors and not missing_required_sources and row_count_matches

    result: dict[str, Any] = {
        "status": "dry_run_ready" if inventory_ready else "dry_run_not_ready",
        "readiness_decision": "ready_for_real_feature_builder_design" if inventory_ready else "not_ready_missing_real_feature_sources",
        "expected_i2_rows": EXPECTED_I2_ROWS,
        "private_i2_row_count": i2_row_count,
        "private_i2_row_count_matches_expected": row_count_matches,
        "i2_rows_by_split": i2_rows_by_split,
        "i2_rows_by_label": i2_rows_by_label,
        "i2_rows_by_source": i2_rows_by_source,
        "required_sources": required_sources,
        "missing_required_sources": missing_required_sources,
        "optional_sources": optional_sources,
        "features_dir_inventory": features_dir_inventory,
        "input_errors": input_errors,
        "inventory_written": False,
        "feature_matrix_written": False,
        "training_started": False,
        "inference_started": False,
        "model_artifact_written": False,
    }

    if args.write:
        if not inventory_ready:
            raise SystemExit("H3 real feature source inventory write refused: dry-run checks did not pass.")
        output_dir.mkdir(parents=True, exist_ok=True)
        inventory_path = output_dir / "real_feature_source_inventory.private.json"
        summary_path = output_dir / "real_feature_source_inventory.private.summary.json"
        result["status"] = "real_feature_source_inventory_written"
        result["inventory_written"] = True
        _write_json(inventory_path, result)
        _write_json(
            summary_path,
            {
                "status": result["status"],
                "readiness_decision": result["readiness_decision"],
                "expected_i2_rows": EXPECTED_I2_ROWS,
                "private_i2_row_count": i2_row_count,
                "private_i2_row_count_matches_expected": row_count_matches,
                "missing_required_sources": missing_required_sources,
                "inventory_written": True,
                "feature_matrix_written": False,
                "training_started": False,
                "inference_started": False,
                "model_artifact_written": False,
            },
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if inventory_ready else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory private H3 real feature sources with aggregate-only output.")
    parser.add_argument("--i2-dir", default=str(DEFAULT_I2_DIR))
    parser.add_argument("--c06-dir", default=str(DEFAULT_C06_DIR))
    parser.add_argument("--c07-dir", default=str(DEFAULT_C07_DIR))
    parser.add_argument("--features-dir", default=str(DEFAULT_FEATURES_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true", help="Write aggregate inventory JSON outside Git. Without this flag, dry-run only.")
    return parser.parse_args()


def _read_i2_rows(path: Path) -> list[dict[str, Any]]:
    _require_file(path, "private I2 rows file")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except ValueError as exc:
                raise InventoryError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise InventoryError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise InventoryError(f"empty JSONL file: {path}")
    return rows


def _source_status(path: Path) -> dict[str, Any]:
    present = path.is_file()
    return {
        "present": present,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size if present else 0,
    }


def _directory_inventory(path: Path) -> dict[str, Any]:
    if not path.is_dir():
        return {
            "present": False,
            "file_count": 0,
            "raster_file_count": 0,
            "vector_file_count": 0,
            "table_file_count": 0,
            "extension_counts": {},
        }

    files = [child for child in path.rglob("*") if child.is_file()]
    extension_counts = Counter(child.suffix.lower() or "no_extension" for child in files)
    return {
        "present": True,
        "file_count": len(files),
        "raster_file_count": sum(1 for child in files if child.suffix.lower() in RASTER_EXTENSIONS),
        "vector_file_count": sum(1 for child in files if child.suffix.lower() in VECTOR_EXTENSIONS),
        "table_file_count": sum(1 for child in files if child.suffix.lower() in TABLE_EXTENSIONS),
        "extension_counts": dict(sorted(extension_counts.items())),
    }


def _count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "missing")) for row in rows).items()))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)
    return path


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
