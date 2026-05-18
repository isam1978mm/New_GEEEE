from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.errors import ReadyPublic
from app.services.ee_session import initialize_ee_session

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> ReadyPublic:
    initialize_ee_session(get_settings())
    return ReadyPublic(status="ready")

