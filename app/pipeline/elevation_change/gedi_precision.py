"""Pure helpers for precision-checking repeated GEDI point observations.

The point-pair audit proves that repeat footprints exist. These helpers answer
one stricter question: after accounting for the fact that two footprints can be
several metres apart on sloping ground, what spread remains in their elevation
differences at each pairing distance?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Sequence

import numpy as np

from app.pipeline.elevation_change.gedi_points import GediPair, nmad

CorrectionKind = Literal["raw", "tandemx", "srtm"]
DEFAULT_DISTANCE_THRESHOLDS_M = (5.0, 10.0, 15.0, 25.0)


@dataclass(frozen=True, slots=True)
class GediTerrainReference:
    """Static reference elevations sampled at one GEDI footprint."""

    tandemx_m: float | None = None
    srtm_m: float | None = None


def _finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if np.isfinite(number) else None


def corrected_pair_change(
    pair: GediPair,
    terrain_by_shot: Mapping[str, GediTerrainReference],
    *,
    correction: CorrectionKind,
) -> float | None:
    """Return late-minus-early change with optional terrain-offset correction.

    GEDI footprints are about 25 m wide and repeat shots rarely have identical
    centres. On sloping ground, part of the raw elevation difference is simply
    because the late footprint is uphill or downhill from the early footprint.
    Subtracting the change in a static reference DEM removes that first-order
    terrain term without treating the DEM itself as a temporal measurement.
    """

    raw = float(pair.elevation_change_m)
    if correction == "raw":
        return raw
    if correction not in {"tandemx", "srtm"}:
        raise ValueError(f"unsupported correction: {correction}")

    early_ref = terrain_by_shot.get(pair.early.shot_number)
    late_ref = terrain_by_shot.get(pair.late.shot_number)
    if early_ref is None or late_ref is None:
        return None

    early_value = _finite_or_none(getattr(early_ref, f"{correction}_m"))
    late_value = _finite_or_none(getattr(late_ref, f"{correction}_m"))
    if early_value is None or late_value is None:
        return None

    reference_change = late_value - early_value
    return float(raw - reference_change)


def summarize_pairs(
    pairs: Sequence[GediPair],
    terrain_by_shot: Mapping[str, GediTerrainReference],
    *,
    correction: CorrectionKind,
) -> dict[str, float | int | None]:
    """Summarize one correction method over a fixed pair set."""

    values = [
        value
        for pair in pairs
        if (value := corrected_pair_change(
            pair,
            terrain_by_shot,
            correction=correction,
        ))
        is not None
    ]
    array = np.asarray(values, dtype=np.float64)
    input_count = len(pairs)
    usable_count = int(array.size)
    missing_count = input_count - usable_count

    if usable_count == 0:
        return {
            "input_pair_count": input_count,
            "usable_pair_count": 0,
            "missing_reference_count": missing_count,
            "median_m": None,
            "nmad_m": None,
            "detection_floor_95_m": None,
            "p05_m": None,
            "p95_m": None,
            "min_m": None,
            "max_m": None,
        }

    spread = nmad(array)
    return {
        "input_pair_count": input_count,
        "usable_pair_count": usable_count,
        "missing_reference_count": missing_count,
        "median_m": float(np.median(array)),
        "nmad_m": spread,
        "detection_floor_95_m": None if spread is None else float(1.96 * spread),
        "p05_m": float(np.percentile(array, 5)),
        "p95_m": float(np.percentile(array, 95)),
        "min_m": float(np.min(array)),
        "max_m": float(np.max(array)),
    }


def summaries_by_distance(
    pairs: Sequence[GediPair],
    terrain_by_shot: Mapping[str, GediTerrainReference],
    *,
    thresholds_m: Sequence[float] = DEFAULT_DISTANCE_THRESHOLDS_M,
) -> dict[str, dict[str, dict[str, float | int | None]]]:
    """Return raw and terrain-corrected summaries at each distance threshold."""

    methods: tuple[CorrectionKind, ...] = ("raw", "tandemx", "srtm")
    result: dict[str, dict[str, dict[str, float | int | None]]] = {
        method: {} for method in methods
    }
    for threshold in thresholds_m:
        distance = float(threshold)
        if distance <= 0:
            raise ValueError("distance thresholds must be positive")
        selected = [pair for pair in pairs if pair.distance_m <= distance]
        key = f"within_{distance:g}m"
        for method in methods:
            result[method][key] = summarize_pairs(
                selected,
                terrain_by_shot,
                correction=method,
            )
    return result


def assess_sub_metre_readiness(
    summaries: Mapping[str, Mapping[str, Mapping[str, float | int | None]]],
    *,
    target_m: float = 0.7,
    minimum_pairs: int = 30,
) -> dict[str, object]:
    """Conservative gate requiring two independent terrain corrections to agree.

    A route is marked ready only when both TanDEM-X- and SRTM-corrected spreads
    support the target at the same 5 m or 10 m distance band, with enough pairs
    for a meaningful robust spread estimate. This is still an audit gate, not a
    depth claim.
    """

    target = float(target_m)
    if target <= 0:
        raise ValueError("target_m must be positive")
    if minimum_pairs < 1:
        raise ValueError("minimum_pairs must be positive")

    checked: list[dict[str, object]] = []
    for band in ("within_5m", "within_10m"):
        tandemx = summaries.get("tandemx", {}).get(band, {})
        srtm = summaries.get("srtm", {}).get(band, {})
        tandemx_count = int(tandemx.get("usable_pair_count") or 0)
        srtm_count = int(srtm.get("usable_pair_count") or 0)
        tandemx_floor = tandemx.get("detection_floor_95_m")
        srtm_floor = srtm.get("detection_floor_95_m")
        supported = (
            tandemx_count >= minimum_pairs
            and srtm_count >= minimum_pairs
            and isinstance(tandemx_floor, (int, float))
            and isinstance(srtm_floor, (int, float))
            and float(tandemx_floor) <= target
            and float(srtm_floor) <= target
        )
        checked.append(
            {
                "distance_band": band,
                "tandemx_pair_count": tandemx_count,
                "srtm_pair_count": srtm_count,
                "tandemx_detection_floor_95_m": tandemx_floor,
                "srtm_detection_floor_95_m": srtm_floor,
                "supports_target": supported,
            }
        )
        if supported:
            return {
                "target_m": target,
                "minimum_pairs": minimum_pairs,
                "ready_for_point_change_prototype": True,
                "supporting_distance_band": band,
                "checked_bands": checked,
                "note": "This supports a point-change prototype, not a depth claim.",
            }

    return {
        "target_m": target,
        "minimum_pairs": minimum_pairs,
        "ready_for_point_change_prototype": False,
        "supporting_distance_band": None,
        "checked_bands": checked,
        "note": "Repeat points exist, but the measured spread does not yet support the target.",
    }
