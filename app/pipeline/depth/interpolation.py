from __future__ import annotations

import json
from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Iterable

from app.pipeline.depth.package import (
    MANIFEST_NAME,
    _required_text,
    _verify_checksums,
    _warnings,
)
from app.pipeline.depth.schema import (
    DEPTH_STATUS_CALIBRATED_RANGE,
    DEPTH_STATUS_INSUFFICIENT_DATA,
    DEPTH_STATUS_VALIDATED_RANGE,
    CandidateDepthEstimate,
    DepthRange,
)

OPERATOR_PACKAGE_SCHEMA_VERSION = "local_depth_package_v2"
OPERATOR_METHOD_KIND = "operator_scalar_interpolation_v1"
OPERATOR_CANDIDATES_SCHEMA = "local_depth_candidates_v2"


class OperatorDepthPackageError(ValueError):
    """Raised when an operator interpolation package is absent or invalid."""


@dataclass(frozen=True, slots=True)
class OperatorCandidateInput:
    candidate_id: str
    signal_name: str
    signal_value: float
    signal_uncertainty: float = 0.0

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if not self.signal_name.strip():
            raise ValueError("signal_name is required")
        if not isfinite(self.signal_value):
            raise ValueError("signal_value must be finite")
        if not isfinite(self.signal_uncertainty) or self.signal_uncertainty < 0:
            raise ValueError("signal_uncertainty must be finite and nonnegative")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "OperatorCandidateInput":
        try:
            return cls(
                candidate_id=str(payload.get("candidate_id") or "").strip(),
                signal_name=str(payload.get("signal_name") or "").strip(),
                signal_value=float(payload["signal_value"]),
                signal_uncertainty=float(payload.get("signal_uncertainty", 0.0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid operator depth candidate") from exc

    def as_mapping(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "signal_name": self.signal_name,
            "signal_value": self.signal_value,
            "signal_uncertainty": self.signal_uncertainty,
        }


@dataclass(frozen=True, slots=True)
class OperatorDepthAnchor:
    anchor_id: str
    signal_value: float
    depth_range: DepthRange
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperatorInterpolationPackage:
    root: Path
    method_version: str
    calibration_dataset_version: str
    site_id: str
    validation_status: str
    allow_run_quality_warning: bool
    signal_name: str
    signal_units: str
    default_signal_uncertainty: float
    anchors: tuple[OperatorDepthAnchor, ...]
    warnings: tuple[str, ...]

    @property
    def method_kind(self) -> str:
        return OPERATOR_METHOD_KIND

    @property
    def output_status(self) -> str:
        return (
            DEPTH_STATUS_VALIDATED_RANGE
            if self.validation_status == "validated"
            else DEPTH_STATUS_CALIBRATED_RANGE
        )

    @property
    def depth_quality(self) -> str:
        return "validated_local" if self.validation_status == "validated" else "provisional_local"

    @property
    def minimum_signal(self) -> float:
        return self.anchors[0].signal_value

    @property
    def maximum_signal(self) -> float:
        return self.anchors[-1].signal_value

    def public_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": OPERATOR_PACKAGE_SCHEMA_VERSION,
            "method_kind": OPERATOR_METHOD_KIND,
            "method_version": self.method_version,
            "calibration_dataset_version": self.calibration_dataset_version,
            "site_id": self.site_id,
            "validation_status": self.validation_status,
            "signal_name": self.signal_name,
            "signal_units": self.signal_units,
            "anchor_count": len(self.anchors),
            "allow_run_quality_warning": self.allow_run_quality_warning,
            "warnings": list(self.warnings),
        }

    def _interpolate_at(
        self, value: float
    ) -> tuple[DepthRange, str, tuple[str, ...]]:
        signals = [anchor.signal_value for anchor in self.anchors]
        tolerance = 1e-12
        for anchor in self.anchors:
            if abs(value - anchor.signal_value) <= tolerance:
                return (
                    anchor.depth_range,
                    f"anchor:{anchor.anchor_id}",
                    anchor.warnings,
                )

        right_index = bisect_right(signals, value)
        if right_index <= 0 or right_index >= len(self.anchors):
            raise ValueError("signal value is outside interpolation support")
        left = self.anchors[right_index - 1]
        right = self.anchors[right_index]
        weight = (value - left.signal_value) / (right.signal_value - left.signal_value)

        def blend(left_value: float, right_value: float) -> float:
            return left_value + weight * (right_value - left_value)

        depth_range = DepthRange(
            minimum_m=blend(left.depth_range.minimum_m, right.depth_range.minimum_m),
            best_m=blend(left.depth_range.best_m, right.depth_range.best_m),
            maximum_m=blend(left.depth_range.maximum_m, right.depth_range.maximum_m),
        )
        warnings = tuple(dict.fromkeys((*left.warnings, *right.warnings)))
        return depth_range, f"interval:{left.anchor_id}:{right.anchor_id}", warnings

    def estimate(
        self,
        candidate: OperatorCandidateInput,
        *,
        extra_warnings: Iterable[str] = (),
    ) -> CandidateDepthEstimate:
        if candidate.signal_name != self.signal_name:
            return CandidateDepthEstimate.unavailable(
                candidate_id=candidate.candidate_id,
                status=DEPTH_STATUS_INSUFFICIENT_DATA,
                warnings=["candidate_signal_name_mismatch"],
            )

        uncertainty = max(candidate.signal_uncertainty, self.default_signal_uncertainty)
        lower_signal = candidate.signal_value - uncertainty
        upper_signal = candidate.signal_value + uncertainty
        tolerance = 1e-12
        if (
            lower_signal < self.minimum_signal - tolerance
            or upper_signal > self.maximum_signal + tolerance
        ):
            return CandidateDepthEstimate.unavailable(
                candidate_id=candidate.candidate_id,
                status=DEPTH_STATUS_INSUFFICIENT_DATA,
                warnings=["candidate_outside_local_calibration_signal_support"],
            )

        sample_signals = {lower_signal, candidate.signal_value, upper_signal}
        sample_signals.update(
            anchor.signal_value
            for anchor in self.anchors
            if lower_signal <= anchor.signal_value <= upper_signal
        )

        evaluated = [self._interpolate_at(value) for value in sorted(sample_signals)]
        centre_range, support_id, centre_warnings = self._interpolate_at(candidate.signal_value)
        minimum_m = min(item[0].minimum_m for item in evaluated)
        maximum_m = max(item[0].maximum_m for item in evaluated)
        final_range = DepthRange(
            minimum_m=min(minimum_m, centre_range.best_m),
            best_m=centre_range.best_m,
            maximum_m=max(maximum_m, centre_range.best_m),
        )

        warnings = [
            "operator_calibrated_local_interpolation",
            "local_calibration_only",
            "not_transferable",
            "not_global_model",
            "no_extrapolation",
            *self.warnings,
            *centre_warnings,
            *extra_warnings,
        ]
        if uncertainty > 0:
            warnings.append("signal_uncertainty_applied")

        return CandidateDepthEstimate.ranged(
            candidate_id=candidate.candidate_id,
            status=self.output_status,
            depth_range=final_range,
            depth_quality=self.depth_quality,
            zone_id=support_id,
            warnings=warnings,
        )


def _required_float(payload: dict[str, Any], key: str) -> float:
    try:
        value = float(payload[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise OperatorDepthPackageError(f"invalid package field: {key}") from exc
    if not isfinite(value):
        raise OperatorDepthPackageError(f"package field must be finite: {key}")
    return value


def _validate_monotonic_depths(anchors: tuple[OperatorDepthAnchor, ...]) -> None:
    differences = [
        right.depth_range.best_m - left.depth_range.best_m
        for left, right in zip(anchors, anchors[1:])
    ]
    if any(abs(value) <= 1e-12 for value in differences):
        raise OperatorDepthPackageError("anchor best depths must be strictly monotonic")
    direction = 1 if differences[0] > 0 else -1
    if any((value > 0) != (direction > 0) for value in differences):
        raise OperatorDepthPackageError("anchor best depths must be monotonic with signal")


def load_operator_interpolation_package(root: Path) -> OperatorInterpolationPackage:
    root = Path(root)
    if not root.is_dir():
        raise OperatorDepthPackageError("operator depth package directory does not exist")

    try:
        _verify_checksums(root)
    except ValueError as exc:
        raise OperatorDepthPackageError(str(exc)) from exc

    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise OperatorDepthPackageError(f"missing {MANIFEST_NAME}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatorDepthPackageError("unreadable operator depth manifest") from exc
    if not isinstance(payload, dict):
        raise OperatorDepthPackageError("operator depth manifest must be a JSON object")
    if payload.get("schema_version") != OPERATOR_PACKAGE_SCHEMA_VERSION:
        raise OperatorDepthPackageError("unsupported operator depth package schema")
    if payload.get("method_kind") != OPERATOR_METHOD_KIND:
        raise OperatorDepthPackageError("unsupported operator depth method kind")

    validation_status = _required_text(payload, "validation_status")
    if validation_status not in {"provisional", "validated"}:
        raise OperatorDepthPackageError("validation_status must be provisional or validated")

    default_uncertainty = float(payload.get("default_signal_uncertainty", 0.0))
    if not isfinite(default_uncertainty) or default_uncertainty < 0:
        raise OperatorDepthPackageError(
            "default_signal_uncertainty must be finite and nonnegative"
        )

    raw_anchors = payload.get("anchors")
    if not isinstance(raw_anchors, list) or len(raw_anchors) < 2:
        raise OperatorDepthPackageError("operator package must contain at least two anchors")

    anchors: list[OperatorDepthAnchor] = []
    seen_anchor_ids: set[str] = set()
    seen_signals: set[float] = set()
    for raw_anchor in raw_anchors:
        if not isinstance(raw_anchor, dict):
            raise OperatorDepthPackageError("anchor entry must be a JSON object")
        anchor_id = _required_text(raw_anchor, "anchor_id")
        if anchor_id in seen_anchor_ids:
            raise OperatorDepthPackageError(f"duplicate anchor_id: {anchor_id}")
        seen_anchor_ids.add(anchor_id)
        signal_value = _required_float(raw_anchor, "signal_value")
        if signal_value in seen_signals:
            raise OperatorDepthPackageError("anchor signal values must be unique")
        seen_signals.add(signal_value)
        try:
            depth_range = DepthRange.from_mapping(raw_anchor)
        except ValueError as exc:
            raise OperatorDepthPackageError(f"invalid range for anchor {anchor_id}") from exc
        anchors.append(
            OperatorDepthAnchor(
                anchor_id=anchor_id,
                signal_value=signal_value,
                depth_range=depth_range,
                warnings=_warnings(raw_anchor.get("warnings")),
            )
        )

    sorted_anchors = tuple(sorted(anchors, key=lambda item: item.signal_value))
    _validate_monotonic_depths(sorted_anchors)

    return OperatorInterpolationPackage(
        root=root.resolve(),
        method_version=_required_text(payload, "method_version"),
        calibration_dataset_version=_required_text(payload, "calibration_dataset_version"),
        site_id=_required_text(payload, "site_id"),
        validation_status=validation_status,
        allow_run_quality_warning=bool(payload.get("allow_run_quality_warning", False)),
        signal_name=_required_text(payload, "signal_name"),
        signal_units=_required_text(payload, "signal_units"),
        default_signal_uncertainty=default_uncertainty,
        anchors=sorted_anchors,
        warnings=_warnings(payload.get("warnings")),
    )
