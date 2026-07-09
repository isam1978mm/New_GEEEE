from __future__ import annotations

from pydantic import BaseModel, Field


class OperatorOutputFilePublic(BaseModel):
    relative_path: str
    filename: str
    directory: str
    group: str
    size_bytes: int
    extension: str
    file_type: str
    status: str
    download_url: str


class OperatorOutputStatusPublic(BaseModel):
    relative_path: str
    filename: str
    directory: str
    group: str
    status: str
    source: str


class OperatorOutputTreePublic(BaseModel):
    run_id: str
    outputs: list[OperatorOutputFilePublic] = Field(default_factory=list)
    not_implemented: list[OperatorOutputStatusPublic] = Field(default_factory=list)
    read_errors: list[OperatorOutputStatusPublic] = Field(default_factory=list)
