from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app


async def seed_artifact(
    session: AsyncSession,
    *,
    run_id: str,
    artifact_name: str,
    artifact_class: ArtifactClass,
    relative_path: str,
) -> None:
    session.add(
        Run(
            id=run_id,
            name="fixture",
            status=RunStatus.DONE,
            latitude=10.0,
            longitude=20.0,
        )
    )
    session.add(
        Artifact(
            run_id=run_id,
            name=artifact_name,
            relative_path=relative_path,
            size_bytes=4,
            sha256="abcd" * 16,
            artifact_class=artifact_class,
            http_servable=True,
        )
    )
    await session.commit()


def test_artifact_class_serving_contract_local_sensitive() -> None:
    _assert_artifact_class_response(ArtifactClass.LOCAL_SENSITIVE, 200)


def test_artifact_class_serving_contract_redacted_public() -> None:
    _assert_artifact_class_response(ArtifactClass.REDACTED_PUBLIC, 200)


def test_artifact_class_serving_contract_preview_only() -> None:
    _assert_artifact_class_response(ArtifactClass.PREVIEW_ONLY, 200)


def test_artifact_class_serving_contract_filesystem_only() -> None:
    _assert_artifact_class_response(ArtifactClass.FILESYSTEM_ONLY, 404)


def _assert_artifact_class_response(
    artifact_class: ArtifactClass,
    expected_status: int,
) -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(
            _run_artifact_class_response_test(
                tmp_path=Path(temp_dir),
                artifact_class=artifact_class,
                expected_status=expected_status,
            )
        )


async def _run_artifact_class_response_test(
    tmp_path: Path,
    artifact_class: ArtifactClass,
    expected_status: int,
) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    run_id = "run-1"
    run_dir = data_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "artifact.txt").write_text("demo", encoding="utf-8")

    async with session_factory() as session:
        await seed_artifact(
            session,
            run_id=run_id,
            artifact_name="artifact.txt",
            artifact_class=artifact_class,
            relative_path="artifact.txt",
        )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(f"/runs/{run_id}/artifacts/artifact.txt")
        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.text == "demo"
        else:
            assert response.json() == {
                "error": "artifact_unavailable",
                "message": "Artifact is unavailable.",
            }

    await engine.dispose()
