"""Vertical co-registration of two elevation surfaces over one locked grid.

Two elevation surfaces acquired years apart by different sensors almost never
share a datum exactly. A constant vertical bias of a metre or more is ordinary.
Differencing them without removing that bias would report the bias as placed
material everywhere, including over ground that never changed.

The correction here is the vertical half of the standard DEM-of-difference
workflow: find ground that is unlikely to have changed, measure the median
offset there, and subtract it. The spread that remains over that same stable
ground is the honest noise floor of the pair, and every downstream uncertainty
is derived from it.

Sign convention, used everywhere in this package:

    delta = late - early

so a positive value means the ground got higher, which means material was added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# 1.4826 rescales the median absolute deviation so that, for normally
# distributed values, NMAD estimates the same quantity as the standard
# deviation. Unlike the standard deviation it is not dragged upward by the
# changed ground we are specifically trying to exclude.
NMAD_SCALE = 1.4826

# Relative tolerance used only when the robust spread collapses to exactly zero.
EXACT_MATCH_TOLERANCE_M = 1e-9

DEFAULT_MAX_SLOPE_DEG = 15.0
DEFAULT_ROBUST_SIGMA_MULTIPLIER = 3.0
DEFAULT_ITERATIONS = 3
MIN_STABLE_PIXELS = 100


class CoregistrationError(ValueError):
    """Raised when two elevation surfaces cannot be co-registered honestly."""


@dataclass(frozen=True, slots=True)
class StableGroundStats:
    """What the unchanged ground tells us about the quality of the pair."""

    offset_m: float
    sigma_m: float
    pixel_count: int
    pixel_fraction: float

    def as_mapping(self) -> dict[str, Any]:
        return {
            "offset_m": round(float(self.offset_m), 6),
            "sigma_m": round(float(self.sigma_m), 6),
            "pixel_count": int(self.pixel_count),
            "pixel_fraction": round(float(self.pixel_fraction), 6),
        }


@dataclass(frozen=True, slots=True)
class CoregistrationResult:
    """A co-registered elevation difference plus the evidence behind it."""

    delta_m: np.ndarray
    valid_mask: np.ndarray
    stable_mask: np.ndarray
    stats: StableGroundStats
    iterations: int
    warnings: tuple[str, ...]

    def as_mapping(self) -> dict[str, Any]:
        return {
            "stable_ground": self.stats.as_mapping(),
            "iterations": int(self.iterations),
            "valid_pixel_count": int(self.valid_mask.sum()),
            "warnings": list(self.warnings),
        }


def nmad(values: np.ndarray) -> float:
    """Return the normalised median absolute deviation of ``values``.

    This is the robust spread estimator used throughout the package. It ignores
    non-finite entries and returns 0.0 for an empty input.
    """

    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return 0.0
    median = float(np.median(finite))
    return float(NMAD_SCALE * np.median(np.abs(finite - median)))


def _finite_mask(array: np.ndarray, *, nodata: float) -> np.ndarray:
    return np.isfinite(array) & (array != nodata)


def select_stable_mask(
    delta_m: np.ndarray,
    *,
    valid_mask: np.ndarray,
    slope_deg: np.ndarray | None = None,
    max_slope_deg: float = DEFAULT_MAX_SLOPE_DEG,
    robust_sigma_multiplier: float = DEFAULT_ROBUST_SIGMA_MULTIPLIER,
) -> np.ndarray:
    """Select pixels that most plausibly did not change between the two epochs.

    Two independent filters are applied:

    - Slope. Steep ground differences badly for reasons that have nothing to do
      with added material: a small horizontal misregistration turns into a large
      apparent vertical change wherever the surface is tilted. Steep pixels are
      therefore poor evidence about the datum offset and are dropped when a
      slope raster is supplied.
    - Robust outlier rejection. Ground that genuinely changed is exactly the
      signal we are trying to measure, so it must not be allowed to influence
      the datum estimate. Pixels beyond ``robust_sigma_multiplier`` NMADs of the
      median difference are excluded.

    The result is a boolean mask, never an in-place modification of the inputs.
    """

    if delta_m.shape != valid_mask.shape:
        raise CoregistrationError("delta and valid mask must share one shape")
    if robust_sigma_multiplier <= 0:
        raise CoregistrationError("robust_sigma_multiplier must be positive")

    stable = np.array(valid_mask, dtype=bool, copy=True)
    stable &= np.isfinite(delta_m)

    if slope_deg is not None:
        if slope_deg.shape != delta_m.shape:
            raise CoregistrationError("slope raster must share the delta shape")
        if max_slope_deg <= 0:
            raise CoregistrationError("max_slope_deg must be positive")
        stable &= np.isfinite(slope_deg)
        stable &= slope_deg <= float(max_slope_deg)

    if not stable.any():
        return stable

    candidate_values = delta_m[stable]
    median = float(np.median(candidate_values))
    spread = nmad(candidate_values)

    if spread > 0.0:
        tolerance = float(robust_sigma_multiplier) * spread
    else:
        # Zero spread means the overwhelming majority of candidates share one
        # exact value, which happens with noiseless or heavily quantised inputs.
        # The limit of the test above is then intolerance of any deviation at
        # all: anything differing from the median is infinitely many robust
        # sigmas away. Keeping such pixels would let genuinely changed ground
        # set the datum, which is the precise failure this function exists to
        # prevent. Only floating-point dust is forgiven.
        tolerance = EXACT_MATCH_TOLERANCE_M * max(1.0, abs(median))

    stable &= np.abs(delta_m - median) <= tolerance
    return stable


def estimate_stable_ground(
    delta_m: np.ndarray,
    *,
    valid_mask: np.ndarray,
    slope_deg: np.ndarray | None = None,
    max_slope_deg: float = DEFAULT_MAX_SLOPE_DEG,
    robust_sigma_multiplier: float = DEFAULT_ROBUST_SIGMA_MULTIPLIER,
) -> tuple[StableGroundStats, np.ndarray]:
    """Measure the datum offset and noise floor over unchanged ground."""

    stable = select_stable_mask(
        delta_m,
        valid_mask=valid_mask,
        slope_deg=slope_deg,
        max_slope_deg=max_slope_deg,
        robust_sigma_multiplier=robust_sigma_multiplier,
    )
    stable_count = int(stable.sum())
    total = int(delta_m.size)
    if stable_count == 0:
        return (
            StableGroundStats(offset_m=0.0, sigma_m=0.0, pixel_count=0, pixel_fraction=0.0),
            stable,
        )

    values = delta_m[stable]
    return (
        StableGroundStats(
            offset_m=float(np.median(values)),
            sigma_m=nmad(values),
            pixel_count=stable_count,
            pixel_fraction=float(stable_count) / float(total) if total else 0.0,
        ),
        stable,
    )


def coregister_elevation_pair(
    early_m: np.ndarray,
    late_m: np.ndarray,
    *,
    nodata: float,
    slope_deg: np.ndarray | None = None,
    max_slope_deg: float = DEFAULT_MAX_SLOPE_DEG,
    robust_sigma_multiplier: float = DEFAULT_ROBUST_SIGMA_MULTIPLIER,
    iterations: int = DEFAULT_ITERATIONS,
    min_stable_pixels: int = MIN_STABLE_PIXELS,
) -> CoregistrationResult:
    """Difference two elevation surfaces and remove their vertical datum offset.

    Both surfaces must already sit on the same grid; this function corrects the
    vertical datum only, never horizontal alignment. Callers fetch both epochs
    through the run's locked grid specification, so they are co-located by
    construction.

    The offset estimate is iterated because the stable-ground selection and the
    offset depend on each other: a large initial bias widens the apparent spread,
    which lets genuinely changed ground survive outlier rejection, which then
    biases the offset. Two or three passes settle this.

    Raises ``CoregistrationError`` when too little stable ground remains to
    support an honest datum estimate. Refusing here is deliberate: a silent
    result computed from a handful of pixels would look identical to a good one.
    """

    early = np.asarray(early_m, dtype=np.float64)
    late = np.asarray(late_m, dtype=np.float64)
    if early.shape != late.shape:
        raise CoregistrationError("elevation epochs must share one grid shape")
    if early.ndim != 2:
        raise CoregistrationError("elevation epochs must be 2D rasters")
    if iterations < 1:
        raise CoregistrationError("iterations must be at least 1")

    valid = _finite_mask(early, nodata=nodata) & _finite_mask(late, nodata=nodata)
    if not valid.any():
        raise CoregistrationError("no pixel has valid data in both elevation epochs")

    raw_delta = np.where(valid, late - early, np.nan)

    warnings: list[str] = []
    offset = 0.0
    stats = StableGroundStats(offset_m=0.0, sigma_m=0.0, pixel_count=0, pixel_fraction=0.0)
    stable = np.zeros_like(valid, dtype=bool)
    completed = 0

    for _ in range(int(iterations)):
        working = raw_delta - offset
        stats, stable = estimate_stable_ground(
            working,
            valid_mask=valid,
            slope_deg=slope_deg,
            max_slope_deg=max_slope_deg,
            robust_sigma_multiplier=robust_sigma_multiplier,
        )
        completed += 1
        if stats.pixel_count == 0:
            break
        offset += stats.offset_m
        if abs(stats.offset_m) < 1e-9:
            break

    if stats.pixel_count < int(min_stable_pixels):
        raise CoregistrationError(
            "insufficient stable ground to co-register the elevation pair: "
            f"stable_pixels={stats.pixel_count}, minimum={int(min_stable_pixels)}"
        )

    corrected = np.where(valid, raw_delta - offset, np.nan)

    # Report the total applied offset, not just the final iteration's residual.
    final_stats = StableGroundStats(
        offset_m=offset,
        sigma_m=stats.sigma_m,
        pixel_count=stats.pixel_count,
        pixel_fraction=stats.pixel_fraction,
    )

    if final_stats.sigma_m <= 0.0:
        warnings.append("stable_ground_spread_is_zero")
    if final_stats.pixel_fraction < 0.10:
        warnings.append("stable_ground_fraction_below_10_percent")
    if abs(offset) > 10.0:
        warnings.append("large_vertical_datum_offset_removed")

    return CoregistrationResult(
        delta_m=corrected,
        valid_mask=valid,
        stable_mask=stable,
        stats=final_stats,
        iterations=completed,
        warnings=tuple(warnings),
    )
