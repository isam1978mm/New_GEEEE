from __future__ import annotations

import asyncio
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app
from app.services.redaction import verify_redacted

ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)([A-Z]:\\|/Users/|/home/)")
HEX_HASH_PATTERN = re.compile(r"\b[a-fA-F0-9]{32,64}\b")
COORDINATE_PAIR_PATTERN = re.compile(r"\b-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+\b")


def test_public_http_surface_does_not_leak_coordinates_hashes_or_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_seed_safe_public_artifact(Path(temp_dir)))
        settings = Settings(
            data_dir=Path(temp_dir) / "data",
            database_path=Path(temp_dir) / "data" / "gee_screening.db",
            ee_service_account_email=None,
            ee_service_account_key_path=None,
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            health = client.get("/healthz")
            ready = client.get("/readyz")
            missing_artifact = client.get("/runs/run-1/artifacts/missing")
            safe_artifact = client.get("/runs/run-1/artifacts/objects_index")
            root = client.get("/")

        assert health.status_code == 200
        verify_redacted(health.json())
        assert ready.status_code == 503
        verify_redacted(ready.json())
        assert missing_artifact.status_code == 404
        verify_redacted(missing_artifact.json())
        assert safe_artifact.status_code == 200
        assert root.status_code == 200

        for text in [health.text, ready.text, missing_artifact.text, safe_artifact.text, root.text]:
            _assert_no_leakage(text)

        assert "latitude" not in safe_artifact.text.casefold()
        assert "longitude" not in safe_artifact.text.casefold()
        assert "bounds" not in safe_artifact.text.casefold()
        assert "transform" not in safe_artifact.text.casefold()


async def _seed_safe_public_artifact(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    data_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(data_dir=data_dir, database_path=db_path)

    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    run_dir = data_dir / "runs" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "objects_index.csv").write_text(
        "object_id,row_min,row_max,col_min,col_max\n1,10,13,12,15\n",
        encoding="utf-8",
    )

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
            name="objects_index",
            relative_path="objects_index.csv",
            size_bytes=55,
            sha256=None,
            artifact_class=ArtifactClass.REDACTED_PUBLIC,
            http_servable=True,
        )
    )
    await session.commit()


def _assert_no_leakage(text: str) -> None:
    assert ABSOLUTE_PATH_PATTERN.search(text) is None
    assert HEX_HASH_PATTERN.search(text) is None
    assert COORDINATE_PAIR_PATTERN.search(text) is None
