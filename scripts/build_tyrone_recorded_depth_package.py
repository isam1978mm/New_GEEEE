from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_NAME = "depth_method_manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
CANDIDATE_TEMPLATE_NAME = "depth_candidates.template.json"

INCH_TO_M = 0.0254


def _m(inches: float) -> float:
    return round(inches * INCH_TO_M, 8)


def build_tyrone_recorded_depth_package(
    output_dir: Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Create a reviewed Tyrone package that reports records without prediction."""

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError("output directory is not empty; use --force to replace generated files")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "recorded_depth_package_v1",
        "method_kind": "operator_recorded_zone_lookup_v1",
        "method_version": "tyrone-recorded-depth-v1",
        "record_dataset_version": "tyrone-3x-confirmation-pits-2026-07-29",
        "site_id": "tyrone_3x",
        "review_status": "reviewed",
        "warnings": [
            "recorded_measurement_only",
            "no_predictive_extrapolation",
            "reviewed_zone_only",
            "not_transferable_to_unknown_zones",
        ],
        "zones": [
            {
                "zone_id": "tyrone_tp5",
                "measurement_mean_m": _m(26.8),
                "measurement_ci95_low_m": _m(25.8),
                "measurement_ci95_high_m": _m(27.8),
                "sample_min_m": _m(26.0),
                "sample_max_m": _m(28.0),
                "sample_count": 5,
                "reported_design_depth_m": _m(24.0),
                "measurement_source": "official 2006 3X as-built report",
                "measurement_date": "",
                "measurement_method": "five confirmation pits",
                "measurement_timing": "after cover placement and before seeding",
                "warnings": [
                    "official_record",
                    "mean_and_ci95_reported",
                    "measurement_date_not_stated_in_reviewed_summary",
                ],
            },
            {
                "zone_id": "tyrone_tp6",
                "measurement_mean_m": _m(37.4),
                "measurement_ci95_low_m": _m(33.5),
                "measurement_ci95_high_m": _m(41.3),
                "sample_min_m": _m(34.0),
                "sample_max_m": _m(42.0),
                "sample_count": 5,
                "reported_design_depth_m": _m(36.0),
                "measurement_source": "official 2006 3X as-built report",
                "measurement_date": "",
                "measurement_method": "five confirmation pits",
                "measurement_timing": "after cover placement and before seeding",
                "warnings": [
                    "official_record",
                    "mean_and_ci95_reported",
                    "measurement_date_not_stated_in_reviewed_summary",
                ],
            },
        ],
    }

    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_bytes = manifest_text.encode("utf-8")
    manifest_path = output_dir / MANIFEST_NAME
    # Write the exact bytes that are hashed. Text-mode writes can translate LF to
    # CRLF on Windows and would make a freshly generated package fail checksum
    # verification immediately.
    manifest_path.write_bytes(manifest_bytes)

    digest = hashlib.sha256(manifest_bytes).hexdigest()
    (output_dir / CHECKSUMS_NAME).write_bytes(
        f"{digest}  {MANIFEST_NAME}\n".encode("utf-8")
    )

    candidate_template = {
        "schema_version": "local_depth_candidates_v1",
        "candidates": [
            {
                "candidate_id": "replace-with-reviewed-local-candidate-for-test-plot-5",
                "zone_id": "tyrone_tp5",
            },
            {
                "candidate_id": "replace-with-reviewed-local-candidate-for-test-plot-6",
                "zone_id": "tyrone_tp6",
            },
        ],
    }
    candidate_text = json.dumps(candidate_template, indent=2, sort_keys=True) + "\n"
    (output_dir / CANDIDATE_TEMPLATE_NAME).write_bytes(candidate_text.encode("utf-8"))

    return {
        "status": "created",
        "method_kind": manifest["method_kind"],
        "method_version": manifest["method_version"],
        "record_dataset_version": manifest["record_dataset_version"],
        "zone_count": len(manifest["zones"]),
        "output_dir": str(output_dir.resolve()),
        "generated_files": [MANIFEST_NAME, CHECKSUMS_NAME, CANDIDATE_TEMPLATE_NAME],
        "warnings": manifest["warnings"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a reviewed Tyrone recorded-depth lookup package.",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = build_tyrone_recorded_depth_package(args.output_dir, force=args.force)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
