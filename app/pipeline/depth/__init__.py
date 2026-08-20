"""Private local depth package helpers.

This package keeps reviewed recorded measurements separate from calibrated or
interpolated estimates. It is not a global depth model and does not make depth
available by default.
"""

from app.pipeline.depth.package import LocalDepthPackage, LocalDepthPackageError, load_local_depth_package
from app.pipeline.depth.recorded import (
    RecordedDepthPackage,
    RecordedDepthPackageError,
    load_recorded_depth_package,
)
from app.pipeline.depth.schema import (
    CandidateDepthEstimate,
    CandidateDepthInput,
    DepthRange,
    RecordedDepthMeasurement,
)

__all__ = [
    "CandidateDepthEstimate",
    "CandidateDepthInput",
    "DepthRange",
    "LocalDepthPackage",
    "LocalDepthPackageError",
    "RecordedDepthMeasurement",
    "RecordedDepthPackage",
    "RecordedDepthPackageError",
    "load_local_depth_package",
    "load_recorded_depth_package",
]
