"""Measure the real repeat-point spread of GEDI L2A observations.

This is a stricter follow-up to ``audit_gedi_point_pairs.py``. It keeps the same
quality filtering and reciprocal-nearest pairing, then reports statistics at 5,
10, 15 and 25 metre separation. It also removes the first-order slope effect
using the static TanDEM-X and SRTM elevations carried on each GEDI footprint.

The script is read-only. It does not create zones, call the depth engine, or
label an elevation difference as depth.
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
    reciprocal_nearest_pairs,
    datetime_from_delta_time,
)
from app.pipeline.elevation_change.gedi_precision import (  # noqa: E402
    GediTerrainReference,
    assess_sub_metre_readiness,
    summaries_by_distance,
)
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402

GEDI_INDEX = "LARSE/GEDI/GEDI02_A_002_INDEX"
DEFAULT_SPLIT_DATE = "2022-01-01"
CATALOG_DECLARED_END_DATE = "2024-11-29"
DEFAULT_TARGET_M = 0.7

SHOT_PROPERTIES = [
    "beam",
    "degrade_flag",
    "delta_time",
    "digital_elevation_model",
    "digital_elevation_model_srtm",
    "elev_lowestmode",
    "elevation_bias_flag",
    "orbit_number",
    "quality_flag",
    "sensitivity",
    "shot_number",
    "surface_flag",
]


class GediPrecisionAuditError(RuntimeError):
    """Raised when a precision audit cannot produce an honest result."""


def _parse_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_finite(properties: dict[str, Any], key: str) -> float | None:
    value = properties.get(key)
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _load_manifest(run_dir: Path) -> tuple[GridManifest, Any]:
    manifest_path = run_dir / "grid_manifest.json"
    if not manifest_path.is_file():
        raise GediPrecisionAuditError(f"missing grid manifest: {manifest_path}")
    manifest = GridManifest(
        **json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    return manifest, grid_spec_from_manifest(manifest)


def _intersecting_table_ids(region: Any) -> list[str]:
    values = (
        ee.FeatureCollection(GEDI_INDEX)
        .filterBounds(region)
        .aggregate_array("table_id")
        .distinct()
        .sort()
        .getInfo()
    )
    if not isinstance(values, list):
        raise GediPrecisionAuditError("Earth Engine returned no GEDI table-id list")
    return [str(value) for value in values if value]


def _quality_filtered_table(table_id: str, region: Any) -> Any:
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


def _feature_to_record(
    feature: dict[str, Any],
    *,
    table_id: str,
    transformer: Transformer,
) -> tuple[GediShot, GediTerrainReference] | None:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    properties = feature.get("properties") or {}
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None

    required = ("delta_time", "elev_lowestmode", "shot_number")
    if any(properties.get(key) is None for key in required):
        return None

    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    elevation = float(properties["elev_lowestmode"])
    delta_time = float(properties["delta_time"])
    if not all(
        math.isfinite(value)
        for value in (longitude, latitude, elevation, delta_time)
    ):
        return None

    x_m, y_m = transformer.transform(longitude, latitude)
    sensitivity = _optional_finite(properties, "sensitivity")
    shot = GediShot(
        shot_number=str(properties["shot_number"]),
        observed_at=datetime_from_delta_time(delta_time),
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
    terrain = GediTerrainReference(
        tandemx_m=_optional_finite(properties, "digital_elevation_model"),
        srtm_m=_optional_finite(properties, "digital_elevation_model_srtm"),
    )
    return shot, terrain


def load_records(
    *,
    table_ids: list[str],
    region: Any,
    epsg: int,
    max_tables: int,
    max_shots_per_table: int,
) -> tuple[list[GediShot], dict[str, GediTerrainReference], list[str]]:
    if len(table_ids) > max_tables:
        raise GediPrecisionAuditError(
            f"{len(table_ids)} tables exceed --max-tables {max_tables}"
        )

    transformer = Transformer.from_crs(
        "EPSG:4326",
        f"EPSG:{epsg}",
        always_xy=True,
    )
    shots_by_number: dict[str, GediShot] = {}
    terrain_by_shot: dict[str, GediTerrainReference] = {}
    warnings: list[str] = []
    duplicate_count = 0

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
            record = _feature_to_record(
                feature,
                table_id=table_id,
                transformer=transformer,
            )
            if record is None:
                continue
            shot, terrain = record
            if shot.shot_number in shots_by_number:
                duplicate_count += 1
            shots_by_number[shot.shot_number] = shot
            terrain_by_shot[shot.shot_number] = terrain

    if duplicate_count:
        warnings.append(f"duplicate_shot_numbers_removed:{duplicate_count}")
    shots = sorted(
        shots_by_number.values(),
        key=lambda shot: (shot.observed_at, shot.shot_number),
    )
    return shots, terrain_by_shot, warnings


def _pair_preview(
    pairs: list[GediPair],
    terrain_by_shot: dict[str, GediTerrainReference],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    summaries = []
    for pair in pairs[: max(0, int(limit))]:
        early_ref = terrain_by_shot.get(pair.early.shot_number)
        late_ref = terrain_by_shot.get(pair.late.shot_number)
        tandemx_change = None
        srtm_change = None
        if early_ref and late_ref:
            if early_ref.tandemx_m is not None and late_ref.tandemx_m is not None:
                tandemx_change = late_ref.tandemx_m - early_ref.tandemx_m
            if early_ref.srtm_m is not None and late_ref.srtm_m is not None:
                srtm_change = late_ref.srtm_m - early_ref.srtm_m
        summaries.append(
            {
                "distance_m": round(pair.distance_m, 3),
                "raw_elevation_change_m": round(pair.elevation_change_m, 4),
                "tandemx_slope_corrected_change_m": (
                    None
                    if tandemx_change is None
                    else round(pair.elevation_change_m - tandemx_change, 4)
                ),
                "srtm_slope_corrected_change_m": (
                    None
                    if srtm_change is None
                    else round(pair.elevation_change_m - srtm_change, 4)
                ),
                "early_shot": pair.early.shot_number,
                "late_shot": pair.late.shot_number,
                "early_observed_at": pair.early.observed_at.isoformat(),
                "late_observed_at": pair.late.observed_at.isoformat(),
            }
        )
    return summaries


def audit(
    *,
    run_dir: Path,
    split_date: datetime,
    max_distance_m: float,
    max_tables: int,
    max_shots_per_table: int,
    pair_preview_limit: int,
    target_m: float,
) -> dict[str, Any]:
    manifest, grid_spec = _load_manifest(run_dir)
    region = build_grid_region(grid_spec)
    table_ids = _intersecting_table_ids(region)
    shots, terrain_by_shot, warnings = load_records(
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
    summaries = summaries_by_distance(pairs, terrain_by_shot)
    readiness = assess_sub_metre_readiness(
        summaries,
        target_m=target_m,
    )

    catalog_end = _parse_date(CATALOG_DECLARED_END_DATE)
    if shots and shots[-1].observed_at > catalog_end:
        warnings.append(
            "observations_extend_beyond_catalog_declared_end_date:"
            f"{shots[-1].observed_at.date().isoformat()}"
        )

    return {
        "schema": "gedi_point_precision_audit_v1",
        "status": "repeat_points_found" if pairs else "no_colocated_repeat_points",
        "run": run_dir.name,
        "run_epsg": manifest.epsg,
        "source": "GEDI L2A vector tables",
        "source_index": GEDI_INDEX,
        "catalog_declared_end_date": CATALOG_DECLARED_END_DATE,
        "split_date": split_date.date().isoformat(),
        "intersecting_table_count": len(table_ids),
        "quality_shot_count": len(shots),
        "early_shot_count": len(early),
        "late_shot_count": len(late),
        "earliest_observation": shots[0].observed_at.isoformat() if shots else None,
        "latest_observation": shots[-1].observed_at.isoformat() if shots else None,
        "reciprocal_pair_count": len(pairs),
        "change_summary_by_distance": summaries,
        "sub_metre_readiness": readiness,
        "pair_preview": _pair_preview(
            pairs,
            terrain_by_shot,
            limit=pair_preview_limit,
        ),
        "warnings": warnings,
        "interpretation": {
            "tandemx_and_srtm_are_static_slope_references": True,
            "does_not_prove_depth": True,
            "does_not_prove_construction_event_bracketing": True,
            "does_not_interpolate_sparse_points_into_a_grid": True,
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit GEDI repeat-point noise with terrain-offset correction."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--split-date", default=DEFAULT_SPLIT_DATE)
    parser.add_argument("--max-distance-m", type=float, default=25.0)
    parser.add_argument("--max-tables", type=int, default=500)
    parser.add_argument("--max-shots-per-table", type=int, default=10000)
    parser.add_argument("--pair-preview-limit", type=int, default=20)
    parser.add_argument("--target-m", type=float, default=DEFAULT_TARGET_M)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    initialize_ee_session(Settings())
    result = audit(
        run_dir=args.run_dir,
        split_date=_parse_date(args.split_date),
        max_distance_m=args.max_distance_m,
        max_tables=args.max_tables,
        max_shots_per_table=args.max_shots_per_table,
        pair_preview_limit=args.pair_preview_limit,
        target_m=args.target_m,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
