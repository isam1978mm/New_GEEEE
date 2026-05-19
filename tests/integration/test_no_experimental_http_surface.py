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


def test_experimental_outputs_have_no_http_surface() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_seed_experimental_artifact(Path(temp_dir)))
        settings = Settings(
            data_dir=Path(temp_dir) / "data",
            database_path=Path(temp_dir) / "data" / "gee_screening.db",
        )

        app = create_app(settings)
        route_paths = {route.path for route in app.routes}
        assert all("experimental" not in path for path in route_paths)

        with TestClient(app, raise_server_exceptions=False) as client:
            blocked = client.get("/runs/run-1/artifacts/experimental_summary")
            root = client.get("/")

        assert blocked.status_code == 404
        assert blocked.json() == {
            "error": "artifact_unavailable",
            "message": "Artifact is unavailable.",
        }
        assert "experimental/summary.json" not in root.text
        assert "experimental_summary" not in root.text


async def _seed_experimental_artifact(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    data_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(data_dir=data_dir, database_path=db_path)

    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    run_dir = data_dir / "runs" / "run-1" / "experimental"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text('{"note":"hidden"}', encoding="utf-8")

    async with session_factory() as session:
        await _seed_run_and_artifact(session)

    await engine.dispose()


async def _seed_run_and_artifact(session: AsyncSession) -> None:
    session.add(
        Run(
            id="run-1",
            name="fixture",
            status=RunStatus.DONE,
            latitude=35.59499,
            longitude=36.12694,
        )
    )
    session.add(
        Artifact(
            run_id="run-1",
            name="experimental_summary",
            relative_path="experimental/summary.json",
            size_bytes=17,
            sha256=None,
            artifact_class=ArtifactClass.FILESYSTEM_ONLY,
            http_servable=False,
        )
    )
    await session.commit()
