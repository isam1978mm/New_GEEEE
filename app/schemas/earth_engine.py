from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.services.earth_engine_control import (
    MAX_ACQUISITION_WINDOW_DAYS,
    EarthEnginePlan,
    EarthEnginePlanRequest,
    SarOrbit,
    SarPolarization,
)


class EarthEnginePlanPublicRequest(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    acquisition_start: date
    acquisition_end: date
    cloud_percent_max: float | None = Field(default=None, ge=0.0, le=100.0)
    sar_orbit: SarOrbit = "any"
    sar_polarization: SarPolarization = "VV_VH"
    dry_run: bool = True

    @model_validator(mode="after")
    def validate_acquisition_window(self) -> EarthEnginePlanPublicRequest:
        if self.acquisition_end < self.acquisition_start:
            raise ValueError("Acquisition end date must not precede start date.")
        if (self.acquisition_end - self.acquisition_start).days > MAX_ACQUISITION_WINDOW_DAYS:
            raise ValueError("Acquisition window exceeds the allowed range.")
        return self

    def to_service_request(self) -> EarthEnginePlanRequest:
        return EarthEnginePlanRequest(
            latitude=self.lat,
            longitude=self.lon,
            acquisition_start=self.acquisition_start,
            acquisition_end=self.acquisition_end,
            cloud_percent_max=self.cloud_percent_max,
            sar_orbit=self.sar_orbit,
            sar_polarization=self.sar_polarization,
            dry_run=self.dry_run,
        )


EarthEnginePlanPublic = EarthEnginePlan
