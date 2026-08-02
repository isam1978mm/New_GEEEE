"""Turn a co-registered elevation difference into measured thickness per area.

The elevation difference raster already holds the measurement. What this module
adds is the part that decides whether a given patch of ground has changed by
more than the pair's own noise, and how wide the honest interval around that
number is.

The uncertainty model matters more than the mean. Elevation error is spatially
correlated: neighbouring pixels of a DEM are wrong in the same direction, so
averaging a thousand of them does not reduce the error by a factor of thirty.
Treating the pixels as independent would produce intervals far too narrow and
would let the app claim centimetre precision it does not have.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from app.pipeline.depth.schema import DepthRange

# Elevation errors stay correlated over distances of a few hundred metres in
# spaceborne DEMs and a few tens of metres in airborne lidar. The default is
# deliberately pessimistic; a caller with a characterised source may lower it.
DEFAULT_CORRELATION_LENGTH_M = 200.0

# Multiple of the pair noise floor a change must exceed before it is reported as
# real. 1.96 corresponds to roughly 95% confidence for normally distributed
# error, which is the usual level of detection in change-mapping work.
DEFAULT_DETECTION_SIGMA = 1.96

# Half-width of the reported interval, in standard deviations.
DEFAULT_INTERVAL_SIGMA = 2.0

MIN_MEASURABLE_PIXELS = 20


class ThicknessError(ValueError):
    """Raised when a thickness measurement cannot be formed honestly."""


@dataclass(frozen=True, slots=True)
class PolygonThickness:
    """The measured vertical change over one area of ground."""

    zone_id: str
    mean_change_m: float
    sigma_m: float
    pixel_count: int
    area_m2: float
    is_significant: bool
    is_accumulation: bool
    warnings: tuple[str, ...]

    @property
    def measurable(self) -> bool:
        """True when this area carries a reportable placed-material thickness."""

        return self.is_significant and self.is_accumulation

    def depth_range(self, *, interval_sigma: float = DEFAULT_INTERVAL_SIGMA) -> DepthRange | None:
        """Return the measured thickness as a depth range, or None to abstain.

        Abstention is returned rather than a zero-width or negative range so the
        caller cannot accidentally publish a number for ground that either did
        not change or lost material.
        """

        if not self.measurable:
            return None
        half_width = float(interval_sigma) * self.sigma_m
        best = float(self.mean_change_m)
        return DepthRange(
            minimum_m=max(0.0, best - half_width),
            best_m=best,
            maximum_m=best + half_width,
        )

    def as_mapping(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "mean_change_m": round(float(self.mean_change_m), 6),
            "sigma_m": round(float(self.sigma_m), 6),
            "pixel_count": int(self.pixel_count),
            "area_m2": round(float(self.area_m2), 3),
            "is_significant": bool(self.is_significant),
            "is_accumulation": bool(self.is_accumulation),
            "measurable": bool(self.measurable),
            "warnings": list(self.warnings),
        }


def correlated_mean_uncertainty(
    *,
    sigma_stable_m: float,
    area_m2: float,
    correlation_length_m: float = DEFAULT_CORRELATION_LENGTH_M,
) -> float:
    """Uncertainty of an area-averaged elevation change, allowing for correlation.

    Follows the standard spatially-correlated treatment for glacier and
    earthwork volume change (Rolstad et al. 2009): once the averaging area grows
    past one correlation area, the error falls off with the square root of the
    ratio of correlation area to averaging area rather than with pixel count.

    Below one correlation area every pixel is effectively the same measurement
    repeated, so no averaging benefit is available at all and the full noise
    floor is returned.
    """

    sigma = float(sigma_stable_m)
    if sigma < 0:
        raise ThicknessError("sigma_stable_m must be nonnegative")
    if area_m2 <= 0:
        raise ThicknessError("area_m2 must be positive")
    if correlation_length_m <= 0:
        raise ThicknessError("correlation_length_m must be positive")

    correlation_area = float(correlation_length_m) ** 2
    if area_m2 <= correlation_area:
        return sigma

    reduction = sqrt((2.0 * correlation_area) / (5.0 * float(area_m2)))
    # The reduction factor is only meaningful as a reduction. Guard against a
    # configuration that would otherwise inflate the noise floor.
    return sigma * min(1.0, reduction)


def measure_polygon_thickness(
    delta_m: np.ndarray,
    mask: np.ndarray,
    *,
    zone_id: str,
    sigma_stable_m: float,
    pixel_area_m2: float,
    correlation_length_m: float = DEFAULT_CORRELATION_LENGTH_M,
    detection_sigma: float = DEFAULT_DETECTION_SIGMA,
    min_pixels: int = MIN_MEASURABLE_PIXELS,
) -> PolygonThickness:
    """Measure the mean elevation change inside ``mask``.

    ``delta_m`` is the co-registered difference raster and may contain NaN for
    pixels that were invalid in either epoch; those are excluded here rather than
    silently averaged in.
    """

    if delta_m.shape != mask.shape:
        raise ThicknessError("delta raster and mask must share one shape")
    if pixel_area_m2 <= 0:
        raise ThicknessError("pixel_area_m2 must be positive")
    if not str(zone_id).strip():
        raise ThicknessError("zone_id is required")

    selected = np.asarray(mask, dtype=bool) & np.isfinite(delta_m)
    pixel_count = int(selected.sum())
    area_m2 = float(pixel_count) * float(pixel_area_m2)

    warnings: list[str] = []
    if pixel_count < int(min_pixels):
        return PolygonThickness(
            zone_id=str(zone_id).strip(),
            mean_change_m=0.0,
            sigma_m=float(sigma_stable_m),
            pixel_count=pixel_count,
            area_m2=area_m2,
            is_significant=False,
            is_accumulation=False,
            warnings=("insufficient_valid_pixels",),
        )

    values = delta_m[selected]
    mean_change = float(np.mean(values))

    area_sigma = correlated_mean_uncertainty(
        sigma_stable_m=sigma_stable_m,
        area_m2=area_m2,
        correlation_length_m=correlation_length_m,
    )
    # Local roughness inside the polygon is a second, independent contribution:
    # a patch whose own pixels disagree wildly is less trustworthy than a smooth
    # one even when the pair as a whole is quiet.
    within_sigma = float(np.std(values)) / sqrt(float(pixel_count))
    sigma = float(sqrt(area_sigma**2 + within_sigma**2))

    is_significant = abs(mean_change) > float(detection_sigma) * sigma
    is_accumulation = mean_change > 0.0

    if not is_significant:
        warnings.append("change_within_noise_floor")
    if is_significant and not is_accumulation:
        warnings.append("material_removed_not_added")

    return PolygonThickness(
        zone_id=str(zone_id).strip(),
        mean_change_m=mean_change,
        sigma_m=sigma,
        pixel_count=pixel_count,
        area_m2=area_m2,
        is_significant=is_significant,
        is_accumulation=is_accumulation,
        warnings=tuple(warnings),
    )


def significant_change_mask(
    delta_m: np.ndarray,
    *,
    sigma_stable_m: float,
    detection_sigma: float = DEFAULT_DETECTION_SIGMA,
) -> np.ndarray:
    """Pixels whose change exceeds the per-pixel noise floor of the pair.

    This is the per-pixel counterpart of the polygon test and is what makes the
    measurement able to draw its own boundaries: the ground that rose is exactly
    the ground that was covered, so no surveyed outline is required.
    """

    if sigma_stable_m < 0:
        raise ThicknessError("sigma_stable_m must be nonnegative")
    threshold = float(detection_sigma) * float(sigma_stable_m)
    return np.isfinite(delta_m) & (np.abs(delta_m) > threshold)
