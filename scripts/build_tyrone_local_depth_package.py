from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_NAME = "depth_method_manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
CANDIDATE_TEMPLATE_NAME = "depth_candidates.template.json"


def build_tyrone_local_depth_package(output_dir: Path, *, force: bool = False) -> dict[str, Any]:
    """Create a private provisional Tyrone local-depth package.

    The package contains measured range anchors only. It contains no coordinates,
    polygons, radar features, model weights, or private source paths.
    """

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError("output directory is not empty; use --force to replace generated files")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "local_depth_package_v1",
        "method_kind": "operator_zone_lookup_v1",
        "method_version": "tyrone-local-beta-v1",
        "calibration_dataset_version": "tyrone-3x-measured-anchors-2026-07-29",
        "site_id": "tyrone_3x",
        "validation_status": "provisional",
        "allow_run_quality_warning": False,
        "warnings": [
            "provisional_geometry",
            "requires_operator_zone_review",
            "local_calibration_only",
            "not_transferable",
            "not_global_model",
        ],
        "zones": [
            {
                "zone_id": "tyrone_tp5",
                "depth_min_m": 0.65532,
                "depth_best_m": 0.68072,
                "depth_max_m": 0.70612,
                "warnings": ["measured_anchor", "public_as_built_record"],
            },
            {
                "zone_id": "tyrone_tp6",
                "depth_min_m": 0.85090,
                "depth_best_m": 0.94996,
                "depth_max_m": 1.04902,
                "warnings": ["measured_anchor", "public_as_built_record"],
            },
        ],
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(manifest_text, encoding="utf-8")

    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (output_dir / CHECKSUMS_NAME).write_text(
        f"{digest}  {MANIFEST_NAME}\n",
        encoding="utf-8",
    )

    candidate_template = {
        "schema_version": "local_depth_candidates_v1",
        "candidates": [
            {
                "candidate_id": "replace-with-local-candidate-id-for-test-plot-5",
                "zone_id": "tyrone_tp5",
            },
            {
                "candidate_id": "replace-with-local-candidate-id-for-test-plot-6",
                "zone_id": "tyrone_tp6",
            },
        ],
    }
    (output_dir / CANDIDATE_TEMPLATE_NAME).write_text(
        json.dumps(candidate_template, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "created",
        "method_version": manifest["method_version"],
        "calibration_dataset_version": manifest["calibration_dataset_version"],
        "zone_count": len(manifest["zones"]),
        "output_dir": str(output_dir.resolve()),
        "generated_files": [MANIFEST_NAME, CHECKSUMS_NAME, CANDIDATE_TEMPLATE_NAME],
        "warnings": manifest["warnings"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a private provisional Tyrone local-depth package.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Private local directory where the package will be written.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace previously generated package files in a non-empty directory.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = build_tyrone_local_depth_package(args.output_dir, force=args.force)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

