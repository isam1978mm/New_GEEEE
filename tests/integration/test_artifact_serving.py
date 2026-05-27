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
from app.services.artifact_response import is_expected_download_filename, public_download_filename


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


def test_public_download_filename_mapping_is_safe_and_keeps_unknown_names() -> None:
    assert public_download_filename("objects_index") == "objects_index.csv"
    assert public_download_filename("clusters_summary") == "clusters_summary.csv"
    assert public_download_filename("alignment_qa") == "alignment_qa.json"
    assert public_download_filename("alignment_audit") == "alignment_audit.json"
    assert public_download_filename("alignment_mask_selection") == "alignment_mask_selection.json"
    assert public_download_filename("unknown_artifact") == "unknown_artifact"
    assert is_expected_download_filename(artifact_name="objects_index", download_filename="objects_index.csv") is True
    assert is_expected_download_filename(artifact_name="objects_index", download_filename="objects_index") is False


def test_known_logical_artifact_download_uses_public_filename_with_extension() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(
            _run_known_artifact_filename_test(
                Path(temp_dir),
                artifact_name="objects_index",
                relative_path="objects_index.csv",
                expected_body="object_id\n1\n",
                expected_filename="objects_index.csv",
            )
        )


def test_known_logical_json_artifact_download_uses_public_filename_with_extension() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(
            _run_known_artifact_filename_test(
                Path(temp_dir),
                artifact_name="alignment_qa",
                relative_path="alignment_qa.json",
                expected_body='{"pass": true}\n',
                expected_filename="alignment_qa.json",
            )
        )


def test_new_download_route_accepts_safe_filename_and_old_route_still_works() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_dual_route_test(Path(temp_dir)))


def test_new_download_route_rejects_wrong_safe_filename() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_wrong_filename_route_test(Path(temp_dir)))


def test_operator_output_tree_lists_grouped_run_files_without_local_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_operator_output_tree_test(Path(temp_dir)))


def test_operator_output_download_preserves_real_filename_and_blocks_traversal() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_operator_output_download_guard_test(Path(temp_dir)))


def test_operator_output_tree_missing_run_returns_safe_error() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_operator_output_missing_run_test(Path(temp_dir)))


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
            assert 'filename="artifact.txt"' in response.headers["content-disposition"]
        else:
            assert response.json() == {
                "error": "artifact_unavailable",
                "message": "Artifact is unavailable.",
            }

    await engine.dispose()


async def _run_known_artifact_filename_test(
    tmp_path: Path,
    *,
    artifact_name: str,
    relative_path: str,
    expected_body: str,
    expected_filename: str,
) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        run_id = "run-1"
        run_dir = data_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / relative_path).write_text(expected_body, encoding="utf-8")

        async with session_factory() as session:
            await seed_artifact(
                session,
                run_id=run_id,
                artifact_name=artifact_name,
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                relative_path=relative_path,
            )

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(f"/runs/{run_id}/artifacts/{artifact_name}")

        assert response.status_code == 200
        assert response.text.replace("\r\n", "\n") == expected_body
        assert f'filename="{expected_filename}"' in response.headers["content-disposition"]
    finally:
        await engine.dispose()


async def _run_dual_route_test(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        run_id = "run-1"
        run_dir = data_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "objects_index.csv").write_text("object_id\n1\n", encoding="utf-8")

        async with session_factory() as session:
            await seed_artifact(
                session,
                run_id=run_id,
                artifact_name="objects_index",
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                relative_path="objects_index.csv",
            )

        with TestClient(app, raise_server_exceptions=False) as client:
            old_route_response = client.get(f"/runs/{run_id}/artifacts/objects_index")
            new_route_response = client.get(f"/runs/{run_id}/artifacts/objects_index/download/objects_index.csv")

        assert old_route_response.status_code == 200
        assert new_route_response.status_code == 200
        assert old_route_response.text.replace("\r\n", "\n") == "object_id\n1\n"
        assert new_route_response.text.replace("\r\n", "\n") == "object_id\n1\n"
        assert 'filename="objects_index.csv"' in old_route_response.headers["content-disposition"]
        assert 'filename="objects_index.csv"' in new_route_response.headers["content-disposition"]
    finally:
        await engine.dispose()


async def _run_wrong_filename_route_test(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        run_id = "run-1"
        run_dir = data_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "objects_index.csv").write_text("object_id\n1\n", encoding="utf-8")

        async with session_factory() as session:
            await seed_artifact(
                session,
                run_id=run_id,
                artifact_name="objects_index",
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                relative_path="objects_index.csv",
            )

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(f"/runs/{run_id}/artifacts/objects_index/download/objects_index")

        assert response.status_code == 404
        assert response.json() == {
            "error": "artifact_unavailable",
            "message": "Artifact is unavailable.",
        }
    finally:
        await engine.dispose()


async def _run_operator_output_tree_test(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        run_id = "run-1"
        run_dir = data_dir / "runs" / run_id
        (run_dir / "DEM_GEO8_TIFS").mkdir(parents=True, exist_ok=True)
        (run_dir / "QA" / "sar" / "intermediates").mkdir(parents=True, exist_ok=True)
        (run_dir / "DEM_GEO8_TIFS" / "DEM_640.tif").write_bytes(b"dem")
        (run_dir / "QA" / "REPORT_640_manifest.json").write_text(
            '{"reports":{"REPORT_640_Pottery_Report.tif":{"status":"not_implemented_no_source_equivalent"}}}',
            encoding="utf-8",
        )
        (run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json").write_text(
            '{"stages":{"per_image_products_db":{"status":"not_implemented_no_source_equivalent"}}}',
            encoding="utf-8",
        )
        (run_dir / ".env").write_text("SECRET=blocked", encoding="utf-8")

        async with session_factory() as session:
            session.add(
                Run(
                    id=run_id,
                    name="fixture",
                    status=RunStatus.DONE,
                    latitude=10.0,
                    longitude=20.0,
                )
            )
            await session.commit()

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(f"/runs/{run_id}/outputs")

        assert response.status_code == 200
        body = response.json()
        assert body["run_id"] == run_id
        assert body["outputs"]
        assert body["not_implemented"]
        assert "SECRET" not in response.text
        assert str(tmp_path) not in response.text
        assert "latitude" not in response.text.casefold()
        assert "longitude" not in response.text.casefold()

        dem_output = next(item for item in body["outputs"] if item["relative_path"] == "DEM_GEO8_TIFS/DEM_640.tif")
        assert dem_output == {
            "relative_path": "DEM_GEO8_TIFS/DEM_640.tif",
            "filename": "DEM_640.tif",
            "directory": "DEM_GEO8_TIFS",
            "group": "DEM_GEO8_TIFS",
            "size_bytes": 3,
            "extension": ".tif",
            "file_type": "tif",
            "status": "implemented",
            "download_url": f"/runs/{run_id}/outputs/download/DEM_GEO8_TIFS/DEM_640.tif",
        }
        assert all(item["filename"] != ".env" for item in body["outputs"])
        assert {
            item["relative_path"] for item in body["not_implemented"]
        } >= {
            "REPORT_640_Pottery_Report.tif",
            "QA/sar/intermediates/per_image_products_db",
        }
    finally:
        await engine.dispose()


async def _run_operator_output_download_guard_test(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        run_id = "run-1"
        run_dir = data_dir / "runs" / run_id
        (run_dir / "NPY_STACKS").mkdir(parents=True, exist_ok=True)
        (run_dir / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy").write_bytes(b"stack")

        async with session_factory() as session:
            session.add(
                Run(
                    id=run_id,
                    name="fixture",
                    status=RunStatus.DONE,
                    latitude=10.0,
                    longitude=20.0,
                )
            )
            await session.commit()

        with TestClient(app, raise_server_exceptions=False) as client:
            download_response = client.get(
                f"/runs/{run_id}/outputs/download/NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy"
            )
            traversal_response = client.get(f"/runs/{run_id}/outputs/download/..%2Fgrid_manifest.json")

        assert download_response.status_code == 200
        assert download_response.content == b"stack"
        assert 'filename="FINAL_TESLA_V7_2_HYPERCUBE.npy"' in download_response.headers["content-disposition"]
        assert traversal_response.status_code == 404
        assert traversal_response.json() == {
            "error": "artifact_unavailable",
            "message": "Artifact is unavailable.",
        }
    finally:
        await engine.dispose()


async def _run_operator_output_missing_run_test(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/runs/missing-run/outputs")

        assert response.status_code == 404
        assert response.json() == {
            "error": "run_not_found",
            "message": "Run is unavailable.",
        }
    finally:
        await engine.dispose()
