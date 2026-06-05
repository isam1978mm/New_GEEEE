from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings
from app.deps import get_settings_from_request
from app.schemas.earth_engine import EarthEnginePlanPublic, EarthEnginePlanPublicRequest
from app.services.earth_engine_control import build_earth_engine_plan

router = APIRouter(prefix="/earth-engine", tags=["earth-engine"])


@router.post("/plan", response_model=EarthEnginePlanPublic)
async def plan_earth_engine_run(
    payload: EarthEnginePlanPublicRequest,
    settings: Settings = Depends(get_settings_from_request),
) -> EarthEnginePlanPublic:
    return build_earth_engine_plan(payload.to_service_request(), settings=settings)
