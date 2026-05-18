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
    http_servable: bool = True,
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
            http_servable=http_servable,
        )
    )
    await session.commit()


def test_redacted_public_and_preview_only_artifacts_are_served() -> None:
    _assert_artifact_response(ArtifactClass.REDACTED_PUBLIC, 200)
    _assert_artifact_response(ArtifactClass.PREVIEW_ONLY, 200)


def test_filesystem_only_artifacts_are_never_served() -> None:
    _assert_artifact_response(ArtifactClass.FILESYSTEM_ONLY, 404)


def test_local_sensitive_artifacts_are_served_on_loopback() -> None:
    _assert_artifact_response(ArtifactClass.LOCAL_SENSITIVE, 200)


def test_local_sensitive_artifacts_are_blocked_under_network_bind() -> None:
    _assert_artifact_response(ArtifactClass.LOCAL_SENSITIVE, 404, allow_network_bind=True)


def test_non_http_servable_artifacts_are_blocked() -> None:
    _assert_artifact_response(ArtifactClass.REDACTED_PUBLIC, 404, http_servable=False)


def _assert_artifact_response(
    artifact_class: ArtifactClass,
    expected_status: int,
    *,
    allow_network_bind: bool = False,
    http_servable: bool = True,
) -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(
            _run_artifact_response_test(
                tmp_path=Path(temp_dir),
                artifact_class=artifact_class,
                expected_status=expected_status,
                allow_network_bind=allow_network_bind,
                http_servable=http_servable,
            )
        )


async def _run_artifact_response_test(
    *,
    tmp_path: Path,
    artifact_class: ArtifactClass,
    expected_status: int,
    allow_network_bind: bool,
    http_servable: bool,
) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(
        data_dir=data_dir,
        database_path=db_path,
        allow_network_bind=allow_network_bind,
    )
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
            http_servable=http_servable,
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
