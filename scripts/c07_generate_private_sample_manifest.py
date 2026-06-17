"""Generate a private C07 mining/disturbance hard-negative sample manifest.

This script samples a local operator-selected Maus mining/disturbance polygon
source and creates private hard-negative candidate references for C07.

Default behavior is dry-run only. It writes nothing unless --write is provided.

It does not download source data, create I1 rows, assemble I2, run the readiness
validator, train, infer, call Earth Engine, or change app/API/frontend code.
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
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\C07_RAW")
DEFAULT_MANIFEST_NAME = "c07_sample_manifest.private.jsonl"
DEFAULT_LINEAGE_NAME = "c07_sample_lineage.private.jsonl"
DEFAULT_SUMMARY_NAME = "c07_sample_manifest.private.summary.json"
DEFAULT_TARGET_COUNT = 217
DEFAULT_SEED = 20260616
DEFAULT_DATASET_ID = "c07_private_sample_manifest_v1"
DEFAULT_SOURCE_VERSION = "maus_mining_polygons_operator_selected_local_version"
DEFAULT_ALLOWED_CLASS_VALUES = (
    "mine",
    "mining",
    "quarry",
    "disturbance",
    "disturbed",
    "extraction",
    "pit",
    "tailings",
)

GEOMETRY_FIELD_CANDIDATES = (
    "geometry",
    "wkt",
    "geom",
    "bbox",
    "polygon",
    "longitude",
    "latitude",
    "lon",
    "lat",
)

EXCLUDE_TRUE_VALUES = {"1", "true", "yes", "y", "exclude", "excluded"}


class C07SamplerError(ValueError):
    """Raised when private C07 sampling cannot proceed safely."""


def main() -> int:
    args = _parse_args()

    source_file = Path(args.source_file)
    output_dir = Path(args.output_dir)
    allowed_class_values = _parse_allowed_class_values(args.allowed_class_values)

    _validate_private_existing_file(source_file, "C07 source file")
    _validate_private_output_dir(output_dir)

    records, reader_name = _read_source_records(source_file)
    eligible_records, reject_counts, class_counts = _eligible_records(
        records=records,
        class_field=args.class_field,
        allowed_class_values=allowed_class_values,
    )
    selected_records = _select_deterministic_records(
        rows=eligible_records,
        target_count=args.target_count,
        seed=args.seed,
    )

    summary = {
        "status": "ready_to_write_private_sample_manifest" if args.write else "dry_run_only",
        "source_id": "C07",
        "source_role": "hard_negative",
        "dataset_id": args.dataset_id,
        "source_version": args.source_version,
        "source_file_name": source_file.name,
        "source_reader": reader_name,
        "requested_count": args.target_count,
        "raw_record_count": len(records),
        "eligible_count": len(eligible_records),
        "selected_count": len(selected_records),
        "held_back_count": max(0, len(records) - len(eligible_records)),
        "seed": args.seed,
        "class_field": args.class_field,
        "class_filter_applied": bool(args.class_field),
        "allowed_class_values": sorted(allowed_class_values),
        "selected_class_counts": dict(sorted(class_counts.items())),
        "reject_counts": dict(sorted(reject_counts.items())),
        "manifest_written": False,
        "i1_rows_created": 0,
        "i2_pack_assembled": False,
        "validator_run_on_real_data": False,
        "training_started": False,
        "inference_started": False,
    }

    if args.write:
        if len(selected_records) != args.target_count:
            raise SystemExit(
                f"C07 sample manifest write refused: selected {len(selected_records)} "
                f"of requested {args.target_count} samples."
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(output_dir / DEFAULT_MANIFEST_NAME, [_manifest_row(row) for row in selected_records])
        _write_jsonl(output_dir / DEFAULT_LINEAGE_NAME, [_lineage_row(row) for row in selected_records])
        summary["manifest_written"] = True
        summary["status"] = "private_sample_manifest_written"
        _write_json(output_dir / DEFAULT_SUMMARY_NAME, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a private C07 hard-negative sample manifest from a local mining/disturbance source."
    )
    parser.add_argument(
        "--source-file",
        required=True,
        help=(
            "Path to a local C07 source file outside Git. Supported: GeoJSON/JSON, "
            "JSONL, CSV, and optionally SHP/GPKG if geopandas is installed."
        ),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--source-version", default=DEFAULT_SOURCE_VERSION)
    parser.add_argument(
        "--class-field",
        default=None,
        help=(
            "Optional source property/column to filter by allowed class values. "
            "If omitted, all records with geometry are treated as operator-selected C07 candidates."
        ),
    )
    parser.add_argument(
        "--allowed-class-values",
        default=",".join(DEFAULT_ALLOWED_CLASS_VALUES),
        help="Comma-separated accepted mining/disturbance class tokens used only when --class-field is set.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write private manifest and lineage files outside Git.",
    )
    return parser.parse_args()


def _read_source_records(path: Path) -> tuple[list[dict[str, Any]], str]:
    suffix = path.suffix.lower()
    if suffix in {".geojson", ".json"}:
        return _read_geojson_or_json(path), "json_geojson"
    if suffix == ".jsonl":
        return _read_jsonl_records(path), "jsonl"
    if suffix == ".csv":
        return _read_csv_records(path), "csv"
    if suffix in {".gpkg", ".shp"}:
        return _read_with_geopandas(path), "geopandas"
    raise C07SamplerError(
        f"unsupported source file extension {suffix}; use GeoJSON/JSON, JSONL, CSV, SHP, or GPKG"
    )


def _read_geojson_or_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []

    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list):
            raise C07SamplerError("GeoJSON FeatureCollection has no features list")
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            geometry = feature.get("geometry")
            records.append(
                {
                    "private_source_index": index,
                    "properties": properties,
                    "geometry_fingerprint": _stable_hash(geometry) if geometry else "",
                    "has_geometry": bool(geometry),
                    "source_record_hint": _source_record_hint(properties, index),
                }
            )
        return records

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            if isinstance(item, dict):
                records.append(_normalize_mapping_record(item, index))
        return records

    if isinstance(payload, dict):
        return [_normalize_mapping_record(payload, 0)]

    raise C07SamplerError("JSON source must be an object, list, or GeoJSON FeatureCollection")


def _read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                records.append(_normalize_mapping_record(payload, index))
    return records


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            records.append(_normalize_mapping_record(dict(row), index))
    return records


def _read_with_geopandas(path: Path) -> list[dict[str, Any]]:
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise C07SamplerError(
            "geopandas is required to read SHP/GPKG files. Convert the source to GeoJSON/CSV or install geopandas."
        ) from exc

    dataframe = gpd.read_file(path)
    records: list[dict[str, Any]] = []
    for index, row in dataframe.iterrows():
        payload = row.drop(labels=[dataframe.geometry.name], errors="ignore").to_dict()
        geometry = row.geometry
        has_geometry = geometry is not None and not geometry.is_empty
        records.append(
            {
                "private_source_index": int(index) if isinstance(index, int) else len(records),
                "properties": {key: _json_safe(value) for key, value in payload.items()},
                "geometry_fingerprint": _stable_hash(geometry.wkb_hex if has_geometry else ""),
                "has_geometry": bool(has_geometry),
                "source_record_hint": _source_record_hint(payload, len(records)),
            }
        )
    return records


def _normalize_mapping_record(record: dict[str, Any], index: int) -> dict[str, Any]:
    has_geometry = _has_geometry_like_value(record)
    return {
        "private_source_index": index,
        "properties": {str(key): _json_safe(value) for key, value in record.items()},
        "geometry_fingerprint": _stable_hash(_geometry_like_payload(record)) if has_geometry else "",
        "has_geometry": has_geometry,
        "source_record_hint": _source_record_hint(record, index),
    }


def _eligible_records(
    *,
    records: list[dict[str, Any]],
    class_field: str | None,
    allowed_class_values: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    eligible: list[dict[str, Any]] = []
    reject_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}

    for record in records:
        properties = record.get("properties", {})
        if _is_excluded(properties):
            _increment(reject_counts, "excluded_by_source_flag")
            continue
        if not record.get("has_geometry"):
            _increment(reject_counts, "missing_geometry")
            continue

        class_value = "mining_disturbance_non_target"
        if class_field:
            raw_value = properties.get(class_field)
            if raw_value is None:
                _increment(reject_counts, "missing_class_field")
                continue
            class_value = str(raw_value).strip()
            if not _class_allowed(class_value, allowed_class_values):
                _increment(reject_counts, "disallowed_class")
                continue

        enriched = dict(record)
        enriched["hard_negative_class"] = "mining_disturbance_non_target"
        enriched["source_class_value"] = class_value or "mining_disturbance_non_target"
        eligible.append(enriched)
        _increment(class_counts, str(enriched["source_class_value"]))

    return eligible, reject_counts, class_counts


def _select_deterministic_records(
    *,
    rows: list[dict[str, Any]],
    target_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    if target_count <= 0:
        raise C07SamplerError("target_count must be positive")
    keyed = [(_sample_sort_key(row, seed), row) for row in rows]
    keyed.sort(key=lambda item: item[0])
    return [row for _, row in keyed[:target_count]]


def _sample_sort_key(row: dict[str, Any], seed: int) -> str:
    payload = {
        "seed": seed,
        "source_record_hint": row.get("source_record_hint"),
        "geometry_fingerprint": row.get("geometry_fingerprint"),
        "hard_negative_class": row.get("hard_negative_class"),
    }
    return _stable_hash(payload)


def _manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    source_record_ref = _private_source_record_ref(row)
    return {
        "source_record_ref": source_record_ref,
        "hard_negative_class": row["hard_negative_class"],
    }


def _lineage_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_record_ref": _private_source_record_ref(row),
        "source_class_value": row.get("source_class_value", "mining_disturbance_non_target"),
        "private_source_index": row.get("private_source_index"),
        "private_geometry_fingerprint": row.get("geometry_fingerprint"),
    }


def _private_source_record_ref(row: dict[str, Any]) -> str:
    fingerprint = _stable_hash(
        {
            "source": "C07",
            "source_record_hint": row.get("source_record_hint"),
            "geometry_fingerprint": row.get("geometry_fingerprint"),
        }
    )
    return f"c07_maus_ref_{fingerprint[:16]}"


def _source_record_hint(properties: dict[str, Any], index: int) -> str:
    for key in ("id", "ID", "fid", "FID", "uid", "UID", "objectid", "OBJECTID"):
        value = properties.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return f"source_index:{index}"


def _has_geometry_like_value(record: dict[str, Any]) -> bool:
    if isinstance(record.get("geometry"), (dict, str)) and record.get("geometry"):
        return True
    if isinstance(record.get("wkt"), str) and record.get("wkt", "").strip():
        return True
    if isinstance(record.get("geom"), str) and record.get("geom", "").strip():
        return True
    if isinstance(record.get("bbox"), (list, tuple, str)) and record.get("bbox"):
        return True
    has_lon_lat = any(str(key).lower() in {"lon", "longitude"} for key in record) and any(
        str(key).lower() in {"lat", "latitude"} for key in record
    )
    return bool(has_lon_lat)


def _geometry_like_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: _json_safe(value) for key, value in record.items() if str(key).lower() in GEOMETRY_FIELD_CANDIDATES}


def _is_excluded(properties: dict[str, Any]) -> bool:
    for key, value in properties.items():
        if str(key).strip().lower() in {"exclude", "excluded", "hold_back", "held_back"}:
            if str(value).strip().lower() in EXCLUDE_TRUE_VALUES:
                return True
    return False


def _class_allowed(value: str, allowed: set[str]) -> bool:
    normalized = value.strip().lower()
    return any(token in normalized for token in allowed)


def _parse_allowed_class_values(text: str) -> set[str]:
    values = {part.strip().lower() for part in text.split(",") if part.strip()}
    if not values:
        raise C07SamplerError("at least one allowed class token is required")
    return values


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


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


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _validate_private_existing_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)


def _validate_private_output_dir(path: Path) -> None:
    _validate_private_path_not_inside_repo(path, "output directory")


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
