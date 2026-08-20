from __future__ import annotations

import json
from pathlib import Path
from typing import TypeAlias

from app.pipeline.depth.interpolation import (
    OPERATOR_METHOD_KIND,
    OPERATOR_PACKAGE_SCHEMA_VERSION,
    OperatorDepthPackageError,
    OperatorInterpolationPackage,
    load_operator_interpolation_package,
)
from app.pipeline.depth.package import (
    MANIFEST_NAME,
    PACKAGE_METHOD_KIND,
    PACKAGE_SCHEMA_VERSION,
    LocalDepthPackage,
    LocalDepthPackageError,
    load_local_depth_package,
)
from app.pipeline.depth.recorded import (
    RECORDED_METHOD_KIND,
    RECORDED_PACKAGE_SCHEMA_VERSION,
    RecordedDepthPackage,
    RecordedDepthPackageError,
    load_recorded_depth_package,
)

DepthPackage: TypeAlias = LocalDepthPackage | OperatorInterpolationPackage | RecordedDepthPackage


class DepthPackageError(ValueError):
    """Raised when a private depth package cannot be loaded safely."""


def load_depth_package(root: Path) -> DepthPackage:
    root = Path(root)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise DepthPackageError(f"missing {MANIFEST_NAME}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthPackageError("unreadable depth manifest") from exc
    if not isinstance(payload, dict):
        raise DepthPackageError("depth manifest must be a JSON object")

    schema_version = payload.get("schema_version")
    method_kind = payload.get("method_kind")
    try:
        if (
            schema_version == PACKAGE_SCHEMA_VERSION
            and method_kind == PACKAGE_METHOD_KIND
        ):
            return load_local_depth_package(root)
        if (
            schema_version == OPERATOR_PACKAGE_SCHEMA_VERSION
            and method_kind == OPERATOR_METHOD_KIND
        ):
            return load_operator_interpolation_package(root)
        if (
            schema_version == RECORDED_PACKAGE_SCHEMA_VERSION
            and method_kind == RECORDED_METHOD_KIND
        ):
            return load_recorded_depth_package(root)
    except (
        LocalDepthPackageError,
        OperatorDepthPackageError,
        RecordedDepthPackageError,
    ) as exc:
        raise DepthPackageError(str(exc)) from exc

    raise DepthPackageError("unsupported depth package schema or method kind")
