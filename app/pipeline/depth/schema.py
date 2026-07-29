from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

DEPTH_STATUS_NOT_AVAILABLE = "not_available"
DEPTH_STATUS_INSUFFICIENT_DATA = "insufficient_data"
DEPTH_STATUS_CALIBRATED_RANGE = "calibrated_range"
DEPTH_STATUS_VALIDATED_RANGE = "validated_range"

ALLOWED_DEPTH_STATUSES = {
    DEPTH_STATUS_NOT_AVAILABLE,
    DEPTH_STATUS_INSUFFICIENT_DATA,
    DEPTH_STATUS_CALIBRATED_RANGE,
    DEPTH_STATUS_VALIDATED_RANGE,
}


def _require_nonempty(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _normalise_warnings(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, list | tuple):
        raise ValueError("warnings must be a list")
    warnings: list[str] = []
    for value in values:
        warning = str(value or "").strip()
        if warning and warning not in warnings:
            warnings.append(warning)
    return tuple(warnings)


@dataclass(frozen=True, slots=True)
class DepthRange:
    minimum_m: float
    best_m: float
    maximum_m: float

    def __post_init__(self) -> None:
        values = (self.minimum_m, self.best_m, self.maximum_m)
        if not all(isfinite(value) for value in values):
            raise ValueError("depth values must be finite")
        if self.minimum_m < 0:
            raise ValueError("depth values must be nonnegative")
        if not self.minimum_m <= self.best_m <= self.maximum_m:
            raise ValueError("depth range must satisfy minimum <= best <= maximum")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "DepthRange":
        try:
            return cls(
                minimum_m=float(payload["depth_min_m"]),
                best_m=float(payload["depth_best_m"]),
                maximum_m=float(payload["depth_max_m"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid depth range") from exc


@dataclass(frozen=True, slots=True)
class CandidateDepthInput:
    candidate_id: str
    zone_id: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "CandidateDepthInput":
        return cls(
            candidate_id=_require_nonempty(payload.get("candidate_id"), "candidate_id"),
            zone_id=_require_nonempty(payload.get("zone_id"), "zone_id"),
        )


@dataclass(frozen=True, slots=True)
class CandidateDepthEstimate:
    candidate_id: str
    depth_status: str
    depth_range: DepthRange | None = None
    depth_quality: str = ""
    zone_id: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_nonempty(self.candidate_id, "candidate_id")
        if self.depth_status not in ALLOWED_DEPTH_STATUSES:
            raise ValueError(f"unsupported depth status: {self.depth_status}")
        has_range = self.depth_range is not None
        requires_range = self.depth_status in {
            DEPTH_STATUS_CALIBRATED_RANGE,
            DEPTH_STATUS_VALIDATED_RANGE,
        }
        if requires_range != has_range:
            raise ValueError("metre values are allowed only for calibrated or validated ranges")

    @classmethod
    def unavailable(
        cls,
        *,
        candidate_id: str,
        status: str,
        zone_id: str = "",
        warnings: Any = None,
    ) -> "CandidateDepthEstimate":
        if status not in {DEPTH_STATUS_NOT_AVAILABLE, DEPTH_STATUS_INSUFFICIENT_DATA}:
            raise ValueError("unavailable estimate requires a non-metre status")
        return cls(
            candidate_id=candidate_id,
            depth_status=status,
            zone_id=zone_id,
            warnings=_normalise_warnings(warnings),
        )

    @classmethod
    def ranged(
        cls,
        *,
        candidate_id: str,
        status: str,
        depth_range: DepthRange,
        depth_quality: str,
        zone_id: str,
        warnings: Any = None,
    ) -> "CandidateDepthEstimate":
        return cls(
            candidate_id=candidate_id,
            depth_status=status,
            depth_range=depth_range,
            depth_quality=_require_nonempty(depth_quality, "depth_quality"),
            zone_id=_require_nonempty(zone_id, "zone_id"),
            warnings=_normalise_warnings(warnings),
        )

    def as_csv_row(self) -> dict[str, str]:
        depth_range = self.depth_range
        return {
            "candidate_id": self.candidate_id,
            "depth_status": self.depth_status,
            "estimated_depth_min_m": "" if depth_range is None else f"{depth_range.minimum_m:.6f}",
            "estimated_depth_best_m": "" if depth_range is None else f"{depth_range.best_m:.6f}",
            "estimated_depth_max_m": "" if depth_range is None else f"{depth_range.maximum_m:.6f}",
            "depth_quality": self.depth_quality,
            "zone_id": self.zone_id,
            "warnings": "|".join(self.warnings),
        }
