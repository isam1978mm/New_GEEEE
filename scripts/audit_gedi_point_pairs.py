"""Audit real GEDI L2A point observations for one existing run.

This is the point-level follow-up to ``check_laser_altimetry_coverage.py``.
The earlier script uses monthly rasters and is only a coarse screening tool; it
cannot count individual shots or prove that early and late footprints are
co-located.

This script reads the official GEDI L2A table index, loads only the vector tables
whose footprints intersect the run AOI, applies conservative quality filters,
and performs unique reciprocal-nearest early/late matching in the run CRS.

It does not modify the run, write calibration zones, invoke the depth engine, or
claim that an elevation difference is depth.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee  # noqa: E402
from pyproj import Transformer  # noqa: E402

from app.config import Settings  # noqa: E402
from app.pipeline.elevation_change.gedi_points import (  # noqa: E402
    GediPair,
    GediShot,
    datetime_from_delta_time,
    elevation_change_summary,
    independent_spatial_bin_count,
    pair_threshold_counts,
    reciprocal_nearest_pairs,
)
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402

GEDI_INDEX = "LARSE/GEDI/GEDI02_A_002_INDEX"
DEFAULT_SPLIT_DATE = "2022-01-01"
DATA_END_DATE = "2024-11-29"
PAIR_THRESHOLDS_M = (5.0, 10.0, 15.0, 25.0)

SHOT_PROPERTIES = [
    "beam",
    "degrade_flag",
    "delta_time",
    "elev_lowestmode",
    "elevation_bias_flag",
    "orbit_number",
    "quality_flag",
    "sensitivity",
    "shot_number",
    "surface_flag",
]


class GediAuditError(RuntimeError):
    """Raised when the point audit cannot produce an honest result."""


def _parse_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _load_manifest(run_dir: Path) -> tuple[GridManifest, Any]:
    manifest_path = run_dir / "grid_manifest.json"
    if not manifest_path.is_file():
        raise GediAuditError(f"missing grid manifest: {manifest_path}")
    manifest = GridManifest(
        **json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    grid_spec = grid_spec_from_manifest(manifest)
    return manifest, grid_spec


def _intersecting_table_ids(region: Any) -> list[str]:
    index = ee.FeatureCollection(GEDI_INDEX).filterBounds(region)
    table_ids = index.aggregate_array("table_id").distinct().sort().getInfo()
    if not isinstance(table_ids, list):
        raise GediAuditError("Earth Engine returned no GEDI table-id list")
    return [str(value) for value in table_ids if value]


def _quality_filtered_table(table_id: str, region: Any) -> Any:
    """Load one L2A vector table and keep conservative ground shots only."""

    return (
        ee.FeatureCollection(table_id)
        .filterBounds(region)
        .filter(ee.Filter.eq("quality_flag", 1))
        .filter(ee.Filter.eq("degrade_flag", 0))
        .filter(ee.Filter.eq("elevation_bias_flag", 0))
        .filter(ee.Filter.eq("surface_flag", 1))
        .filter(ee.Filter.gte("sensitivity", 0.0))
        .filter(ee.Filter.lte("sensitivity", 1.0))
        .filter(ee.Filter.notNull(["delta_time", "elev_lowestmode", "shot_number"]))
        .select(SHOT_PROPERTIES)
    )


def _feature_to_shot(
    feature: dict[str, Any],
    *,
    table_id: str,
    transformer: Transformer,
) -> GediShot | None:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    properties = feature.get("properties") or {}
    if (
        not isinstance(coordinates, list)
        or len(coordinates) < 2
        or properties.get("delta_time") is None
        or properties.get("elev_lowestmode") is None
    ):
        return None

    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    elevation = float(properties["elev_lowestmode"])
    delta_time = float(properties["delta_time"])
    sensitivity_raw = properties.get("sensitivity")
    if not all(math.isfinite(value) for value in (longitude, latitude, elevation, delta_time)):
        return None

    x_m, y_m = transformer.transform(longitude, latitude)
    observed_at = datetime_from_delta_time(delta_time)
    sensitivity = (
        float(sensitivity_raw)
        if sensitivity_raw is not None and math.isfinite(float(sensitivity_raw))
        else None
    )
    return GediShot(
        shot_number=str(properties.get("shot_number", "")),
        observed_at=observed_at,
        longitude=longitude,
        latitude=latitude,
        x_m=float(x_m),
        y_m=float(y_m),
        elevation_m=elevation,
        beam=int(properties.get("beam", -1)),
        orbit_number=int(properties.get("orbit_number", -1)),
        table_id=table_id,
        sensitivity=sensitivity,
    )


def load_quality_shots(
    *,
    table_ids: list[str],
    region: Any,
    epsg: int,
    max_tables: int,
    max_shots_per_table: int,
) -> tuple[list[GediShot], list[str]]:
    """Fetch point features table by table and return shots plus warnings."""

    if len(table_ids) > max_tables:
        raise GediAuditError(
            f"{len(table_ids)} GEDI tables intersect this AOI, above --max-tables "
            f"{max_tables}; raise the limit explicitly after checking scope"
        )

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    shots: list[GediShot] = []
    warnings: list[str] = []

    for table_id in table_ids:
        collection = _quality_filtered_table(table_id, region)
        count = int(collection.size().getInfo())
        if count > max_shots_per_table:
            warnings.append(
                f"table_truncated:{table_id}:{count}>{max_shots_per_table}"
            )
            collection = collection.limit(max_shots_per_table)
        payload = collection.getInfo()
        features = payload.get("features", []) if isinstance(payload, dict) else []
        for feature in features:
            shot = _feature_to_shot(
                feature,
                table_id=table_id,
                transformer=transformer,
            )
            if shot is not None:
                shots.append(shot)

    deduplicated = {shot.shot_number: shot for shot in shots if shot.shot_number}
    if len(deduplicated) != len(shots):
        warnings.append(
            f"duplicate_shot_numbers_removed:{len(shots) - len(deduplicated)}"
        )
    ordered = sorted(
        deduplicated.values(),
        key=lambda shot: (shot.observed_at, shot.shot_number),
    )
    return ordered, warnings


def _pair_to_mapping(pair: GediPair) -> dict[str, Any]:
    return {
        "distance_m": round(pair.distance_m, 3),
        "elevation_change_m": round(pair.elevation_change_m, 4),
        "early": {
            "shot_number": pair.early.shot_number,
            "observed_at": pair.early.observed_at.isoformat(),
            "longitude": pair.early.longitude,
            "latitude": pair.early.latitude,
            "elevation_m": pair.early.elevation_m,
            "beam": pair.early.beam,
            "orbit_number": pair.early.orbit_number,
            "table_id": pair.early.table_id,
        },
        "late": {
            "shot_number": pair.late.shot_number,
            "observed_at": pair.late.observed_at.isoformat(),
            "longitude": pair.late.longitude,
            "latitude": pair.late.latitude,
            "elevation_m": pair.late.elevation_m,
            "beam": pair.late.beam,
            "orbit_number": pair.late.orbit_number,
            "table_id": pair.late.table_id,
        },
    }


def audit(
    *,
    run_dir: Path,
    split_date: datetime,
    max_distance_m: float,
    max_tables: int,
    max_shots_per_table: int,
    pair_preview_limit: int,
) -> dict[str, Any]:
    manifest, grid_spec = _load_manifest(run_dir)
    region = build_grid_region(grid_spec)
    table_ids = _intersecting_table_ids(region)
    shots, warnings = load_quality_shots(
        table_ids=table_ids,
        region=region,
        epsg=manifest.epsg,
        max_tables=max_tables,
        max_shots_per_table=max_shots_per_table,
    )

    early = [shot for shot in shots if shot.observed_at < split_date]
    late = [shot for shot in shots if shot.observed_at >= split_date]
    pairs = reciprocal_nearest_pairs(
        early,
        late,
        max_distance_m=max_distance_m,
    )

    pair_counts = pair_threshold_counts(
        pairs,
        thresholds_m=PAIR_THRESHOLDS_M,
    )
    within_25m = [pair for pair in pairs if pair.distance_m <= 25.0]

    observation_dates = sorted({shot.observed_at.date().isoformat() for shot in shots})
    status = "possible_point_change_test" if within_25m else "no_colocated_repeat_points"

    return {
        "schema": "gedi_point_audit_v1",
        "status": status,
        "run": run_dir.name,
        "run_epsg": manifest.epsg,
        "source": "GEDI L2A vector tables",
        "source_index": GEDI_INDEX,
        "dataset_end_date": DATA_END_DATE,
        "split_date": split_date.date().isoformat(),
        "quality_filters": {
            "quality_flag": 1,
            "degrade_flag": 0,
            "elevation_bias_flag": 0,
            "surface_flag": 1,
            "sensitivity_range": [0.0, 1.0],
        },
        "intersecting_table_count": len(table_ids),
        "quality_shot_count": len(shots),
        "early_shot_count": len(early),
        "late_shot_count": len(late),
        "earliest_observation": shots[0].observed_at.isoformat() if shots else None,
        "latest_observation": shots[-1].observed_at.isoformat() if shots else None,
        "unique_observation_date_count": len(observation_dates),
        "unique_orbit_count": len({shot.orbit_number for shot in shots}),
        "unique_beams": sorted({shot.beam for shot in shots}),
        "reciprocal_pair_count_by_distance": pair_counts,
        "independent_100m_midpoint_bins_within_25m": independent_spatial_bin_count(
            within_25m,
            bin_size_m=100.0,
        ),
        "raw_elevation_change_within_25m": elevation_change_summary(within_25m),
        "pair_preview": [
            _pair_to_mapping(pair)
            for pair in within_25m[: max(0, int(pair_preview_limit))]
        ],
        "warnings": warnings,
        "does_not_prove": [
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "sub_metre_accuracy",
            "construction_event_bracketing",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit real GEDI L2A point pairs for one run without modifying the run."
        )
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument(
        "--split-date",
        default=DEFAULT_SPLIT_DATE,
        help="Early/late boundary in YYYY-MM-DD form.",
    )
    parser.add_argument(
        "--max-distance-m",
        type=float,
        default=25.0,
        help="Maximum distance for reciprocal-nearest pairing.",
    )
    parser.add_argument("--max-tables", type=int, default=500)
    parser.add_argument("--max-shots-per-table", type=int, default=10000)
    parser.add_argument("--pair-preview-limit", type=int, default=50)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    split_date = _parse_date(args.split_date)
    result = audit(
        run_dir=args.run_dir,
        split_date=split_date,
        max_distance_m=args.max_distance_m,
        max_tables=args.max_tables,
        max_shots_per_table=args.max_shots_per_table,
        pair_preview_limit=args.pair_preview_limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
