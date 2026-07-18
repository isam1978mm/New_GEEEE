"""Calculate aggregate counts and hashes for a private depth-calibration pack.

The command writes only the private calibration manifest, and only with --write.
It never prints private rows, identifiers, coordinates, depth values, or paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_depth_calibration_pack as validator

DEFAULT_DATASET_DIR = validator.DEFAULT_DATASET_DIR


class ManifestFinalizeError(ValueError):
    """Raised when a private manifest cannot be finalized safely."""


def finalize_manifest(
    dataset_dir: Path,
    *,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    validator._require_outside_repo(dataset_dir, "dataset directory")
    paths = {name: dataset_dir / name for name in validator.REQUIRED_FILES}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ManifestFinalizeError(f"required private pack files are missing: {', '.join(missing)}")

    issues: Counter[str] = Counter()
    rows = validator._read_csv(paths["calibration_records.csv"], validator.REQUIRED_COLUMNS, issues, "records")
    sources = validator._read_csv(paths["source_index.csv"], validator.SOURCE_COLUMNS, issues, "source_index")
    exclusions = validator._read_csv(paths["exclusions.csv"], validator.EXCLUSION_COLUMNS, issues, "exclusions")
    manifest = validator._read_json(paths["calibration_manifest.json"])
    feature_manifest = validator._read_json(paths["feature_manifest.json"])

    validator._validate_rows(rows, sources, exclusions, issues)
    validator._validate_feature_manifest(feature_manifest, rows, issues)
    if not rows:
        issues["no_records"] += 1
    if issues:
        raise ManifestFinalizeError(f"private pack has contract issues: {json.dumps(dict(sorted(issues.items())), sort_keys=True)}")

    resolved_dataset_id = (dataset_id or manifest.get("dataset_id") or "").strip()
    resolved_dataset_version = (dataset_version or manifest.get("dataset_version") or "").strip()
    if not resolved_dataset_id or not resolved_dataset_version:
        raise ManifestFinalizeError("dataset_id and dataset_version are required")

    counts = validator._aggregate_counts(rows)
    if counts["positive_count"] <= 0 or counts["negative_count"] <= 0:
        raise ManifestFinalizeError("positive and confirmed negative records are both required")
    if any(counts["split_counts"].get(split, 0) <= 0 for split in ("train", "validation", "holdout")):
        raise ManifestFinalizeError("train, validation, and holdout records are required")

    now = datetime.now(timezone.utc).isoformat()
    records_hash = validator._sha256(paths["calibration_records.csv"])
    source_hash = validator._sha256(paths["source_index.csv"])
    exclusions_hash = validator._sha256(paths["exclusions.csv"])
    positive_depths = [float(row["known_depth_top_m"]) for row in rows if row["reference_status"] == "known_depth_positive"]
    uncertainties = [
        float(row["depth_reference_uncertainty_m"])
        for row in rows
        if row["reference_status"] == "known_depth_positive" and row["depth_reference_uncertainty_m"]
    ]

    updated = dict(manifest)
    updated.update(
        {
            "schema_version": "depth_calibration_manifest_v1",
            "status": "populated_private_dataset",
            "dataset_id": resolved_dataset_id,
            "dataset_version": resolved_dataset_version,
            "created_at": manifest.get("created_at") or now,
            "updated_at": now,
            "build_commit": manifest.get("build_commit") or _single_value(rows, "pipeline_commit"),
            "build_procedure": manifest.get("build_procedure") or "scripts/finalize_depth_calibration_manifest.py",
            "record_count": len(rows),
            "positive_count": counts["positive_count"],
            "negative_count": counts["negative_count"],
            "excluded_count": counts["excluded_or_uncertain_count"],
            "included_relative_count": counts["included_relative_count"],
            "included_numerical_count": counts["included_numerical_count"],
            "label_quality_counts": _count(rows, "label_quality"),
            "evidence_source_counts": _count(rows, "evidence_source_type"),
            "finding_family_counts": _count(rows, "finding_family"),
            "soil_surface_counts": _count(rows, "soil_or_surface_type"),
            "season_moisture_counts": _count(rows, "moisture_or_season"),
            "terrain_counts": _count(rows, "terrain_class"),
            "depth_min_m": min(positive_depths),
            "depth_max_m": max(positive_depths),
            "depth_uncertainty_summary": _numeric_summary(uncertainties),
            "split_policy_version": _single_value(rows, "split_policy_version"),
            "split_counts": counts["split_counts"],
            "site_counts_by_split": _site_counts(rows),
            "feature_manifest_version": feature_manifest.get("feature_manifest_version"),
            "data_source_list": sorted({row["source_type"] for row in sources if row.get("source_type")}),
            "records_sha256": records_hash,
            "source_index_sha256": source_hash,
            "exclusions_sha256": exclusions_hash,
            "content_hash": validator._combined_hash((records_hash, source_hash, exclusions_hash)),
            "storage_location_reference": manifest.get("storage_location_reference") or "owner_private_depth_dataset_root",
            "artifact_class": "FILESYSTEM_ONLY",
            "filesystem_only": True,
            "http_servable": False,
            "frontend_visible": False,
            "downloadable_via_api": False,
        }
    )
    updated["manifest_hash"] = None
    updated["manifest_hash"] = _manifest_hash(updated)

    if write:
        paths["calibration_manifest.json"].write_text(
            json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    return {
        "status": "manifest_written" if write else "manifest_dry_run_ready",
        "record_count": len(rows),
        "positive_count": counts["positive_count"],
        "negative_count": counts["negative_count"],
        "included_relative_count": counts["included_relative_count"],
        "included_numerical_count": counts["included_numerical_count"],
        "split_counts": counts["split_counts"],
        "manifest_hash": updated["manifest_hash"],
        "content_hash": updated["content_hash"],
        "private_rows_printed": False,
        "manifest_written": write,
        "scientific_validation_run": False,
        "training_started": False,
    }


def _count(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    values = Counter(row.get(field, "").strip() or "unknown" for row in rows)
    return dict(sorted(values.items()))


def _numeric_summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return {
        "minimum_m": ordered[0],
        "maximum_m": ordered[-1],
        "mean_m": sum(ordered) / len(ordered),
    }


def _single_value(rows: list[dict[str, str]], field: str) -> str | None:
    values = sorted({row.get(field, "").strip() for row in rows if row.get(field, "").strip()})
    return values[0] if len(values) == 1 else None


def _site_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    sites: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        split = row.get("split", "").strip()
        site_id = row.get("site_id", "").strip()
        if split and site_id:
            sites[split].add(site_id)
    return {split: len(site_ids) for split, site_ids in sorted(sites.items())}


def _manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate private depth-calibration manifest counts and hashes.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--dataset-id")
    parser.add_argument("--dataset-version")
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = finalize_manifest(
            Path(args.dataset_dir),
            dataset_id=args.dataset_id,
            dataset_version=args.dataset_version,
            write=args.write,
        )
    except (OSError, ManifestFinalizeError, validator.PackValidationError) as exc:
        print(json.dumps({"status": "manifest_finalize_failed", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
