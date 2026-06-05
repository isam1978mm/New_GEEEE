from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import Settings
from app.pipeline.roi_preview import GridPreview, RoiWindowPreview, SelectedPointPreview, build_roi_grid_preview

MAX_ACQUISITION_WINDOW_DAYS = 366

SarOrbit = Literal["any", "ascending", "descending"]
SarPolarization = Literal["VV", "VH", "VV_VH"]
ExecutionStatus = Literal[
    "dry_run",
    "auth_not_configured",
    "ready_for_real_execution",
    "real_execution_disabled",
]


class EarthEnginePlanRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    acquisition_start: date
    acquisition_end: date
    cloud_percent_max: float | None = Field(default=None, ge=0.0, le=100.0)
    sar_orbit: SarOrbit = "any"
    sar_polarization: SarPolarization = "VV_VH"
    dry_run: bool = True

    @model_validator(mode="after")
    def validate_acquisition_window(self) -> EarthEnginePlanRequest:
        if self.acquisition_end < self.acquisition_start:
            raise ValueError("Acquisition end date must not precede start date.")
        if (self.acquisition_end - self.acquisition_start).days > MAX_ACQUISITION_WINDOW_DAYS:
            raise ValueError("Acquisition window exceeds the allowed range.")
        return self

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_numeric(cls, value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("Coordinate values must be numeric.")
        return float(value)


class EarthEngineAuthReadiness(BaseModel):
    status: ExecutionStatus
    backend_auth_configured: bool
    key_file_present: bool
    real_execution_enabled: bool


class EarthEnginePlan(BaseModel):
    plan_id: str
    mode: str = "controlled_earth_engine_planning"
    dry_run: bool
    execution_status: ExecutionStatus
    selected_point_preview: SelectedPointPreview
    roi_window_preview: RoiWindowPreview
    grid_preview: GridPreview
    auth_readiness: EarthEngineAuthReadiness
    acquisition_window: dict[str, str]
    planned_provider_families: list[str]
    planned_query_filters: dict[str, str | float | None]
    warnings: list[str]


def build_earth_engine_plan(request: EarthEnginePlanRequest, *, settings: Settings) -> EarthEnginePlan:
    preview = build_roi_grid_preview(latitude=request.latitude, longitude=request.longitude)
    auth_readiness = evaluate_earth_engine_auth_readiness(settings=settings, dry_run=request.dry_run)
    execution_status = _execution_status(request=request, auth_readiness=auth_readiness)
    warnings = [
        "Controlled Earth Engine planning only; no Earth Engine request, run start, raster writer, or file write occurs.",
    ]
    if execution_status == "auth_not_configured":
        warnings.append("Backend auth is not configured for real execution.")
    elif execution_status == "real_execution_disabled":
        warnings.append("Backend auth is present, but real execution is disabled by configuration.")

    return EarthEnginePlan(
        plan_id=f"ee-plan-{uuid4()}",
        dry_run=request.dry_run,
        execution_status=execution_status,
        selected_point_preview=preview.selected_point_preview,
        roi_window_preview=preview.roi_window_preview,
        grid_preview=preview.grid_preview,
        auth_readiness=auth_readiness,
        acquisition_window={
            "start": request.acquisition_start.isoformat(),
            "end": request.acquisition_end.isoformat(),
        },
        planned_provider_families=[
            "Sentinel-2 optical planning",
            "Sentinel-1 SAR planning",
            "Landsat thermal planning",
            "DEM planning",
        ],
        planned_query_filters={
            "cloud_percent_max": request.cloud_percent_max,
            "sar_orbit": request.sar_orbit,
            "sar_polarization": request.sar_polarization,
        },
        warnings=warnings,
    )


def evaluate_earth_engine_auth_readiness(*, settings: Settings, dry_run: bool) -> EarthEngineAuthReadiness:
    backend_auth_configured = bool(settings.ee_service_account_email)
    key_file_present = bool(settings.ee_service_account_key_path and settings.ee_service_account_key_path.is_file())
    real_execution_enabled = bool(settings.ee_real_execution_enabled)
    if not backend_auth_configured or not key_file_present:
        status: ExecutionStatus = "auth_not_configured"
    else:
        status = "ready_for_real_execution"

    return EarthEngineAuthReadiness(
        status=status,
        backend_auth_configured=backend_auth_configured,
        key_file_present=key_file_present,
        real_execution_enabled=real_execution_enabled,
    )


def import_earth_engine():
    import importlib

    return importlib.import_module("ee")


def _execution_status(
    *,
    request: EarthEnginePlanRequest,
    auth_readiness: EarthEngineAuthReadiness,
) -> ExecutionStatus:
    if auth_readiness.status == "auth_not_configured":
        return "auth_not_configured"
    if request.dry_run:
        return "dry_run"
    if not auth_readiness.real_execution_enabled:
        return "real_execution_disabled"
    return auth_readiness.status
