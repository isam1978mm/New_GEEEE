"""A4 public API safety integration tests.

End-to-end checks over the real FastAPI app proving that:
- FastAPI validation errors do not echo submitted request bodies (unsafe names,
  coordinates, path-like strings, raw lat/lon values).
- Public artifact listing excludes LOCAL_SENSITIVE / FILESYSTEM_ONLY artifacts
  and never exposes relative/absolute paths.
- Artifact download routes only serve public-servable artifacts and reject
  private classes and path-traversal names without leaking paths.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

# Provide lightweight stand-ins for heavy geospatial/Earth Engine modules when
# they are not installed, so the public API safety surface can be exercised
# without raster dependencies. ``setdefault`` never overrides a real install.
for _heavy_module in (
    "rasterio",
    "rasterio.transform",
    "rasterio.features",
    "rasterio.warp",
    "rasterio.enums",
    "ee",
):
    sys.modules.setdefault(_heavy_module, MagicMock())

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app

ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)([A-Z]:\\|/Users/|/home/|/tmp/)")
COORDINATE_PAIR_PATTERN = re.compile(r"\b-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+\b")


# --- 1. Validation error echo safety ----------------------------------------


def test_create_run_with_coordinate_like_name_returns_generic_validation_error() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        unsafe_name = "35.59499, 36.12694"

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/runs", json={"lat": 35.59499, "lon": 36.12694, "name": unsafe_name}
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        assert unsafe_name not in response.text
        assert COORDINATE_PAIR_PATTERN.search(response.text) is None
        _assert_no_leakage(response.text)


def test_create_run_with_path_like_name_does_not_echo_path() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        unsafe_name = r"C:\secret\runs\path.txt"

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/runs", json={"lat": 35.59499, "lon": 36.12694, "name": unsafe_name}
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        assert "secret" not in response.text.casefold()
        assert "path" not in response.text.casefold()
        _assert_no_leakage(response.text)


def test_create_run_with_out_of_range_coordinates_does_not_echo_values() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/runs", json={"lat": 999.123456, "lon": -888.654321, "name": "safe name"}
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        # Raw submitted lat/lon values must not be echoed back.
        assert "999.123456" not in response.text
        assert "888.654321" not in response.text
        _assert_no_leakage(response.text)


# --- 2. Public artifact listing safety ---------------------------------------


def test_run_detail_lists_only_public_artifacts() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run_with_mixed_artifacts(settings, "run-mixed"))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/run-mixed")

        assert response.status_code == 200
        body = response.json()
        listed = {artifact["name"] for artifact in body["artifacts"]}
        assert listed == {"objects_index", "preview_overlay", "experimental_summary"}
        assert "internal_array" not in listed
        assert "kmz_bundle" not in listed
        # No public artifact may expose a relative or absolute path.
        for artifact in body["artifacts"]:
            assert "relative_path" not in artifact
            assert "path" not in artifact
            assert set(artifact) <= {"name", "artifact_class", "created_at"}
        assert "experimental/" not in response.text
        assert "internal.npy" not in response.text
        assert ".kmz" not in response.text.casefold()
        _assert_no_leakage(response.text)


# --- 3. Artifact download route safety ---------------------------------------


def test_public_artifact_route_serves_redacted_public_artifact() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run_with_mixed_artifacts(settings, "run-dl"))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/run-dl/artifacts/objects_index")

        assert response.status_code == 200


def test_private_artifacts_are_not_downloadable_through_public_route() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run_with_mixed_artifacts(settings, "run-priv"))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            local_sensitive = client.get("/runs/run-priv/artifacts/internal_array")
            filesystem_only = client.get("/runs/run-priv/artifacts/kmz_bundle")
            experimental = client.get("/runs/run-priv/artifacts/experimental_summary")

        for response in (local_sensitive, filesystem_only):
            assert response.status_code == 404
            assert response.json() == {"error": "artifact_unavailable", "message": "Artifact is unavailable."}
            assert "relative_path" not in response.text
            _assert_no_leakage(response.text)
        assert experimental.status_code == 200
        assert experimental.json() == {"note": "hidden"}


def test_path_traversal_artifact_names_are_not_served() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run_with_mixed_artifacts(settings, "run-trav"))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            responses = [
                client.get("/runs/run-trav/artifacts/..%2F..%2Fsecret"),
                client.get("/runs/run-trav/artifacts/internal.npy"),
                client.get("/runs/run-trav/artifacts/experimental%2Fsummary.json"),
            ]

        for response in responses:
            assert response.status_code in {404, 400}
            assert "secret" not in response.text.casefold()
            assert "relative_path" not in response.text
            _assert_no_leakage(response.text)


# --- Helpers -----------------------------------------------------------------


async def _seed_run_with_mixed_artifacts(settings: Settings, run_id: str) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    run_dir = settings.data_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "objects_index.csv").write_text(
        "object_id,row_min,row_max,col_min,col_max\n1,10,13,12,15\n", encoding="utf-8"
    )
    (run_dir / "preview.png").write_bytes(b"\x89PNG\r\n")
    (run_dir / "internal.npy").write_bytes(b"0000")
    experimental_dir = run_dir / "experimental"
    experimental_dir.mkdir(parents=True, exist_ok=True)
    (experimental_dir / "summary.json").write_text('{"note":"hidden"}', encoding="utf-8")
    exports_dir = run_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    (exports_dir / "site.kmz").write_bytes(b"PK\x03\x04")

    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                name="mixed artifacts",
                status=RunStatus.DONE,
                latitude=35.59499,
                longitude=36.12694,
            )
        )
        session.add_all(
            [
                Artifact(
                    run_id=run_id,
                    name="objects_index",
                    relative_path="objects_index.csv",
                    size_bytes=(run_dir / "objects_index.csv").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="preview_overlay",
                    relative_path="preview.png",
                    size_bytes=(run_dir / "preview.png").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.PREVIEW_ONLY,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="internal_array",
                    relative_path="internal.npy",
                    size_bytes=(run_dir / "internal.npy").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    http_servable=False,
                ),
                Artifact(
                    run_id=run_id,
                    name="experimental_summary",
                    relative_path="experimental/summary.json",
                    size_bytes=(experimental_dir / "summary.json").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="kmz_bundle",
                    relative_path="exports/site.kmz",
                    size_bytes=(exports_dir / "site.kmz").stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    http_servable=False,
                ),
            ]
        )
        await session.commit()
    await engine.dispose()


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _assert_no_leakage(text: str) -> None:
    assert ABSOLUTE_PATH_PATTERN.search(text) is None
    lowered = text.casefold()
    for forbidden in ("latitude", "longitude", "geometry", "bounds", "bbox", "transform"):
        assert forbidden not in lowered
