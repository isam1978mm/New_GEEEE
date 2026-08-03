"""Read-only ICESat-2 ATL08 repeat-point precision audit for one run.

Requires the optional SlideRule Python client:
    python -m pip install "sliderule>=5.4.3"

This audit queries official ATL08 100 m terrain segments through SlideRule's
``atl08x`` endpoint.  It measures repeat-point precision before applying any
optional per-segment uncertainty ceiling.  Reported ATL08 uncertainty is kept as
a diagnostic instead of silently eliminating every observation.

The script never writes to the run, creates zones, invokes the depth engine, or
modifies the frontend.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from pyproj import Transformer

from app.pipeline.elevation_change.icesat2_repeat import (
    Icesat2Pair,
    Icesat2Segment,
    independent_midpoint_bins,
    pair_count_by_distance,
    readiness,
    reciprocal_repeat_pairs,
    summary_by_distance,
)
from app.services.grid import GridManifest

DEFAULT_START = "2018-10-13T00:00:00Z"
DEFAULT_END = "2026-08-03T00:00:00Z"
DEFAULT_SPLIT = "2022-01-01T00:00:00Z"
DISTANCE_THRESHOLDS_M = (5.0, 10.0, 15.0)
UNCERTAINTY_THRESHOLDS_M = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0)
MAX_PLAUSIBLE_UNCERTAINTY_M = 100.0
MAX_PLAUSIBLE_ABS_HEIGHT_M = 100_000.0


class Icesat2AuditError(RuntimeError):
    """Raised when the live ATL08 audit cannot produce a defensible result."""


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _load_manifest(run_dir: Path) -> GridManifest:
    path = run_dir / "grid_manifest.json"
    if not path.is_file():
        raise Icesat2AuditError(f"missing grid manifest: {path}")
    return GridManifest(**json.loads(path.read_text(encoding="utf-8")))


def _wgs84_polygon(manifest: GridManifest) -> list[dict[str, float]]:
    bounds = manifest.bounds_m
    required = ("xmin", "ymin", "xmax", "ymax")
    if not all(name in bounds for name in required):
        raise Icesat2AuditError("grid manifest has incomplete bounds_m")

    transformer = Transformer.from_crs(
        f"EPSG:{manifest.epsg}", "EPSG:4326", always_xy=True
    )
    corners_xy = [
        (bounds["xmin"], bounds["ymin"]),
        (bounds["xmax"], bounds["ymin"]),
        (bounds["xmax"], bounds["ymax"]),
        (bounds["xmin"], bounds["ymax"]),
        (bounds["xmin"], bounds["ymin"]),
    ]
    return [
        {
            "lon": float(transformer.transform(x_m, y_m)[0]),
            "lat": float(transformer.transform(x_m, y_m)[1]),
        }
        for x_m, y_m in corners_xy
    ]


def _query_atl08(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
):
    try:
        from sliderule import icesat2, sliderule
    except ImportError as exc:
        raise Icesat2AuditError(
            'missing optional dependency "sliderule"; install it with: '
            'python -m pip install "sliderule>=5.4.3"'
        ) from exc

    try:
        # The mission-specific initializer is the supported way to verify that
        # the ICESat-2 plugin is available. Passing plugins=["icesat2"] to the
        # base initializer produced a misleading KeyError in client v5.5.0.
        icesat2.init(url="slideruleearth.io", rethrow=True)
        frame = sliderule.run(
            "atl08x",
            {
                "poly": polygon,
                "t0": start,
                "t1": end,
            },
        )
    except Exception as exc:  # noqa: BLE001 - convert remote errors to audit status
        raise Icesat2AuditError(f"SlideRule ATL08 query failed: {exc}") from exc

    if frame is None:
        raise Icesat2AuditError("SlideRule returned no ATL08 result")
    if not hasattr(frame, "iterrows"):
        raise Icesat2AuditError(
            f"SlideRule returned unexpected result type: {type(frame).__name__}"
        )
    return frame


def _datetime_for_row(index_value: Any, row: Any) -> datetime | None:
    candidates = [index_value]
    for name in ("time_ns", "time", "datetime"):
        if name in row:
            candidates.append(row[name])

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, datetime):
            value = candidate
        elif hasattr(candidate, "to_pydatetime"):
            value = candidate.to_pydatetime()
        elif isinstance(candidate, (int, float)) and math.isfinite(float(candidate)):
            numeric = float(candidate)
            seconds = numeric / 1_000_000_000.0 if abs(numeric) > 1e12 else numeric
            value = datetime.fromtimestamp(seconds, tz=UTC)
        else:
            try:
                value = datetime.fromisoformat(str(candidate).replace("Z", "+00:00"))
            except ValueError:
                continue
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return None


def _coordinates_for_row(row: Any) -> tuple[float, float] | None:
    geometry = row.get("geometry") if hasattr(row, "get") else None
    if geometry is not None and hasattr(geometry, "x") and hasattr(geometry, "y"):
        return float(geometry.x), float(geometry.y)
    for lon_name, lat_name in (("longitude", "latitude"), ("lon", "lat")):
        if lon_name in row and lat_name in row:
            try:
                longitude = float(row[lon_name])
                latitude = float(row[lat_name])
            except (TypeError, ValueError):
                return None
            if math.isfinite(longitude) and math.isfinite(latitude):
                return longitude, latitude
    return None


def _finite_float(row: Any, name: str) -> float | None:
    if name not in row or row[name] is None:
        return None
    try:
        value = float(row[name])
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _finite_int(row: Any, name: str) -> int | None:
    value = _finite_float(row, name)
    return None if value is None else int(value)


def _distribution(values: Iterable[float]) -> dict[str, object]:
    array = np.asarray(list(values), dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return {
            "count": 0,
            "min_m": None,
            "p05_m": None,
            "p25_m": None,
            "median_m": None,
            "p75_m": None,
            "p95_m": None,
            "max_m": None,
            "count_at_or_below_m": {
                f"{threshold:g}": 0 for threshold in UNCERTAINTY_THRESHOLDS_M
            },
        }
    return {
        "count": int(array.size),
        "min_m": float(np.min(array)),
        "p05_m": float(np.percentile(array, 5)),
        "p25_m": float(np.percentile(array, 25)),
        "median_m": float(np.median(array)),
        "p75_m": float(np.percentile(array, 75)),
        "p95_m": float(np.percentile(array, 95)),
        "max_m": float(np.max(array)),
        "count_at_or_below_m": {
            f"{threshold:g}": int(np.sum(array <= threshold))
            for threshold in UNCERTAINTY_THRESHOLDS_M
        },
    }


def _segments_from_frame(
    frame: Any,
    *,
    epsg: int,
    maximum_uncertainty_m: float | None,
    minimum_ground_photons: int,
) -> tuple[list[Icesat2Segment], dict[str, int], dict[str, object]]:
    transformer = Transformer.from_crs(
        "EPSG:4326", f"EPSG:{epsg}", always_xy=True
    )
    segments: list[Icesat2Segment] = []
    all_uncertainties: list[float] = []
    all_ground_photons: list[float] = []
    rejected = {
        "missing_or_invalid": 0,
        "snow_or_ice": 0,
        "too_few_ground_photons": 0,
        "implausible_uncertainty_fill": 0,
        "uncertainty_above_optional_ceiling": 0,
    }

    for index_value, row in frame.iterrows():
        observed_at = _datetime_for_row(index_value, row)
        coordinates = _coordinates_for_row(row)
        height = _finite_float(row, "h_te_median")
        rgt = _finite_int(row, "rgt")
        cycle = _finite_int(row, "cycle")
        spot = _finite_int(row, "spot")
        if (
            observed_at is None
            or coordinates is None
            or height is None
            or abs(height) > MAX_PLAUSIBLE_ABS_HEIGHT_M
            or rgt is None
            or cycle is None
            or spot is None
        ):
            rejected["missing_or_invalid"] += 1
            continue

        snowcover = _finite_int(row, "segment_snowcover")
        if snowcover is not None and snowcover != 1:
            rejected["snow_or_ice"] += 1
            continue

        ground_photons = _finite_int(row, "n_te_photons")
        if ground_photons is not None:
            all_ground_photons.append(float(ground_photons))
        if ground_photons is not None and ground_photons < minimum_ground_photons:
            rejected["too_few_ground_photons"] += 1
            continue

        uncertainty = _finite_float(row, "h_te_uncertainty")
        if uncertainty is not None:
            if uncertainty < 0.0 or uncertainty > MAX_PLAUSIBLE_UNCERTAINTY_M:
                rejected["implausible_uncertainty_fill"] += 1
                continue
            all_uncertainties.append(uncertainty)
        if (
            maximum_uncertainty_m is not None
            and uncertainty is not None
            and uncertainty > maximum_uncertainty_m
        ):
            rejected["uncertainty_above_optional_ceiling"] += 1
            continue

        longitude, latitude = coordinates
        x_m, y_m = transformer.transform(longitude, latitude)
        segment_id = str(
            row.get("segment_id_beg", f"{rgt}:{cycle}:{spot}:{index_value}")
        )
        segments.append(
            Icesat2Segment(
                segment_id=segment_id,
                observed_at=observed_at,
                longitude=longitude,
                latitude=latitude,
                x_m=float(x_m),
                y_m=float(y_m),
                height_m=height,
                height_uncertainty_m=uncertainty,
                terrain_slope=_finite_float(row, "terrain_slope"),
                ground_photon_count=ground_photons,
                rgt=rgt,
                cycle=cycle,
                spot=spot,
                gt=str(row.get("gt", "")),
            )
        )

    deduplicated = {
        (
            segment.rgt,
            segment.cycle,
            segment.spot,
            segment.segment_id,
            segment.observed_at,
        ): segment
        for segment in segments
    }
    ordered = sorted(
        deduplicated.values(),
        key=lambda segment: (
            segment.observed_at,
            segment.rgt,
            segment.spot,
            segment.segment_id,
        ),
    )
    rejected["duplicates_removed"] = len(segments) - len(ordered)
    diagnostics = {
        "returned_row_count": int(len(frame)),
        "h_te_uncertainty_m": _distribution(all_uncertainties),
        "n_te_photons": _distribution(all_ground_photons),
        "note": (
            "Reported ATL08 uncertainty is diagnostic by default. "
            "Use --maximum-uncertainty-m to apply an explicit ceiling."
        ),
    }
    return ordered, rejected, diagnostics


def _pair_preview(pair: Icesat2Pair) -> dict[str, object]:
    return {
        "distance_m": round(pair.distance_m, 3),
        "elevation_change_m": round(pair.elevation_change_m, 4),
        "rgt": pair.early.rgt,
        "spot": pair.early.spot,
        "early": {
            "segment_id": pair.early.segment_id,
            "cycle": pair.early.cycle,
            "observed_at": pair.early.observed_at.isoformat(),
            "longitude": pair.early.longitude,
            "latitude": pair.early.latitude,
            "height_m": pair.early.height_m,
            "height_uncertainty_m": pair.early.height_uncertainty_m,
            "ground_photon_count": pair.early.ground_photon_count,
        },
        "late": {
            "segment_id": pair.late.segment_id,
            "cycle": pair.late.cycle,
            "observed_at": pair.late.observed_at.isoformat(),
            "longitude": pair.late.longitude,
            "latitude": pair.late.latitude,
            "height_m": pair.late.height_m,
            "height_uncertainty_m": pair.late.height_uncertainty_m,
            "ground_photon_count": pair.late.ground_photon_count,
        },
    }


def _reported_pair_uncertainty_by_distance(
    pairs: list[Icesat2Pair],
) -> dict[str, dict[str, float | int | None]]:
    output: dict[str, dict[str, float | int | None]] = {}
    for threshold in DISTANCE_THRESHOLDS_M:
        values: list[float] = []
        for pair in pairs:
            if pair.distance_m > threshold:
                continue
            early_u = pair.early.height_uncertainty_m
            late_u = pair.late.height_uncertainty_m
            if early_u is None or late_u is None:
                continue
            values.append(math.sqrt(early_u * early_u + late_u * late_u))
        if not values:
            output[f"within_{threshold:g}m"] = {
                "count": 0,
                "median_combined_1sigma_m": None,
                "p95_combined_1sigma_m": None,
            }
        else:
            array = np.asarray(values, dtype=np.float64)
            output[f"within_{threshold:g}m"] = {
                "count": int(array.size),
                "median_combined_1sigma_m": float(np.median(array)),
                "p95_combined_1sigma_m": float(np.percentile(array, 95)),
            }
    return output


def audit(
    *,
    run_dir: Path,
    start: str,
    end: str,
    split_time: datetime,
    target_m: float,
    maximum_uncertainty_m: float | None,
    minimum_ground_photons: int,
    minimum_pairs: int,
    preview_limit: int,
) -> dict[str, object]:
    manifest = _load_manifest(run_dir)
    frame = _query_atl08(
        polygon=_wgs84_polygon(manifest),
        start=start,
        end=end,
    )
    segments, rejected, diagnostics = _segments_from_frame(
        frame,
        epsg=manifest.epsg,
        maximum_uncertainty_m=maximum_uncertainty_m,
        minimum_ground_photons=minimum_ground_photons,
    )
    early = [segment for segment in segments if segment.observed_at < split_time]
    late = [segment for segment in segments if segment.observed_at >= split_time]
    pairs = reciprocal_repeat_pairs(early, late, max_distance_m=15.0)
    summaries = summary_by_distance(pairs, thresholds_m=DISTANCE_THRESHOLDS_M)
    decision = readiness(
        summaries,
        target_m=target_m,
        minimum_pairs=minimum_pairs,
    )
    within_15m = [pair for pair in pairs if pair.distance_m <= 15.0]
    dates = sorted({segment.observed_at.date().isoformat() for segment in segments})

    if not segments:
        status = "no_quality_atl08_segments"
    elif not pairs:
        status = "no_colocated_repeat_segments"
    elif decision["ready_for_point_change_prototype"]:
        status = "target_precision_supported"
    else:
        status = "repeat_segments_found_but_target_not_supported"

    return {
        "schema": "icesat2_atl08_repeat_audit_v2",
        "status": status,
        "run": run_dir.name,
        "run_epsg": manifest.epsg,
        "source": "ICESat-2 ATL08 via SlideRule atl08x",
        "query_start": start,
        "query_end": end,
        "split_time": split_time.isoformat(),
        "filters": {
            "snow_free_land_only_when_flag_present": True,
            "maximum_h_te_uncertainty_m": maximum_uncertainty_m,
            "minimum_n_te_photons": minimum_ground_photons,
            "same_rgt_and_same_spot_only": True,
            "different_cycles_only": True,
        },
        "quality_segment_count": len(segments),
        "early_segment_count": len(early),
        "late_segment_count": len(late),
        "earliest_observation": (
            segments[0].observed_at.isoformat() if segments else None
        ),
        "latest_observation": (
            segments[-1].observed_at.isoformat() if segments else None
        ),
        "unique_observation_date_count": len(dates),
        "unique_rgt_count": len({segment.rgt for segment in segments}),
        "unique_cycle_count": len({segment.cycle for segment in segments}),
        "input_diagnostics": diagnostics,
        "rejected": rejected,
        "reciprocal_pair_count_by_distance": pair_count_by_distance(
            pairs, thresholds_m=DISTANCE_THRESHOLDS_M
        ),
        "independent_100m_midpoint_bins_within_15m": independent_midpoint_bins(
            within_15m, bin_size_m=100.0
        ),
        "change_summary_by_distance": summaries,
        "reported_pair_uncertainty_by_distance": (
            _reported_pair_uncertainty_by_distance(pairs)
        ),
        "sub_metre_readiness": decision,
        "pair_preview": [
            _pair_preview(pair)
            for pair in within_15m[: max(0, int(preview_limit))]
        ],
        "does_not_prove": [
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "construction_event_bracketing",
            "radar_depth_prediction",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit ICESat-2 ATL08 repeat-point precision for one run."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--split-date", default=DEFAULT_SPLIT)
    parser.add_argument("--target-m", type=float, default=0.7)
    parser.add_argument(
        "--maximum-uncertainty-m",
        type=float,
        default=None,
        help=(
            "Optional ATL08 h_te_uncertainty ceiling. By default no ceiling is "
            "applied; the distribution is reported and repeat precision decides."
        ),
    )
    parser.add_argument("--minimum-ground-photons", type=int, default=3)
    parser.add_argument("--minimum-pairs", type=int, default=30)
    parser.add_argument("--pair-preview-limit", type=int, default=30)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = audit(
            run_dir=args.run_dir,
            start=args.start,
            end=args.end,
            split_time=_parse_time(args.split_date),
            target_m=args.target_m,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            minimum_ground_photons=args.minimum_ground_photons,
            minimum_pairs=args.minimum_pairs,
            preview_limit=args.pair_preview_limit,
        )
    except Icesat2AuditError as exc:
        print(
            json.dumps(
                {"status": "audit_unavailable", "error": str(exc)},
                indent=2,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
