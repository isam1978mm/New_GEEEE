from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app


def test_post_runs_accepts_lat_lon_and_hides_them_in_public_surfaces(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_create_database(settings))
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _fake_background_runner_factory(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "release run"})
            run_id = response.json()["id"]
            list_response = client.get("/runs")
            detail_response = client.get(f"/runs/{run_id}")

        assert response.status_code == 201
        assert response.json()["name"] == "release run"
        assert response.json()["status"] == "queued"
        assert "lat" not in response.text.casefold()
        assert "lon" not in response.text.casefold()
        assert "path" not in response.text.casefold()

        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
        assert "latitude" not in list_response.text.casefold()
        assert "longitude" not in list_response.text.casefold()
        assert "transform" not in list_response.text.casefold()

        assert detail_response.status_code == 200
        body = detail_response.json()
        assert body["id"] == run_id
        assert body["status"] == "done"
        assert {artifact["name"] for artifact in body["artifacts"]} == {"objects_index", "alignment_qa"}
        assert all("relative_path" not in artifact for artifact in body["artifacts"])
        assert all("sha256" not in artifact for artifact in body["artifacts"])
        assert "experimental_summary" not in detail_response.text
        assert "experimental/" not in detail_response.text
        assert "filesystem_only" not in detail_response.text.casefold()
        _assert_no_sensitive_public_fields(detail_response.text)


def test_public_run_surfaces_do_not_expose_grid_override_fields(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_create_database(settings))
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _fake_background_runner_factory(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "release run"})
            run_id = response.json()["id"]
            detail_response = client.get(f"/runs/{run_id}")

        assert response.status_code == 201
        assert detail_response.status_code == 200
        assert "notebook" not in response.text.casefold()
        assert "notebook" not in detail_response.text.casefold()
        assert "grid" not in response.text.casefold()
        assert "grid" not in detail_response.text.casefold()
        _assert_no_sensitive_public_fields(response.text)
        _assert_no_sensitive_public_fields(detail_response.text)


def test_post_runs_rejects_second_active_run_with_public_safe_conflict(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_create_database(settings))
        asyncio.run(_seed_run(settings, run_id="active-run", status=RunStatus.QUEUED, name="active"))
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _fake_background_runner_factory(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "blocked"})

        assert response.status_code == 409
        assert response.json() == {
            "error": "active_run_exists",
            "message": "Another run is already active.",
        }
        _assert_no_sensitive_public_fields(response.text)


async def _create_database(settings: Settings) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


def _fake_background_runner_factory(settings: Settings):
    def fake_background_runner(run_id: str, _settings: Settings) -> None:
        assert _settings.data_dir == settings.data_dir
        asyncio.run(_mark_run_done_with_public_and_hidden_artifacts(settings, run_id))

    return fake_background_runner


async def _mark_run_done_with_public_and_hidden_artifacts(settings: Settings, run_id: str) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    run_dir = settings.data_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "objects_index.csv").write_text("object_id,row_min,row_max,col_min,col_max\n1,10,13,12,15\n", encoding="utf-8")
    (run_dir / "alignment_qa.json").write_text('{"pass": true}', encoding="utf-8")
    experimental_dir = run_dir / "experimental"
    experimental_dir.mkdir(parents=True, exist_ok=True)
    (experimental_dir / "summary.json").write_text('{"note":"hidden"}', encoding="utf-8")
    (run_dir / "internal.npy").write_bytes(b"0000")

    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        assert run is not None
        run.status = RunStatus.DONE
        session.add_all(
            [
                Artifact(
                    run_id=run_id,
                    name="objects_index",
                    relative_path="objects_index.csv",
                    size_bytes=(run_dir / "objects_index.csv").stat().st_size,
                    sha256="abcd" * 16,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="alignment_qa",
                    relative_path="alignment_qa.json",
                    size_bytes=(run_dir / "alignment_qa.json").stat().st_size,
                    sha256="abcd" * 16,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="experimental_summary",
                    relative_path="experimental/summary.json",
                    size_bytes=(experimental_dir / "summary.json").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    http_servable=False,
                ),
                Artifact(
                    run_id=run_id,
                    name="internal_array",
                    relative_path="internal.npy",
                    size_bytes=(run_dir / "internal.npy").stat().st_size,
                    sha256="abcd" * 16,
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    http_servable=False,
                ),
            ]
        )
        await session.commit()

    await engine.dispose()


async def _seed_run(settings: Settings, *, run_id: str, status: RunStatus, name: str) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                name=name,
                status=status,
                latitude=35.59499,
                longitude=36.12694,
            )
        )
        await session.commit()
    await engine.dispose()


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _assert_no_sensitive_public_fields(text: str) -> None:
    lowered = text.casefold()
    for forbidden in ("latitude", "longitude", "geometry", "bounds", "transform", "sha256", "relative_path", "path"):
        assert forbidden not in lowered
