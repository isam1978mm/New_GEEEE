from __future__ import annotations

from pydantic import BaseModel


class ErrorPublic(BaseModel):
    error: str
    message: str


class ReadyPublic(BaseModel):
    status: str

