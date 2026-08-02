"""Derive reviewed measurement zones directly from the thickness raster.

The existing local-depth engine has always been able to turn a radar signal into
a depth, but only once somebody handed it at least two polygons whose real depth
was known. Those polygons never arrived, because obtaining them meant a site
visit or a records request.

This module removes that requirement. Where material was placed the ground rose,
so the raised ground *is* the outline and its height *is* the depth. The zones
are read out of the measurement rather than supplied alongside it.

Zone geometry is deliberately the largest axis-aligned rectangle that fits
wholly inside a measured region, not a traced outline of the region itself. A
traced outline hugs the edge of the change, where co-registration error, mixed
pixels and construction batter are worst, and can produce self-touching rings
that no downstream consumer validates for. An inscribed rectangle is always a
simple closed ring, always strictly interior, and always conservative. Losing
area at the margin is the correct trade when the alternative is a boundary that
quietly contaminates the number.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from app.pipeline.elevation_change.thickness import (
    DEFAULT_CORRELATION_LENGTH_M,
    DEFAULT_DETECTION_SIGMA,
    DEFAULT_INTERVAL_SIGMA,
    MIN_MEASURABLE_PIXELS,
    PolygonThickness,
    measure_polygon_thickness,
)

ANCHOR_ROLE = "anchor"
CANDIDATE_ROLE = "candidate"

# The interpolation engine refuses to extrapolate, so a withheld validation zone
# is only useful if it sits inside the range spanned by the retained anchors.
MIN_ANCHORS = 2
MIN_ZONES_WITH_WITHHELD_CANDIDATE = 3

# Two anchors whose measured depths differ by less than this cannot define a
# usable interpolation interval: the engine requires strictly distinct best
# depths, and near-identical anchors would make the fitted slope meaningless.
MIN_ANCHOR_DEPTH_SEPARATION_M = 0.05


class ZoneGenerationError(ValueError):
    """Raised when measured zones cannot be derived honestly."""


@dataclass(frozen=True, slots=True)
class MeasuredZone:
    """One rectangle of ground whose placed thickness has been measured."""

    zone_id: str
    role: str
    row_start: int
    row_stop: int
    col_start: int
    col_stop: int
    thickness: PolygonThickness

    @property
    def pixel_count(self) -> int:
        return (self.row_stop - self.row_start) * (self.col_stop - self.col_start)

    def mask(self, shape: tuple[int, int]) -> np.ndarray:
        mask = np.zeros(shape, dtype=bool)
        mask[self.row_start : self.row_stop, self.col_start : self.col_stop] = True
        return mask


def erode_mask(mask: np.ndarray, pixels: int) -> np.ndarray:
    """Shrink ``mask`` by ``pixels`` using 8-connectivity.

    Equivalent to the private helper in ``scripts/extract_operator_depth_signals.py``.
    It is reimplemented here rather than imported because ``scripts/`` is excluded
    from the distributable packages in ``pyproject.toml`` and so cannot be
    imported from ``app/``.
    """

    if pixels < 0:
        raise ZoneGenerationError("erosion pixels must be nonnegative")
    result = np.asarray(mask, dtype=bool).copy()
    if result.ndim != 2:
        raise ZoneGenerationError("mask must be 2D")
    height, width = result.shape
    for _ in range(int(pixels)):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        neighbours = [
            padded[row_offset : row_offset + height, col_offset : col_offset + width]
            for row_offset in range(3)
            for col_offset in range(3)
        ]
        result = np.logical_and.reduce(neighbours)
    return result


def label_components(mask: np.ndarray) -> list[np.ndarray]:
    """Split a boolean mask into 4-connected components, largest first."""

    working = np.asarray(mask, dtype=bool)
    if working.ndim != 2:
        raise ZoneGenerationError("mask must be 2D")

    seen = np.zeros_like(working, dtype=bool)
    components: list[np.ndarray] = []
    height, width = working.shape

    for start_row in range(height):
        for start_col in range(width):
            if not working[start_row, start_col] or seen[start_row, start_col]:
                continue
            component = np.zeros_like(working, dtype=bool)
            queue: deque[tuple[int, int]] = deque([(start_row, start_col)])
            seen[start_row, start_col] = True
            while queue:
                row, col = queue.popleft()
                component[row, col] = True
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if working[next_row, next_col] and not seen[next_row, next_col]:
                        seen[next_row, next_col] = True
                        queue.append((next_row, next_col))
            components.append(component)

    components.sort(key=lambda item: int(item.sum()), reverse=True)
    return components


def largest_inscribed_rectangle(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """Return ``(row_start, row_stop, col_start, col_stop)`` of the biggest
    all-true axis-aligned rectangle, or None when the mask is empty.

    Standard maximal-rectangle-under-histogram scan: build the running column
    heights row by row and solve each row's histogram with a monotonic stack.
    """

    working = np.asarray(mask, dtype=bool)
    if working.ndim != 2:
        raise ZoneGenerationError("mask must be 2D")
    if not working.any():
        return None

    height, width = working.shape
    heights = np.zeros(width, dtype=np.int64)
    best_area = 0
    best: tuple[int, int, int, int] | None = None

    for row in range(height):
        heights = np.where(working[row], heights + 1, 0)

        stack: list[int] = []
        for col in range(width + 1):
            current = int(heights[col]) if col < width else 0
            while stack and int(heights[stack[-1]]) >= current:
                bar_index = stack.pop()
                bar_height = int(heights[bar_index])
                left = stack[-1] + 1 if stack else 0
                bar_width = col - left
                area = bar_height * bar_width
                if bar_height > 0 and area > best_area:
                    best_area = area
                    best = (row - bar_height + 1, row + 1, left, col)
            stack.append(col)

    return best


def rectangle_ring(
    *,
    row_start: int,
    row_stop: int,
    col_start: int,
    col_stop: int,
    transform: Sequence[float],
) -> list[list[float]]:
    """Convert pixel-index bounds into a closed GeoJSON ring in the grid CRS.

    ``transform`` is the six-value affine used everywhere else in the pipeline,
    applied at pixel *edges* rather than centres so the ring encloses exactly the
    pixels that were measured.
    """

    if len(transform) != 6:
        raise ZoneGenerationError("transform must contain six values")
    a, b, c, d, e, f = (float(value) for value in transform)

    def position(col: float, row: float) -> list[float]:
        return [a * col + b * row + c, d * col + e * row + f]

    # Counter-clockwise for a north-up grid: lower-left, lower-right, upper-right,
    # upper-left, then repeat the first position to close the ring.
    corners = [
        position(col_start, row_stop),
        position(col_stop, row_stop),
        position(col_stop, row_start),
        position(col_start, row_start),
    ]
    return [*corners, list(corners[0])]


def _distinct_by_depth(
    zones: Sequence[MeasuredZone],
    *,
    minimum_separation_m: float,
) -> list[MeasuredZone]:
    """Keep zones whose measured depths are far enough apart to be usable."""

    ordered = sorted(zones, key=lambda zone: zone.thickness.mean_change_m)
    kept: list[MeasuredZone] = []
    for zone in ordered:
        if not kept:
            kept.append(zone)
            continue
        if zone.thickness.mean_change_m - kept[-1].thickness.mean_change_m >= minimum_separation_m:
            kept.append(zone)
    return kept


def generate_measured_zones(
    delta_m: np.ndarray,
    *,
    sigma_stable_m: float,
    pixel_area_m2: float,
    band_count: int = 3,
    erosion_pixels: int = 2,
    min_pixels: int = MIN_MEASURABLE_PIXELS,
    correlation_length_m: float = DEFAULT_CORRELATION_LENGTH_M,
    detection_sigma: float = DEFAULT_DETECTION_SIGMA,
    minimum_separation_m: float = MIN_ANCHOR_DEPTH_SEPARATION_M,
    zone_id_prefix: str = "elev",
) -> list[MeasuredZone]:
    """Find distinct measured-thickness zones in a co-registered difference.

    Accumulation is split into thickness bands so the resulting zones span a
    range of depths rather than clustering at one value; an interpolation
    anchored on two near-identical depths would carry no information.
    """

    if band_count < 2:
        raise ZoneGenerationError("band_count must be at least 2")
    if pixel_area_m2 <= 0:
        raise ZoneGenerationError("pixel_area_m2 must be positive")

    delta = np.asarray(delta_m, dtype=np.float64)
    threshold = float(detection_sigma) * float(sigma_stable_m)
    accumulation = np.isfinite(delta) & (delta > threshold)
    if not accumulation.any():
        return []

    # Erode before doing anything else. A per-pixel significance test on quiet
    # ground still passes for a few percent of pixels by chance, and at typical
    # cover areas that speckle can outnumber the genuinely raised pixels. Left in
    # place it drags the band edges into the middle of real covers and splits one
    # cover across two bands. Isolated speckle does not survive erosion; a real
    # cover does.
    core = erode_mask(accumulation, erosion_pixels)
    if not core.any():
        return []

    values = delta[core]
    # Quantile edges rather than equal-width bins: equal-width bins over a skewed
    # thickness distribution routinely leave every band but one empty.
    quantiles = np.linspace(0.0, 1.0, int(band_count) + 1)
    edges = np.quantile(values, quantiles)
    edges[0] = -np.inf
    edges[-1] = np.inf

    zones: list[MeasuredZone] = []
    for band_index in range(int(band_count)):
        low = float(edges[band_index])
        high = float(edges[band_index + 1])
        band_mask = core & (delta > low) & (delta <= high)
        if not band_mask.any():
            continue

        for component in label_components(band_mask):
            if int(component.sum()) < int(min_pixels):
                continue
            rectangle = largest_inscribed_rectangle(component)
            if rectangle is None:
                continue
            row_start, row_stop, col_start, col_stop = rectangle
            zone_mask = np.zeros_like(delta, dtype=bool)
            zone_mask[row_start:row_stop, col_start:col_stop] = True
            if int(zone_mask.sum()) < int(min_pixels):
                continue

            zone_id = f"{zone_id_prefix}-b{band_index + 1}-{len(zones) + 1:02d}"
            thickness = measure_polygon_thickness(
                delta,
                zone_mask,
                zone_id=zone_id,
                sigma_stable_m=sigma_stable_m,
                pixel_area_m2=pixel_area_m2,
                correlation_length_m=correlation_length_m,
                detection_sigma=detection_sigma,
                min_pixels=min_pixels,
            )
            if not thickness.measurable:
                continue
            zones.append(
                MeasuredZone(
                    zone_id=zone_id,
                    role=ANCHOR_ROLE,
                    row_start=row_start,
                    row_stop=row_stop,
                    col_start=col_start,
                    col_stop=col_stop,
                    thickness=thickness,
                )
            )

    return _distinct_by_depth(zones, minimum_separation_m=minimum_separation_m)


def assign_roles(
    zones: Sequence[MeasuredZone],
    *,
    withhold_for_validation: bool = True,
) -> list[MeasuredZone]:
    """Split measured zones into anchors and candidates.

    With ``withhold_for_validation`` the zone nearest the middle of the measured
    depth range becomes the candidate and its measured depth is kept out of the
    anchor set. Predicting a zone whose true depth is known, from anchors that
    never saw it, is the only self-check available without external truth.

    The middle zone is chosen deliberately: the engine abstains rather than
    extrapolate, so withholding an extreme zone would guarantee an abstention and
    prove nothing.
    """

    ordered = sorted(zones, key=lambda zone: zone.thickness.mean_change_m)
    if len(ordered) < MIN_ANCHORS:
        raise ZoneGenerationError(
            f"at least {MIN_ANCHORS} measured zones are required, found {len(ordered)}"
        )

    if not withhold_for_validation:
        anchors = ordered
        candidates: list[MeasuredZone] = []
    elif len(ordered) < MIN_ZONES_WITH_WITHHELD_CANDIDATE:
        raise ZoneGenerationError(
            "withholding a validation zone requires at least "
            f"{MIN_ZONES_WITH_WITHHELD_CANDIDATE} measured zones, found {len(ordered)}"
        )
    else:
        middle = len(ordered) // 2
        candidates = [ordered[middle]]
        anchors = [zone for index, zone in enumerate(ordered) if index != middle]

    assigned = [
        MeasuredZone(
            zone_id=zone.zone_id,
            role=ANCHOR_ROLE,
            row_start=zone.row_start,
            row_stop=zone.row_stop,
            col_start=zone.col_start,
            col_stop=zone.col_stop,
            thickness=zone.thickness,
        )
        for zone in anchors
    ]
    assigned.extend(
        MeasuredZone(
            zone_id=zone.zone_id,
            role=CANDIDATE_ROLE,
            row_start=zone.row_start,
            row_stop=zone.row_stop,
            col_start=zone.col_start,
            col_stop=zone.col_stop,
            thickness=zone.thickness,
        )
        for zone in candidates
    )
    return assigned


def zones_to_geojson(
    zones: Iterable[MeasuredZone],
    *,
    transform: Sequence[float],
    crs: str,
    interval_sigma: float = DEFAULT_INTERVAL_SIGMA,
) -> dict[str, Any]:
    """Render measured zones as the reviewed-zones FeatureCollection.

    The output matches the schema the browser preflight and the signal extractor
    already accept, so nothing downstream needs to change. ``template_only`` is
    never emitted: this file is complete by construction, and the preflight
    rejects any file still carrying that marker.
    """

    features: list[dict[str, Any]] = []
    anchor_count = 0
    candidate_count = 0

    for zone in zones:
        properties: dict[str, Any] = {
            "feature_id": zone.zone_id,
            "role": zone.role,
            "source": "measured_elevation_change",
            "measured_pixel_count": int(zone.thickness.pixel_count),
            "measured_area_m2": round(float(zone.thickness.area_m2), 3),
            "measured_sigma_m": round(float(zone.thickness.sigma_m), 6),
        }

        if zone.role == ANCHOR_ROLE:
            depth_range = zone.thickness.depth_range(interval_sigma=interval_sigma)
            if depth_range is None:
                raise ZoneGenerationError(
                    f"anchor {zone.zone_id} has no measurable depth range"
                )
            properties["depth_min_m"] = round(float(depth_range.minimum_m), 6)
            properties["depth_best_m"] = round(float(depth_range.best_m), 6)
            properties["depth_max_m"] = round(float(depth_range.maximum_m), 6)
            anchor_count += 1
        else:
            # The withheld measurement travels as a separate property so it can
            # be compared afterwards. It is deliberately not named like the
            # anchor depth fields, so that no consumer can mistake it for a
            # supplied depth and quietly calibrate on it.
            withheld = zone.thickness.depth_range(interval_sigma=interval_sigma)
            if withheld is not None:
                properties["withheld_measured_depth_best_m"] = round(float(withheld.best_m), 6)
                properties["withheld_measured_depth_min_m"] = round(float(withheld.minimum_m), 6)
                properties["withheld_measured_depth_max_m"] = round(float(withheld.maximum_m), 6)
            candidate_count += 1

        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        rectangle_ring(
                            row_start=zone.row_start,
                            row_stop=zone.row_stop,
                            col_start=zone.col_start,
                            col_stop=zone.col_stop,
                            transform=transform,
                        )
                    ],
                },
            }
        )

    if anchor_count < MIN_ANCHORS:
        raise ZoneGenerationError(
            f"at least {MIN_ANCHORS} anchor zones are required, found {anchor_count}"
        )
    if candidate_count < 1:
        raise ZoneGenerationError("at least one candidate zone is required")

    return {
        "type": "FeatureCollection",
        "crs_hint": crs,
        "generated_by": "measured_elevation_change_v1",
        "provenance": [
            "Anchor depths are measured public elevation change, not operator survey records.",
            "Depths are placed-material thickness, not depth to a buried object.",
            "Zone outlines are conservative interior rectangles, not surveyed boundaries.",
        ],
        "features": features,
    }
