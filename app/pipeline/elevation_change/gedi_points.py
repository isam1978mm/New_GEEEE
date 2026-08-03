"""Pure helpers for auditing repeated GEDI point observations.

This module deliberately contains no Earth Engine imports. The live script
loads GEDI L2A vector tables, then hands ordinary point records to these
functions so pairing and summary logic can be unit-tested offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable, Sequence

import numpy as np

GEDI_EPOCH = datetime(2018, 1, 1, tzinfo=UTC)
DEFAULT_PAIR_THRESHOLDS_M = (5.0, 10.0, 15.0, 25.0)


@dataclass(frozen=True, slots=True)
class GediShot:
    """One quality-filtered GEDI L2A footprint."""

    shot_number: str
    observed_at: datetime
    longitude: float
    latitude: float
    x_m: float
    y_m: float
    elevation_m: float
    beam: int
    orbit_number: int
    table_id: str
    sensitivity: float | None = None


@dataclass(frozen=True, slots=True)
class GediPair:
    """A unique reciprocal-nearest early/late footprint pair."""

    early: GediShot
    late: GediShot
    distance_m: float

    @property
    def elevation_change_m(self) -> float:
        return float(self.late.elevation_m - self.early.elevation_m)

    @property
    def midpoint_x_m(self) -> float:
        return float((self.early.x_m + self.late.x_m) / 2.0)

    @property
    def midpoint_y_m(self) -> float:
        return float((self.early.y_m + self.late.y_m) / 2.0)


def datetime_from_delta_time(delta_time_s: float) -> datetime:
    """Convert GEDI seconds since 2018-01-01 UTC to an aware datetime."""

    value = float(delta_time_s)
    if not np.isfinite(value):
        raise ValueError("GEDI delta_time must be finite")
    return GEDI_EPOCH + timedelta(seconds=value)


def nmad(values: Sequence[float] | np.ndarray) -> float | None:
    """Normalised median absolute deviation, or None for no finite values."""

    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return None
    median = float(np.median(array))
    return float(1.4826 * np.median(np.abs(array - median)))


def _nearest_indices(
    query: Sequence[GediShot],
    candidates: Sequence[GediShot],
    *,
    max_distance_m: float,
) -> list[tuple[int | None, float]]:
    """Find nearest candidate for each query with a small spatial hash.

    The maximum search radius is also the bucket size, so only the query bucket
    and its eight neighbours need inspection. This avoids adding a SciPy runtime
    dependency solely for a read-only audit script.
    """

    limit = float(max_distance_m)
    buckets: dict[tuple[int, int], list[int]] = {}
    for index, shot in enumerate(candidates):
        key = (int(np.floor(shot.x_m / limit)), int(np.floor(shot.y_m / limit)))
        buckets.setdefault(key, []).append(index)

    result: list[tuple[int | None, float]] = []
    limit_sq = limit * limit
    for shot in query:
        cell_x = int(np.floor(shot.x_m / limit))
        cell_y = int(np.floor(shot.y_m / limit))
        best_index: int | None = None
        best_sq = float("inf")
        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                for candidate_index in buckets.get(
                    (cell_x + offset_x, cell_y + offset_y), ()
                ):
                    candidate = candidates[candidate_index]
                    dx = candidate.x_m - shot.x_m
                    dy = candidate.y_m - shot.y_m
                    distance_sq = dx * dx + dy * dy
                    if distance_sq > limit_sq:
                        continue
                    if (
                        distance_sq < best_sq
                        or (
                            distance_sq == best_sq
                            and best_index is not None
                            and candidate.shot_number
                            < candidates[best_index].shot_number
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


def reciprocal_nearest_pairs(
    early: Sequence[GediShot],
    late: Sequence[GediShot],
    *,
    max_distance_m: float = 25.0,
) -> list[GediPair]:
    """Return unique reciprocal-nearest pairs within ``max_distance_m``.

    A simple nearest-neighbour join can reuse one late shot for many early
    shots. Reciprocal matching keeps a pair only when each shot is the other's
    nearest neighbour, so every footprint appears at most once.
    """

    limit = float(max_distance_m)
    if limit <= 0:
        raise ValueError("max_distance_m must be positive")
    if not early or not late:
        return []

    early_to_late = _nearest_indices(early, late, max_distance_m=limit)
    late_to_early = _nearest_indices(late, early, max_distance_m=limit)

    pairs: list[GediPair] = []
    for early_index, (late_index, distance) in enumerate(early_to_late):
        if late_index is None:
            continue
        reverse_early_index, _ = late_to_early[late_index]
        if reverse_early_index != early_index:
            continue
        pairs.append(
            GediPair(
                early=early[early_index],
                late=late[late_index],
                distance_m=distance,
            )
        )

    pairs.sort(
        key=lambda pair: (
            pair.distance_m,
            pair.early.shot_number,
            pair.late.shot_number,
        )
    )
    return pairs


def pair_threshold_counts(
    pairs: Iterable[GediPair],
    *,
    thresholds_m: Sequence[float] = DEFAULT_PAIR_THRESHOLDS_M,
) -> dict[str, int]:
    """Count unique pairs at each distance threshold."""

    pair_list = list(pairs)
    result: dict[str, int] = {}
    for threshold in thresholds_m:
        value = float(threshold)
        if value <= 0:
            raise ValueError("pair thresholds must be positive")
        result[f"within_{value:g}m"] = sum(
            pair.distance_m <= value for pair in pair_list
        )
    return result


def independent_spatial_bin_count(
    pairs: Iterable[GediPair],
    *,
    bin_size_m: float = 100.0,
) -> int:
    """Count occupied midpoint bins as a transparent dispersion metric."""

    size = float(bin_size_m)
    if size <= 0:
        raise ValueError("bin_size_m must be positive")
    bins = {
        (
            int(np.floor(pair.midpoint_x_m / size)),
            int(np.floor(pair.midpoint_y_m / size)),
        )
        for pair in pairs
    }
    return len(bins)


def elevation_change_summary(
    pairs: Sequence[GediPair],
) -> dict[str, float | int | None]:
    """Robust statistics for raw late-minus-early elevation change."""

    changes = np.asarray(
        [pair.elevation_change_m for pair in pairs],
        dtype=np.float64,
    )
    if changes.size == 0:
        return {
            "count": 0,
            "median_m": None,
            "nmad_m": None,
            "p05_m": None,
            "p95_m": None,
            "min_m": None,
            "max_m": None,
        }
    return {
        "count": int(changes.size),
        "median_m": float(np.median(changes)),
        "nmad_m": nmad(changes),
        "p05_m": float(np.percentile(changes, 5)),
        "p95_m": float(np.percentile(changes, 95)),
        "min_m": float(np.min(changes)),
        "max_m": float(np.max(changes)),
    }
