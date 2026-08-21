from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_NAME = "depth_method_manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
CANDIDATE_TEMPLATE_NAME = "depth_candidates.template.json"

# Route A is deliberately local and provisional. TP5/TP6 retain the confidence
# intervals already frozen in the July 29 operator-zone beta. The later six-plot
# canonical reference supplies direct measured sample envelopes for TP1/2/3/7;
# those four are labelled explicitly rather than being promoted to an invented CI.
TYRONE_REVIEWED_ZONES: tuple[dict[str, Any], ...] = (
    {
        "zone_id": "tyrone_tp1",
        "depth_min_m": 0.66040,
        "depth_best_m": 0.70612,
        "depth_max_m": 0.81280,
        "warnings": [
            "measured_anchor",
            "official_record",
            "measured_sample_envelope",
            "derived_geometry",
        ],
    },
    {
        "zone_id": "tyrone_tp2",
        "depth_min_m": 0.86360,
        "depth_best_m": 0.94996,
        "depth_max_m": 1.06680,
        "warnings": [
            "measured_anchor",
            "official_record",
            "measured_sample_envelope",
            "derived_geometry",
        ],
    },
    {
        "zone_id": "tyrone_tp3",
        "depth_min_m": 1.19380,
        "depth_best_m": 1.28016,
        "depth_max_m": 1.37160,
        "warnings": [
            "measured_anchor",
            "official_record",
            "measured_sample_envelope",
            "derived_geometry",
        ],
    },
    {
        "zone_id": "tyrone_tp5",
        "depth_min_m": 0.65532,
        "depth_best_m": 0.68072,
        "depth_max_m": 0.70612,
        "warnings": [
            "measured_anchor",
            "official_record",
            "official_95pct_confidence_interval",
            "derived_geometry",
        ],
    },
    {
        "zone_id": "tyrone_tp6",
        "depth_min_m": 0.85090,
        "depth_best_m": 0.94996,
        "depth_max_m": 1.04902,
        "warnings": [
            "measured_anchor",
            "official_record",
            "official_95pct_confidence_interval",
            "derived_geometry",
        ],
    },
    {
        "zone_id": "tyrone_tp7",
        "depth_min_m": 1.27000,
        "depth_best_m": 1.30556,
        "depth_max_m": 1.37160,
        "warnings": [
            "measured_anchor",
            "official_record",
            "measured_sample_envelope",
            "derived_geometry",
        ],
    },
)


def _write_utf8_bytes(path: Path, text: str) -> bytes:
    payload = text.encode("utf-8")
    path.write_bytes(payload)
    return payload


def build_tyrone_local_depth_package(
    output_dir: Path,
    *,
    force: bool = False,
    allow_run_quality_warning: bool = False,
) -> dict[str, Any]:
    """Create the private provisional six-zone Tyrone Route A package.

    The package stores source-reviewed metre ranges only. Geometry stays in the
    separate source-controlled WGS84 reference and is used only to determine
    which reviewed Tyrone zones are fully contained by the selected run footprint.
    No classifier or NB output is used to create candidates or metre values.

    ``allow_run_quality_warning`` is deliberately opt-in. The operator service
    enables it only after proving the run's sole warning is the irrelevant
    ``classifier_no_objects_classified`` condition.
    """

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError("output directory is not empty; use --force to replace generated files")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "local_depth_package_v1",
        "method_kind": "operator_zone_lookup_v1",
        "method_version": "tyrone-local-six-zone-v1",
        "calibration_dataset_version": "tyrone-3x-six-plot-reference-2026-08-18",
        "site_id": "tyrone_3x",
        "validation_status": "provisional",
        "allow_run_quality_warning": bool(allow_run_quality_warning),
        "warnings": [
            "local_only",
            "provisional_calibration",
            "derived_geometry",
            "requires_reviewed_zone_containment",
            "not_transferable",
            "not_global_model",
            "not_physical_confirmation",
        ],
        "zones": [dict(zone) for zone in TYRONE_REVIEWED_ZONES],
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path = output_dir / MANIFEST_NAME
    manifest_bytes = _write_utf8_bytes(manifest_path, manifest_text)

    digest = hashlib.sha256(manifest_bytes).hexdigest()
    _write_utf8_bytes(
        output_dir / CHECKSUMS_NAME,
        f"{digest}  {MANIFEST_NAME}\n",
    )

    candidate_template = {
        "schema_version": "local_depth_candidates_v1",
        "candidates": [
            {
                "candidate_id": f"replace-with-reviewed-candidate-for-{zone['zone_id']}",
                "zone_id": zone["zone_id"],
            }
            for zone in TYRONE_REVIEWED_ZONES
        ],
    }
    _write_utf8_bytes(
        output_dir / CANDIDATE_TEMPLATE_NAME,
        json.dumps(candidate_template, indent=2, sort_keys=True) + "\n",
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
        description="Build the private provisional six-zone Tyrone Route A package.",
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
