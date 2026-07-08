from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models.enums import RunStatus
from app.schemas.artifact import ArtifactPublic

class RunCreate(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    name: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_private_local_name(cls, value: str | None) -> str | None:
        return value


class RunPublic(BaseModel):
    id: str
    name: str | None
    status: RunStatus
    created_at: datetime
    disk_usage_bytes: int | None = None
    output_file_count: int | None = None
    last_disk_scan_at: datetime | None = None


class RunStageProgressPublic(BaseModel):
    name: str
    label: str
    status: str


class RunHistoryEventPublic(BaseModel):
    timestamp: datetime
    event_type: str
    label: str
    message: str
    stage_name: str | None = None


class RunDetailPublic(RunPublic):
    current_stage: str | None = None
    stages: list[RunStageProgressPublic] = Field(default_factory=list)
    history: list[RunHistoryEventPublic] = Field(default_factory=list)
    artifacts: list[ArtifactPublic] = Field(default_factory=list)


class RunDeletePublic(BaseModel):
    run_id: str
    deleted: bool
    deleted_files_count: int
    deleted_dirs_count: int
    freed_bytes: int
    status: str
    message: str


class RunDeletionAuditRecordPublic(BaseModel):
    run_id: str
    run_name: str | None
    deleted_at: datetime
    deleted_files_count: int
    deleted_dirs_count: int
    freed_bytes: int
    status: str
    message: str


class RunDeletionAuditPublic(BaseModel):
    total_freed_bytes: int
    records: list[RunDeletionAuditRecordPublic] = Field(default_factory=list)


class CleanupRunSuggestionPublic(BaseModel):
    id: str
    name: str | None
    status: RunStatus
    created_at: datetime
    disk_usage_bytes: int | None = None
    output_file_count: int | None = None
    last_disk_scan_at: datetime | None = None


class RunCleanupSummaryPublic(BaseModel):
    total_runs: int
    total_disk_usage_bytes: int
    terminal_runs_count: int
    active_runs_count: int
    deleted_runs_count: int
    total_freed_bytes: int
    largest_runs: list[CleanupRunSuggestionPublic] = Field(default_factory=list)
    oldest_terminal_runs: list[CleanupRunSuggestionPublic] = Field(default_factory=list)
    stale_failed_runs: list[CleanupRunSuggestionPublic] = Field(default_factory=list)
    cleanup_recommended: bool
    warning_reason: str
    threshold_bytes: int
