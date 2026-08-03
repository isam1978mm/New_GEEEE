"""Pure helpers for scanning ICESat-2 ATL08 terrain time series for steps.

The scan is intentionally conservative.  A single high point is not a candidate.
A surviving candidate must look like a persistent upward step in one exact ATL08
segment and must be supported by neighbouring segments with the same event
window and a consistent step magnitude.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment


@dataclass(frozen=True, slots=True)
class SegmentStepAssessment:
    rgt: int
    spot: int
    segment_id: str
    x_m: float
    y_m: float
    longitude: float
    latitude: float
    classification: str
    observation_count: int
    cycle_count: int
    pre_cycle: int | None
    post_cycle: int | None
    event_start: datetime | None
    event_end: datetime | None
    pre_median_m: float | None
    post_median_m: float | None
    step_m: float | None
    pre_nmad_m: float | None
    post_nmad_m: float | None
    residual_nmad_m: float | None
    linear_residual_nmad_m: float | None
    dominant_increment_ratio: float | None
    positive_increment_fraction: float | None
    score: float | None
    observations: tuple[Icesat2Segment, ...]


@dataclass(frozen=True, slots=True)
class StepCluster:
    rgt: int
    spot: int
    pre_cycle: int
    post_cycle: int
    event_start: datetime
    event_end: datetime
    assessments: tuple[SegmentStepAssessment, ...]
    median_step_m: float
    step_nmad_m: float
    centroid_x_m: float
    centroid_y_m: float
    centroid_longitude: float
    centroid_latitude: float
    spatial_extent_m: float


def nmad(values: Sequence[float] | np.ndarray) -> float | None:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return None
    median = float(np.median(array))
    return float(1.4826 * np.median(np.abs(array - median)))


def _linear_residual_nmad(
    observations: Sequence[Icesat2Segment],
) -> float | None:
    if len(observations) < 2:
        return None
    t0 = observations[0].observed_at.timestamp()
    times = np.asarray(
        [
            (item.observed_at.timestamp() - t0) / 86400.0
            for item in observations
        ],
        dtype=np.float64,
    )
    heights = np.asarray(
        [item.height_m for item in observations],
        dtype=np.float64,
    )
    if np.ptp(times) <= 0.0:
        return None
    slope, intercept = np.polyfit(times, heights, 1)
    residuals = heights - (slope * times + intercept)
    return nmad(residuals)


def _empty_assessment(
    ordered: Sequence[Icesat2Segment],
    *,
    classification: str,
) -> SegmentStepAssessment:
    first = ordered[0]
    return SegmentStepAssessment(
        rgt=first.rgt,
        spot=first.spot,
        segment_id=first.segment_id,
        x_m=float(np.median([item.x_m for item in ordered])),
        y_m=float(np.median([item.y_m for item in ordered])),
        longitude=float(np.median([item.longitude for item in ordered])),
        latitude=float(np.median([item.latitude for item in ordered])),
        classification=classification,
        observation_count=len(ordered),
        cycle_count=len({item.cycle for item in ordered}),
        pre_cycle=None,
        post_cycle=None,
        event_start=None,
        event_end=None,
        pre_median_m=None,
        post_median_m=None,
        step_m=None,
        pre_nmad_m=None,
        post_nmad_m=None,
        residual_nmad_m=None,
        linear_residual_nmad_m=None,
        dominant_increment_ratio=None,
        positive_increment_fraction=None,
        score=None,
        observations=tuple(ordered),
    )


def assess_segment_series(
    observations: Sequence[Icesat2Segment],
    *,
    minimum_epochs: int = 4,
    minimum_side_epochs: int = 2,
    minimum_step_m: float = 0.3,
    maximum_plateau_nmad_m: float = 0.25,
    minimum_step_dominance: float = 0.6,
) -> SegmentStepAssessment:
    """Classify one exact ATL08 segment through time.

    ``step_up_candidate`` means a single positive increment dominates the total
    positive movement, with stable plateaus on both sides.  ``ramp_up`` means
    the series rises more gradually across several epochs.  The function does
    not claim a cause for either pattern.
    """

    ordered = sorted(
        observations,
        key=lambda item: (item.observed_at, item.cycle, item.segment_id),
    )
    if not ordered:
        raise ValueError("observations must not be empty")
    if minimum_epochs < 4:
        raise ValueError("minimum_epochs must be at least four")
    if minimum_side_epochs < 2:
        raise ValueError("minimum_side_epochs must be at least two")
    if len(ordered) < minimum_epochs or len({item.cycle for item in ordered}) < minimum_epochs:
        return _empty_assessment(ordered, classification="insufficient_epochs")

    heights = np.asarray(
        [item.height_m for item in ordered],
        dtype=np.float64,
    )
    increments = np.diff(heights)
    positive_increments = np.maximum(increments, 0.0)
    negative_increments = np.maximum(-increments, 0.0)
    total_positive = float(np.sum(positive_increments))
    total_negative = float(np.sum(negative_increments))
    positive_fraction = (
        float(np.mean(increments > 0.0)) if increments.size else 0.0
    )

    best: dict[str, float | int | None] | None = None
    final_split = len(ordered) - minimum_side_epochs
    for split in range(minimum_side_epochs, final_split + 1):
        pre = heights[:split]
        post = heights[split:]
        pre_median = float(np.median(pre))
        post_median = float(np.median(post))
        step = post_median - pre_median
        pre_spread = nmad(pre)
        post_spread = nmad(post)
        residuals = np.concatenate(
            (pre - pre_median, post - post_median)
        )
        residual_spread = nmad(residuals)
        boundary_increment = float(heights[split] - heights[split - 1])
        positive_dominance = (
            max(boundary_increment, 0.0) / total_positive
            if total_positive > 0.0
            else 0.0
        )
        negative_dominance = (
            max(-boundary_increment, 0.0) / total_negative
            if total_negative > 0.0
            else 0.0
        )
        score = step / max(float(residual_spread or 0.0), 0.05)
        candidate = {
            "split": split,
            "pre_median": pre_median,
            "post_median": post_median,
            "step": step,
            "pre_spread": pre_spread,
            "post_spread": post_spread,
            "residual_spread": residual_spread,
            "positive_dominance": positive_dominance,
            "negative_dominance": negative_dominance,
            "score": score,
        }
        if best is None:
            best = candidate
            continue
        current_key = (
            float(candidate["score"]),
            float(candidate["step"]),
            -float(candidate["residual_spread"] or 0.0),
            -int(candidate["split"]),
        )
        best_key = (
            float(best["score"]),
            float(best["step"]),
            -float(best["residual_spread"] or 0.0),
            -int(best["split"]),
        )
        if current_key > best_key:
            best = candidate

    assert best is not None
    split = int(best["split"])
    pre_spread = best["pre_spread"]
    post_spread = best["post_spread"]
    residual_spread = best["residual_spread"]
    step = float(best["step"])
    positive_dominance = float(best["positive_dominance"])
    negative_dominance = float(best["negative_dominance"])
    plateau_ok = (
        isinstance(pre_spread, (int, float))
        and isinstance(post_spread, (int, float))
        and isinstance(residual_spread, (int, float))
        and float(pre_spread) <= maximum_plateau_nmad_m
        and float(post_spread) <= maximum_plateau_nmad_m
        and float(residual_spread) <= maximum_plateau_nmad_m
    )

    if (
        step >= minimum_step_m
        and plateau_ok
        and positive_dominance >= minimum_step_dominance
    ):
        classification = "step_up_candidate"
    elif (
        -step >= minimum_step_m
        and plateau_ok
        and negative_dominance >= minimum_step_dominance
    ):
        classification = "step_down_candidate"
    elif (
        heights[-1] - heights[0] >= minimum_step_m
        and positive_fraction >= 2.0 / 3.0
        and positive_dominance < minimum_step_dominance
    ):
        classification = "ramp_up"
    elif float(np.ptp(heights)) <= 2.0 * maximum_plateau_nmad_m:
        classification = "stable"
    else:
        classification = "irregular_or_noise"

    first = ordered[0]
    return SegmentStepAssessment(
        rgt=first.rgt,
        spot=first.spot,
        segment_id=first.segment_id,
        x_m=float(np.median([item.x_m for item in ordered])),
        y_m=float(np.median([item.y_m for item in ordered])),
        longitude=float(np.median([item.longitude for item in ordered])),
        latitude=float(np.median([item.latitude for item in ordered])),
        classification=classification,
        observation_count=len(ordered),
        cycle_count=len({item.cycle for item in ordered}),
        pre_cycle=ordered[split - 1].cycle,
        post_cycle=ordered[split].cycle,
        event_start=ordered[split - 1].observed_at,
        event_end=ordered[split].observed_at,
        pre_median_m=float(best["pre_median"]),
        post_median_m=float(best["post_median"]),
        step_m=step,
        pre_nmad_m=float(pre_spread) if isinstance(pre_spread, (int, float)) else None,
        post_nmad_m=float(post_spread) if isinstance(post_spread, (int, float)) else None,
        residual_nmad_m=(
            float(residual_spread)
            if isinstance(residual_spread, (int, float))
            else None
        ),
        linear_residual_nmad_m=_linear_residual_nmad(ordered),
        dominant_increment_ratio=(
            positive_dominance if step >= 0.0 else negative_dominance
        ),
        positive_increment_fraction=positive_fraction,
        score=float(best["score"]),
        observations=tuple(ordered),
    )


def scan_segment_series(
    segments: Sequence[Icesat2Segment],
    **assessment_kwargs: object,
) -> list[SegmentStepAssessment]:
    groups: dict[tuple[int, int, str], list[Icesat2Segment]] = {}
    for segment in segments:
        groups.setdefault(
            (segment.rgt, segment.spot, segment.segment_id), []
        ).append(segment)
    assessments = [
        assess_segment_series(values, **assessment_kwargs)
        for _, values in sorted(groups.items())
    ]
    assessments.sort(
        key=lambda item: (
            item.classification != "step_up_candidate",
            -(item.score or float("-inf")),
            item.rgt,
            item.spot,
            item.segment_id,
        )
    )
    return assessments


def cluster_step_candidates(
    assessments: Sequence[SegmentStepAssessment],
    *,
    neighbor_distance_m: float = 250.0,
    minimum_neighbor_segments: int = 3,
    maximum_cluster_step_nmad_m: float = 0.25,
) -> list[StepCluster]:
    """Keep connected neighbouring step candidates with one event window."""

    if neighbor_distance_m <= 0:
        raise ValueError("neighbor_distance_m must be positive")
    if minimum_neighbor_segments <= 0:
        raise ValueError("minimum_neighbor_segments must be positive")

    grouped: dict[
        tuple[int, int, int, int], list[SegmentStepAssessment]
    ] = {}
    for item in assessments:
        if (
            item.classification != "step_up_candidate"
            or item.pre_cycle is None
            or item.post_cycle is None
            or item.event_start is None
            or item.event_end is None
            or item.step_m is None
        ):
            continue
        grouped.setdefault(
            (item.rgt, item.spot, item.pre_cycle, item.post_cycle), []
        ).append(item)

    clusters: list[StepCluster] = []
    limit_sq = float(neighbor_distance_m) ** 2
    for (rgt, spot, pre_cycle, post_cycle), items in sorted(grouped.items()):
        remaining = set(range(len(items)))
        while remaining:
            seed = remaining.pop()
            component = {seed}
            frontier = [seed]
            while frontier:
                current = frontier.pop()
                current_item = items[current]
                neighbours: list[int] = []
                for candidate in list(remaining):
                    other = items[candidate]
                    dx = current_item.x_m - other.x_m
                    dy = current_item.y_m - other.y_m
                    if dx * dx + dy * dy <= limit_sq:
                        neighbours.append(candidate)
                for candidate in neighbours:
                    remaining.remove(candidate)
                    component.add(candidate)
                    frontier.append(candidate)

            selected = [items[index] for index in sorted(component)]
            if len(selected) < minimum_neighbor_segments:
                continue
            steps = np.asarray(
                [float(item.step_m) for item in selected],
                dtype=np.float64,
            )
            spread = float(nmad(steps) or 0.0)
            if spread > maximum_cluster_step_nmad_m:
                continue
            xs = np.asarray([item.x_m for item in selected], dtype=np.float64)
            ys = np.asarray([item.y_m for item in selected], dtype=np.float64)
            centroid_x = float(np.mean(xs))
            centroid_y = float(np.mean(ys))
            extent = float(
                np.max(
                    np.sqrt(
                        (xs - centroid_x) ** 2 + (ys - centroid_y) ** 2
                    )
                )
            )
            clusters.append(
                StepCluster(
                    rgt=rgt,
                    spot=spot,
                    pre_cycle=pre_cycle,
                    post_cycle=post_cycle,
                    event_start=min(
                        item.event_start
                        for item in selected
                        if item.event_start is not None
                    ),
                    event_end=max(
                        item.event_end
                        for item in selected
                        if item.event_end is not None
                    ),
                    assessments=tuple(selected),
                    median_step_m=float(np.median(steps)),
                    step_nmad_m=spread,
                    centroid_x_m=centroid_x,
                    centroid_y_m=centroid_y,
                    centroid_longitude=float(
                        np.mean([item.longitude for item in selected])
                    ),
                    centroid_latitude=float(
                        np.mean([item.latitude for item in selected])
                    ),
                    spatial_extent_m=extent,
                )
            )

    clusters.sort(
        key=lambda item: (
            -len(item.assessments),
            -item.median_step_m,
            item.step_nmad_m,
            item.rgt,
            item.spot,
            item.pre_cycle,
            item.post_cycle,
        )
    )
    return clusters
