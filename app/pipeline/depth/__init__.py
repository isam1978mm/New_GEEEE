"""Private local depth package helpers.

This package supports only explicitly configured local calibration zones. It is
not a global depth model and does not make depth available by default.
"""

from app.pipeline.depth.package import LocalDepthPackage, LocalDepthPackageError, load_local_depth_package
from app.pipeline.depth.schema import CandidateDepthEstimate, CandidateDepthInput, DepthRange

__all__ = [
    "CandidateDepthEstimate",
    "CandidateDepthInput",
    "DepthRange",
    "LocalDepthPackage",
    "LocalDepthPackageError",
    "load_local_depth_package",
]
