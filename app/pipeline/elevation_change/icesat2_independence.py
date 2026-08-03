"""Independent-cycle diagnostics for ICESat-2 repeat observations.

A long run of adjacent ATL08 segments from one pair of satellite passes is not
hundreds of independent validations.  This module groups repeat pairs by their
actual early/late cycle combination and requires precision to recur across
independent early and late cycles before the laser route is considered
repeatable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.pipeline.elevation_change.icesat2_repeat import (
    Icesat2Pair,
    Icesat2Segment,
    reciprocal_repeat_pairs,
    summary_by_distance,
)


@dataclass(frozen=True, slots=True)
class CyclePairCohort:
    rgt: int
    spot: int
    early_cycle: int
    late_cycle: int
    early_time: datetime
    late_time: datetime
    pairs: tuple[Icesat2Pair, ...]


def build_cycle_pair_cohorts(
    segments: Sequence[Icesat2Segment],
    *,
    split_time: datetime,
    max_distance_m: float = 15.0,
) -> list[CyclePairCohort]:
    """Build one reciprocal-pair cohort per RGT/spot/early-cycle/late-cycle."""

    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")

    groups: dict[tuple[int, int, int], list[Icesat2Segment]] = {}
    for segment in segments:
        groups.setdefault((segment.rgt, segment.spot, segment.cycle), []).append(
            segment
        )

    early_keys = [
        key
        for key, values in groups.items()
        if values and min(item.observed_at for item in values) < split_time
    ]
    late_keys = [
        key
        for key, values in groups.items()
        if values and max(item.observed_at for item in values) >= split_time
    ]

    cohorts: list[CyclePairCohort] = []
    for early_key in sorted(early_keys):
        early_rgt, early_spot, early_cycle = early_key
        early_values = [
            item for item in groups[early_key] if item.observed_at < split_time
        ]
        if not early_values:
            continue
        for late_key in sorted(late_keys):
            late_rgt, late_spot, late_cycle = late_key
            if (early_rgt, early_spot) != (late_rgt, late_spot):
                continue
            if early_cycle == late_cycle:
                continue
            late_values = [
                item for item in groups[late_key] if item.observed_at >= split_time
            ]
            if not late_values:
                continue
            pairs = reciprocal_repeat_pairs(
                early_values,
                late_values,
                max_distance_m=max_distance_m,
            )
            if not pairs:
                continue
            cohorts.append(
                CyclePairCohort(
                    rgt=early_rgt,
                    spot=early_spot,
                    early_cycle=early_cycle,
                    late_cycle=late_cycle,
                    early_time=min(item.observed_at for item in early_values),
                    late_time=min(item.observed_at for item in late_values),
                    pairs=tuple(pairs),
                )
            )

    cohorts.sort(
        key=lambda cohort: (
            cohort.early_time,
            cohort.late_time,
            cohort.rgt,
            cohort.spot,
        )
    )
    return cohorts


def summarize_cohort(
    cohort: CyclePairCohort,
    *,
    target_m: float,
    minimum_pairs: int = 30,
) -> dict[str, object]:
    summaries = summary_by_distance(cohort.pairs, thresholds_m=(5.0, 10.0, 15.0))
    supporting_band: str | None = None
    for band in ("within_5m", "within_10m"):
        summary = summaries[band]
        count = int(summary.get("count") or 0)
        floor_value = summary.get("detection_floor_95_m")
        floor = (
            float(floor_value)
            if isinstance(floor_value, (int, float))
            else None
        )
        if count >= minimum_pairs and floor is not None and floor <= target_m:
            supporting_band = band
            break
    return {
        "rgt": cohort.rgt,
        "spot": cohort.spot,
        "early_cycle": cohort.early_cycle,
        "late_cycle": cohort.late_cycle,
        "early_observation": cohort.early_time.isoformat(),
        "late_observation": cohort.late_time.isoformat(),
        "pair_count_within_15m": len(cohort.pairs),
        "summary_by_distance": summaries,
        "supports_target": supporting_band is not None,
        "supporting_distance_band": supporting_band,
    }


def independence_decision(
    cohort_summaries: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Require passing precision across at least two early and two late cycles."""

    passing = [item for item in cohort_summaries if item.get("supports_target")]
    early_cycles = sorted({int(item["early_cycle"]) for item in passing})
    late_cycles = sorted({int(item["late_cycle"]) for item in passing})
    passing_tracks = sorted(
        {(int(item["rgt"]), int(item["spot"])) for item in passing}
    )
    return {
        "passing_cycle_pair_count": len(passing),
        "distinct_passing_early_cycles": early_cycles,
        "distinct_passing_late_cycles": late_cycles,
        "distinct_passing_rgt_spot_tracks": [
            {"rgt": rgt, "spot": spot} for rgt, spot in passing_tracks
        ],
        "single_cycle_pair_precision_supported": bool(passing),
        "multi_epoch_repeatability_supported": (
            len(early_cycles) >= 2 and len(late_cycles) >= 2
        ),
        "note": (
            "Multi-epoch support requires passing precision in at least two "
            "independent early cycles and two independent late cycles. It still "
            "does not prove that any laser segment intersects the target or "
            "brackets a construction event."
        ),
    }
