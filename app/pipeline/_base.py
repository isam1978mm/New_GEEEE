from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.errors import ArtifactClassError


class ParityCategory(str, Enum):
    PARITY_REPRODUCES = "PARITY_REPRODUCES"
    PARITY_CORRECTS = "PARITY_CORRECTS"
    PARITY_REPLACES = "PARITY_REPLACES"


@dataclass(slots=True)
class StageArtifact:
    name: str
    relative_path: str
    artifact_class: ArtifactClass
    size_bytes: int = 0
    sha256: str | None = None
    http_servable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StageResult:
    artifacts: list[StageArtifact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StageContext:
    run_id: str
    settings: Settings
    run_dir: Path


def build_stage_artifact(
    *,
    name: str,
    relative_path: str,
    artifact_class: ArtifactClass | None,
    size_bytes: int = 0,
    sha256: str | None = None,
    http_servable: bool = True,
    metadata: dict[str, Any] | None = None,
) -> StageArtifact:
    if artifact_class is None:
        raise ArtifactClassError()

    return StageArtifact(
        name=name,
        relative_path=relative_path,
        artifact_class=artifact_class,
        size_bytes=size_bytes,
        sha256=sha256,
        http_servable=http_servable,
        metadata=metadata or {},
    )


class Stage(ABC):
    name: str = ""
    parity_category: ParityCategory | None = None
    parity_reason: str | None = None

    @abstractmethod
    async def run(self, context: StageContext) -> StageResult:
        raise NotImplementedError
