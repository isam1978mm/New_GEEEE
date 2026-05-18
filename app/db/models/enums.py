from __future__ import annotations

from enum import Enum


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"
    STALE_FAILED = "stale_failed"


class ArtifactClass(str, Enum):
    LOCAL_SENSITIVE = "LOCAL_SENSITIVE"
    REDACTED_PUBLIC = "REDACTED_PUBLIC"
    PREVIEW_ONLY = "PREVIEW_ONLY"
    FILESYSTEM_ONLY = "FILESYSTEM_ONLY"
