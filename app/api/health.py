from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas.errors import ReadyPublic
from app.services.ee_session import initialize_ee_session

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> ReadyPublic:
    settings = getattr(request.app.state, "settings", None) or get_settings()
    initialize_ee_session(settings)
    return ReadyPublic(status="ready")

