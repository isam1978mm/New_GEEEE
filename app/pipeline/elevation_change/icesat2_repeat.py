"""Pure helpers for auditing repeated ICESat-2 ATL08 terrain segments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

import numpy as np

DEFAULT_DISTANCE_THRESHOLDS_M = (5.0, 10.0, 15.0)


@dataclass(frozen=True, slots=True)
class Icesat2Segment:
    segment_id: str
    observed_at: datetime
    longitude: float
    latitude: float
    x_m: float
    y_m: float
    height_m: float
    height_uncertainty_m: float | None
    terrain_slope: float | None
    ground_photon_count: int | None
    rgt: int
    cycle: int
    spot: int
    gt: str


@dataclass(frozen=True, slots=True)
class Icesat2Pair:
    early: Icesat2Segment
    late: Icesat2Segment
    distance_m: float

    @property
    def elevation_change_m(self) -> float:
        return float(self.late.height_m - self.early.height_m)

    @property
    def midpoint_x_m(self) -> float:
        return float((self.early.x_m + self.late.x_m) / 2.0)

    @property
    def midpoint_y_m(self) -> float:
        return float((self.early.y_m + self.late.y_m) / 2.0)


def nmad(values: Sequence[float] | np.ndarray) -> float | None:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return None
    median = float(np.median(array))
    return float(1.4826 * np.median(np.abs(array - median)))


def _nearest_indices(
    query: Sequence[Icesat2Segment],
    candidates: Sequence[Icesat2Segment],
    *,
    max_distance_m: float,
) -> list[tuple[int | None, float]]:
    limit = float(max_distance_m)
    if limit <= 0:
        raise ValueError("max_distance_m must be positive")
    buckets: dict[tuple[int, int], list[int]] = {}
    for index, segment in enumerate(candidates):
        key = (
            int(np.floor(segment.x_m / limit)),
            int(np.floor(segment.y_m / limit)),
        )
        buckets.setdefault(key, []).append(index)

    result: list[tuple[int | None, float]] = []
    limit_sq = limit * limit
    for segment in query:
        cell_x = int(np.floor(segment.x_m / limit))
        cell_y = int(np.floor(segment.y_m / limit))
        best_index: int | None = None
        best_sq = float("inf")
        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                for candidate_index in buckets.get(
                    (cell_x + offset_x, cell_y + offset_y), ()
                ):
                    candidate = candidates[candidate_index]
                    dx = candidate.x_m - segment.x_m
                    dy = candidate.y_m - segment.y_m
                    distance_sq = dx * dx + dy * dy
                    if distance_sq > limit_sq:
                        continue
                    if (
                        distance_sq < best_sq
                        or (
                            distance_sq == best_sq
                            and best_index is not None
                            and candidate.segment_id
                            < candidates[best_index].segment_id
                        )
                    ):
                        best_sq = distance_sq
                        best_index = candidate_index
        result.append(
            (best_index, float(np.sqrt(best_sq)))
            if best_index is not None
            else (None, float("inf"))
        )
    return result


def reciprocal_repeat_pairs(
    early: Sequence[Icesat2Segment],
    late: Sequence[Icesat2Segment],
    *,
    max_distance_m: float = 15.0,
) -> list[Icesat2Pair]:
    """Pair only same-RGT, same-spot segments from different cycles."""

    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")

    early_groups: dict[tuple[int, int], list[Icesat2Segment]] = {}
    late_groups: dict[tuple[int, int], list[Icesat2Segment]] = {}
    for segment in early:
        early_groups.setdefault((segment.rgt, segment.spot), []).append(segment)
    for segment in late:
        late_groups.setdefault((segment.rgt, segment.spot), []).append(segment)

    pairs: list[Icesat2Pair] = []
    for group_key in sorted(set(early_groups) & set(late_groups)):
        early_group = early_groups[group_key]
        late_group = late_groups[group_key]
        early_to_late = _nearest_indices(
            early_group, late_group, max_distance_m=max_distance_m
        )
        late_to_early = _nearest_indices(
            late_group, early_group, max_distance_m=max_distance_m
        )
        for early_index, (late_index, distance) in enumerate(early_to_late):
            if late_index is None:
                continue
            reverse_early_index, _ = late_to_early[late_index]
            if reverse_early_index != early_index:
                continue
            early_segment = early_group[early_index]
            late_segment = late_group[late_index]
            if early_segment.cycle == late_segment.cycle:
                continue
            pairs.append(
                Icesat2Pair(
                    early=early_segment,
                    late=late_segment,
                    distance_m=distance,
                )
            )

    pairs.sort(
        key=lambda pair: (
            pair.distance_m,
            pair.early.rgt,
            pair.early.spot,
            pair.early.segment_id,
            pair.late.segment_id,
        )
    )
    return pairs


def pair_count_by_distance(
    pairs: Iterable[Icesat2Pair],
    *,
    thresholds_m: Sequence[float] = DEFAULT_DISTANCE_THRESHOLDS_M,
) -> dict[str, int]:
    pair_list = list(pairs)
    return {
        f"within_{float(threshold):g}m": sum(
            pair.distance_m <= float(threshold) for pair in pair_list
        )
        for threshold in thresholds_m
    }


def change_summary(
    pairs: Sequence[Icesat2Pair],
) -> dict[str, float | int | None]:
    changes = np.asarray(
        [pair.elevation_change_m for pair in pairs], dtype=np.float64
    )
    if changes.size == 0:
        return {
            "count": 0,
            "median_m": None,
            "nmad_m": None,
            "detection_floor_95_m": None,
            "p05_m": None,
            "p95_m": None,
            "min_m": None,
            "max_m": None,
        }
    spread = nmad(changes)
    return {
        "count": int(changes.size),
        "median_m": float(np.median(changes)),
        "nmad_m": spread,
        "detection_floor_95_m": None if spread is None else 1.96 * spread,
        "p05_m": float(np.percentile(changes, 5)),
        "p95_m": float(np.percentile(changes, 95)),
        "min_m": float(np.min(changes)),
        "max_m": float(np.max(changes)),
    }


def summary_by_distance(
    pairs: Sequence[Icesat2Pair],
    *,
    thresholds_m: Sequence[float] = DEFAULT_DISTANCE_THRESHOLDS_M,
) -> dict[str, dict[str, float | int | None]]:
    result: dict[str, dict[str, float | int | None]] = {}
    for threshold in thresholds_m:
        value = float(threshold)
        selected = [pair for pair in pairs if pair.distance_m <= value]
        result[f"within_{value:g}m"] = change_summary(selected)
    return result


def independent_midpoint_bins(
    pairs: Iterable[Icesat2Pair],
    *,
    bin_size_m: float = 100.0,
) -> int:
    size = float(bin_size_m)
    if size <= 0:
        raise ValueError("bin_size_m must be positive")
    return len(
        {
            (
                int(np.floor(pair.midpoint_x_m / size)),
                int(np.floor(pair.midpoint_y_m / size)),
            )
            for pair in pairs
        }
    )


def readiness(
    summaries: dict[str, dict[str, float | int | None]],
    *,
    target_m: float,
    minimum_pairs: int = 30,
) -> dict[str, object]:
    checked: list[dict[str, object]] = []
    supporting_band: str | None = None
    for band in ("within_5m", "within_10m"):
        summary = summaries.get(band, {})
        count = int(summary.get("count") or 0)
        floor_raw = summary.get("detection_floor_95_m")
        floor = float(floor_raw) if isinstance(floor_raw, (int, float)) else None
        supports = (
            count >= int(minimum_pairs)
            and floor is not None
            and floor <= float(target_m)
        )
        checked.append(
            {
                "distance_band": band,
                "pair_count": count,
                "detection_floor_95_m": floor,
                "supports_target": supports,
            }
        )
        if supports and supporting_band is None:
            supporting_band = band
    return {
        "target_m": float(target_m),
        "minimum_pairs": int(minimum_pairs),
        "ready_for_point_change_prototype": supporting_band is not None,
        "supporting_distance_band": supporting_band,
        "checked_bands": checked,
    }
