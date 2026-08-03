"""Run the focused regional ICESat-2 near-miss audit with safe defaults."""

from __future__ import annotations

import json

from audit_icesat2_regional_near_misses import (
    DEFAULT_OUTPUT_DIRNAME,
    DEFAULT_REGIONAL_SUMMARY_FILENAME,
    DEFAULT_SUMMARY_FILENAME,
    _build_parser,
    audit_near_misses,
)

REGIONAL_EXPANSION_DIRNAME = "icesat2_regional_expansion"


def main() -> int:
    args = _build_parser().parse_args()
    regional_summary = args.regional_summary or (
        args.runs_dir
        / REGIONAL_EXPANSION_DIRNAME
        / DEFAULT_REGIONAL_SUMMARY_FILENAME
    )
    output_dir = args.output_dir or (
        args.runs_dir / DEFAULT_OUTPUT_DIRNAME
    )
    summary_path = args.summary_json or (
        output_dir / DEFAULT_SUMMARY_FILENAME
    )
    diagnostic_radii = args.diagnostic_radius_m or [500.0, 1000.0]
    try:
        result = audit_near_misses(
            runs_dir=args.runs_dir,
            regional_summary_path=regional_summary,
            output_dir=output_dir,
            summary_path=summary_path,
            start=args.start,
            end=args.end,
            buffer_m=float(args.buffer_km) * 1000.0,
            tile_size_m=float(args.tile_km) * 1000.0,
            strict_radius_m=args.strict_radius_m,
            diagnostic_radii_m=diagnostic_radii,
            minimum_segments=args.minimum_segments,
            maximum_step_nmad_m=args.maximum_step_nmad_m,
            cross_spot_distance_m=args.cross_spot_distance_m,
            minimum_ground_photons=args.minimum_ground_photons,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            minimum_epochs=args.minimum_epochs,
            minimum_side_epochs=args.minimum_side_epochs,
            minimum_step_m=args.minimum_step_m,
            maximum_plateau_nmad_m=args.maximum_plateau_nmad_m,
            minimum_step_dominance=args.minimum_step_dominance,
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "near_miss_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed_geography_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
