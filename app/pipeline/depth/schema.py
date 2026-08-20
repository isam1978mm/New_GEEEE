from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

DEPTH_STATUS_NOT_AVAILABLE = "not_available"
DEPTH_STATUS_INSUFFICIENT_DATA = "insufficient_data"
DEPTH_STATUS_RECORDED_MEASUREMENT = "recorded_measurement"
DEPTH_STATUS_CALIBRATED_RANGE = "calibrated_range"
DEPTH_STATUS_VALIDATED_RANGE = "validated_range"

ALLOWED_DEPTH_STATUSES = {
    DEPTH_STATUS_NOT_AVAILABLE,
    DEPTH_STATUS_INSUFFICIENT_DATA,
    DEPTH_STATUS_RECORDED_MEASUREMENT,
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
class RecordedDepthMeasurement:
    mean_m: float
    ci95_low_m: float
    ci95_high_m: float
    sample_min_m: float
    sample_max_m: float
    sample_count: int
    measurement_source: str
    measurement_method: str
    measurement_timing: str
    reported_design_depth_m: float | None = None
    measurement_date: str = ""

    def __post_init__(self) -> None:
        values = (
            self.mean_m,
            self.ci95_low_m,
            self.ci95_high_m,
            self.sample_min_m,
            self.sample_max_m,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("recorded depth values must be finite")
        if min(values) < 0:
            raise ValueError("recorded depth values must be nonnegative")
        if not self.ci95_low_m <= self.mean_m <= self.ci95_high_m:
            raise ValueError("recorded 95% interval must contain the mean")
        if not self.sample_min_m <= self.mean_m <= self.sample_max_m:
            raise ValueError("recorded sample range must contain the mean")
        if self.sample_count <= 0:
            raise ValueError("recorded sample_count must be positive")
        if self.reported_design_depth_m is not None:
            if not isfinite(self.reported_design_depth_m) or self.reported_design_depth_m < 0:
                raise ValueError("reported design depth must be finite and nonnegative")
        _require_nonempty(self.measurement_source, "measurement_source")
        _require_nonempty(self.measurement_method, "measurement_method")
        _require_nonempty(self.measurement_timing, "measurement_timing")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "RecordedDepthMeasurement":
        try:
            raw_design = payload.get("reported_design_depth_m")
            return cls(
                mean_m=float(payload["measurement_mean_m"]),
                ci95_low_m=float(payload["measurement_ci95_low_m"]),
                ci95_high_m=float(payload["measurement_ci95_high_m"]),
                sample_min_m=float(payload["sample_min_m"]),
                sample_max_m=float(payload["sample_max_m"]),
                sample_count=int(payload["sample_count"]),
                reported_design_depth_m=(
                    None if raw_design in {None, ""} else float(raw_design)
                ),
                measurement_source=_require_nonempty(
                    payload.get("measurement_source"), "measurement_source"
                ),
                measurement_date=str(payload.get("measurement_date") or "").strip(),
                measurement_method=_require_nonempty(
                    payload.get("measurement_method"), "measurement_method"
                ),
                measurement_timing=_require_nonempty(
                    payload.get("measurement_timing"), "measurement_timing"
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid recorded depth measurement") from exc

    def as_csv_fields(self) -> dict[str, str]:
        return {
            "recorded_depth_mean_m": f"{self.mean_m:.6f}",
            "recorded_depth_ci95_low_m": f"{self.ci95_low_m:.6f}",
            "recorded_depth_ci95_high_m": f"{self.ci95_high_m:.6f}",
            "recorded_sample_min_m": f"{self.sample_min_m:.6f}",
            "recorded_sample_max_m": f"{self.sample_max_m:.6f}",
            "recorded_sample_count": str(self.sample_count),
            "reported_design_depth_m": (
                ""
                if self.reported_design_depth_m is None
                else f"{self.reported_design_depth_m:.6f}"
            ),
            "measurement_source": self.measurement_source,
            "measurement_date": self.measurement_date,
            "measurement_method": self.measurement_method,
            "measurement_timing": self.measurement_timing,
        }


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
    recorded_measurement: RecordedDepthMeasurement | None = None
    depth_quality: str = ""
    zone_id: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_nonempty(self.candidate_id, "candidate_id")
        if self.depth_status not in ALLOWED_DEPTH_STATUSES:
            raise ValueError(f"unsupported depth status: {self.depth_status}")
        has_range = self.depth_range is not None
        has_recorded = self.recorded_measurement is not None
        requires_range = self.depth_status in {
            DEPTH_STATUS_CALIBRATED_RANGE,
            DEPTH_STATUS_VALIDATED_RANGE,
        }
        requires_recorded = self.depth_status == DEPTH_STATUS_RECORDED_MEASUREMENT
        if requires_range != has_range:
            raise ValueError("metre estimates are allowed only for calibrated or validated ranges")
        if requires_recorded != has_recorded:
            raise ValueError("recorded metre values require recorded_measurement status")
        if has_range and has_recorded:
            raise ValueError("recorded measurements and estimated ranges must remain separate")

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
    def recorded(
        cls,
        *,
        candidate_id: str,
        measurement: RecordedDepthMeasurement,
        zone_id: str,
        warnings: Any = None,
    ) -> "CandidateDepthEstimate":
        return cls(
            candidate_id=candidate_id,
            depth_status=DEPTH_STATUS_RECORDED_MEASUREMENT,
            recorded_measurement=measurement,
            depth_quality="recorded_reviewed",
            zone_id=_require_nonempty(zone_id, "zone_id"),
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
        row = {
            "candidate_id": self.candidate_id,
            "depth_status": self.depth_status,
            "estimated_depth_min_m": "" if depth_range is None else f"{depth_range.minimum_m:.6f}",
            "estimated_depth_best_m": "" if depth_range is None else f"{depth_range.best_m:.6f}",
            "estimated_depth_max_m": "" if depth_range is None else f"{depth_range.maximum_m:.6f}",
            "recorded_depth_mean_m": "",
            "recorded_depth_ci95_low_m": "",
            "recorded_depth_ci95_high_m": "",
            "recorded_sample_min_m": "",
            "recorded_sample_max_m": "",
            "recorded_sample_count": "",
            "reported_design_depth_m": "",
            "measurement_source": "",
            "measurement_date": "",
            "measurement_method": "",
            "measurement_timing": "",
            "depth_quality": self.depth_quality,
            "zone_id": self.zone_id,
            "warnings": "|".join(self.warnings),
        }
        if self.recorded_measurement is not None:
            row.update(self.recorded_measurement.as_csv_fields())
        return row
