"""Measured elevation change between two public elevation epochs.

This package measures how much material was added to or removed from the ground
by differencing two independently acquired public elevation surfaces over the
same locked run grid.

The measured quantity is a vertical elevation difference in metres. It is a
direct measurement, not a model output and not a radar-derived proxy. It carries
no fitted parameters, so it never needs calibration records to produce a number.

Scope limits, enforced by the code rather than by documentation:

- it measures placed or removed material thickness, not depth to a buried object;
- it can only measure change that happened between the two acquisition epochs;
- it abstains when the measured change cannot be separated from the noise of the
  two source surfaces.
"""

from app.pipeline.elevation_change.coregistration import (
    CoregistrationError,
    CoregistrationResult,
    StableGroundStats,
    coregister_elevation_pair,
    estimate_stable_ground,
    nmad,
    select_stable_mask,
)

__all__ = [
    "CoregistrationError",
    "CoregistrationResult",
    "StableGroundStats",
    "coregister_elevation_pair",
    "estimate_stable_ground",
    "nmad",
    "select_stable_mask",
]
