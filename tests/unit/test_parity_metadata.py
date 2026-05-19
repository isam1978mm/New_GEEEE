from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.errors import ParityMetadataError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.orchestrator import Orchestrator


class MissingParityStage(Stage):
    name = "missing"

    async def run(self, context: StageContext) -> StageResult:
        return StageResult()


class MissingReasonStage(Stage):
    name = "missing_reason"
    parity_category = ParityCategory.PARITY_CORRECTS

    async def run(self, context: StageContext) -> StageResult:
        return StageResult()


class ValidStage(Stage):
    name = "valid"
    parity_category = ParityCategory.PARITY_REPRODUCES

    async def run(self, context: StageContext) -> StageResult:
        return StageResult()


class MissingReplaceReasonStage(Stage):
    name = "missing_replace_reason"
    parity_category = ParityCategory.PARITY_REPLACES

    async def run(self, context: StageContext) -> StageResult:
        return StageResult()


def test_orchestrator_rejects_missing_parity_category(tmp_path) -> None:
    with pytest.raises(ParityMetadataError):
        Orchestrator(
            settings=Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite"),
            session_factory=_session_factory(tmp_path),
            stages=[MissingParityStage()],
        )


def test_orchestrator_rejects_missing_reason_for_corrects(tmp_path) -> None:
    with pytest.raises(ParityMetadataError):
        Orchestrator(
            settings=Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite"),
            session_factory=_session_factory(tmp_path),
            stages=[MissingReasonStage()],
        )


def test_orchestrator_accepts_valid_parity_metadata(tmp_path) -> None:
    orchestrator = Orchestrator(
        settings=Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite"),
        session_factory=_session_factory(tmp_path),
        stages=[ValidStage()],
    )

    assert len(orchestrator.stages) == 1


def test_orchestrator_rejects_missing_reason_for_replaces(tmp_path) -> None:
    with pytest.raises(ParityMetadataError):
        Orchestrator(
            settings=Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite"),
            session_factory=_session_factory(tmp_path),
            stages=[MissingReplaceReasonStage()],
        )


def _session_factory(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    engine = create_async_engine(settings.database_url, future=True)
    return async_sessionmaker(engine, expire_on_commit=False)
