from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app
from app.services.run_history import append_run_event
from app.services.storage import write_stage_manifest


@pytest.fixture(autouse=True)
def _disable_startup_active_run_recovery(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.mark_stale_active_runs",
        _noop_startup_active_run_recovery,
    )


def test_post_runs_accepts_lat_lon_and_hides_them_in_public_surfaces(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
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
        assert "history" in body
        assert {artifact["name"] for artifact in body["artifacts"]} == {
            "objects_index",
            "alignment_qa",
            "experimental_summary",
        }
        assert all("relative_path" not in artifact for artifact in body["artifacts"])
        assert all("sha256" not in artifact for artifact in body["artifacts"])
        assert "experimental/" not in detail_response.text
        assert "filesystem_only" not in detail_response.text.casefold()
        _assert_no_sensitive_public_fields(detail_response.text)


def test_public_run_surfaces_do_not_expose_grid_override_fields(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _fake_background_runner_factory(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "release run"})
            run_id = response.json()["id"]
            detail_response = client.get(f"/runs/{run_id}")

        assert response.status_code == 201
        assert detail_response.status_code == 200
        assert "notebook" not in response.text.casefold()
        assert "notebook" not in detail_response.text.casefold()
        assert "grid_spec_override" not in response.text.casefold()
        assert "grid_spec_override" not in detail_response.text.casefold()
        _assert_no_sensitive_public_fields(response.text)
        _assert_no_sensitive_public_fields(detail_response.text)


def test_post_runs_rejects_second_active_run_with_public_safe_conflict(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
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


def test_post_runs_maps_database_active_run_race_to_conflict(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(
            _seed_run(
                settings,
                run_id="active-run",
                status=RunStatus.QUEUED,
                name="active",
            )
        )
        monkeypatch.setattr(
            "app.api.runs.ensure_single_active_run",
            _allow_active_run_precheck,
        )
        monkeypatch.setattr(
            "app.api.runs.enqueue_core_pipeline_run",
            _fake_background_runner_factory(settings),
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/runs",
                json={
                    "lat": 35.59499,
                    "lon": 36.12694,
                    "name": "racing",
                },
            )

        assert response.status_code == 409
        assert response.json() == {
            "error": "active_run_exists",
            "message": "Another run is already active.",
        }
        _assert_no_sensitive_public_fields(response.text)


def test_background_pipeline_failure_marks_run_failed_without_breaking_create_response(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        monkeypatch.setattr("app.api.runs.run_core_pipeline_for_run", _failing_run_core_pipeline)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "failing run"})
            run_id = response.json()["id"]
            detail_response = client.get(f"/runs/{run_id}")

        assert response.status_code == 201
        assert response.json()["status"] == "queued"
        assert "traceback" not in response.text.casefold()

        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "failed"
        _assert_no_sensitive_public_fields(detail_response.text)
        assert "traceback" not in detail_response.text.casefold()


def test_run_detail_exposes_public_safe_stage_progress() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run(settings, run_id="progress-run", status=RunStatus.QUEUED, name="progress"))
        write_stage_manifest(settings, "progress-run", "grid", {"status": "done", "artifact_count": 1})
        write_stage_manifest(settings, "progress-run", "dem", {"status": "running", "artifact_count": 0})

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/progress-run")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "queued"
        assert body["current_stage"] == "dem"
        assert len(body["stages"]) == 20
        assert body["stages"][0] == {"name": "grid", "label": "GRID setup", "status": "done"}
        assert body["stages"][1] == {"name": "dem", "label": "DEM", "status": "running"}
        assert body["stages"][2] == {"name": "zero_shift", "label": "Zero shift", "status": "pending"}
        assert all(set(stage) == {"name", "label", "status"} for stage in body["stages"])
        assert {stage["status"] for stage in body["stages"]} <= {"pending", "running", "done", "failed", "skipped"}
        assert {stage["label"] for stage in body["stages"]} >= {"GRID setup", "SAR RTC", "Classifier", "Alignment QA"}


def test_run_public_surfaces_include_safe_disk_summary_without_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        asyncio.run(_seed_run(settings, run_id=run_id, status=RunStatus.DONE, name="disk summary"))
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "a.txt").write_bytes(b"abc")
        nested = run_dir / "nested"
        nested.mkdir()
        (nested / "b.bin").write_bytes(b"12345")

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            list_response = client.get("/runs")
            detail_response = client.get(f"/runs/{run_id}")

        assert list_response.status_code == 200
        list_body = list_response.json()[0]
        assert list_body["disk_usage_bytes"] == 8
        assert list_body["output_file_count"] == 2
        assert list_body["last_disk_scan_at"] is not None
        _assert_no_sensitive_public_fields(list_response.text)

        assert detail_response.status_code == 200
        detail_body = detail_response.json()
        assert detail_body["disk_usage_bytes"] == 8
        assert detail_body["output_file_count"] == 2
        assert detail_body["last_disk_scan_at"] is not None
        _assert_no_sensitive_public_fields(detail_response.text)


def test_terminal_run_refreshes_stale_disk_summary_when_exports_exceed_stored_size() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        stale_scan_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        asyncio.run(
            _seed_run(
                settings,
                run_id=run_id,
                status=RunStatus.DONE,
                name="stale-summary",
                disk_usage_bytes=828,
                output_file_count=1,
                last_disk_scan_at=stale_scan_at,
            )
        )
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        public_path = run_dir / "NDVI.tif"
        public_bytes = b"x" * (2 * 1024 * 1024)
        public_path.write_bytes(public_bytes)
        hidden_path = run_dir / "internal.npy"
        hidden_bytes = b"y" * 2048
        hidden_path.write_bytes(hidden_bytes)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            list_response = client.get("/runs")
            detail_response = client.get(f"/runs/{run_id}")

        assert list_response.status_code == 200
        list_body = list_response.json()[0]
        assert list_body["disk_usage_bytes"] >= len(public_bytes) + len(hidden_bytes)
        assert list_body["disk_usage_bytes"] > 828
        assert list_body["output_file_count"] == 2
        assert list_body["last_disk_scan_at"] != stale_scan_at.isoformat()

        assert detail_response.status_code == 200
        detail_body = detail_response.json()
        assert detail_body["disk_usage_bytes"] >= len(public_bytes)
        assert detail_body["disk_usage_bytes"] > 828
        assert detail_body["output_file_count"] == 2
        _assert_no_sensitive_public_fields(list_response.text)
        _assert_no_sensitive_public_fields(detail_response.text)


def test_active_run_does_not_rescan_existing_disk_summary_on_every_request() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        last_scan_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        asyncio.run(
            _seed_run(
                settings,
                run_id=run_id,
                status=RunStatus.QUEUED,
                name="active-summary",
                disk_usage_bytes=828,
                output_file_count=1,
                last_disk_scan_at=last_scan_at,
            )
        )
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "NDVI.tif").write_bytes(b"x" * (2 * 1024 * 1024))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            list_response = client.get("/runs")
            detail_response = client.get(f"/runs/{run_id}")

        assert list_response.status_code == 200
        assert list_response.json()[0]["disk_usage_bytes"] == 828
        assert list_response.json()[0]["last_disk_scan_at"].startswith("2026-01-01T00:00:00")

        assert detail_response.status_code == 200
        assert detail_response.json()["disk_usage_bytes"] == 828
        assert detail_response.json()["last_disk_scan_at"].startswith("2026-01-01T00:00:00")
        _assert_no_sensitive_public_fields(list_response.text)
        _assert_no_sensitive_public_fields(detail_response.text)


def test_disk_summary_counts_symlink_without_following_external_target() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        asyncio.run(_seed_run(settings, run_id=run_id, status=RunStatus.DONE, name="symlink summary"))
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "local.txt").write_bytes(b"1234")
        outside = Path(temp_dir) / "outside-large.bin"
        outside.write_bytes(b"x" * 4096)
        symlink_path = run_dir / "external-link.bin"
        try:
            symlink_path.symlink_to(outside)
        except OSError:
            return

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(f"/runs/{run_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["output_file_count"] == 2
        assert body["disk_usage_bytes"] >= 4
        assert body["disk_usage_bytes"] < 4096
        _assert_no_sensitive_public_fields(response.text)
        assert "artifact_count" not in response.text
        _assert_no_sensitive_public_fields(response.text)


def test_run_detail_exposes_failed_stage_without_internal_error_content() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run(settings, run_id="failed-stage-run", status=RunStatus.FAILED, name="failed"))
        write_stage_manifest(settings, "failed-stage-run", "grid", {"status": "done", "artifact_count": 1})
        write_stage_manifest(
            settings,
            "failed-stage-run",
            "dem",
            {"status": "failed", "artifact_count": 0, "metadata": {"failure": "stage_failed"}},
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/failed-stage-run")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["current_stage"] == "dem"
        assert body["stages"][1] == {"name": "dem", "label": "DEM", "status": "failed"}
        assert all(set(stage) == {"name", "label", "status"} for stage in body["stages"])
        assert {"stage_failed", "run_failed"} <= {event["event_type"] for event in body["history"]}
        failed_event = next(event for event in body["history"] if event["event_type"] == "stage_failed")
        assert failed_event["stage_name"] == "dem"
        assert failed_event["label"] == "DEM failed"
        assert failed_event["message"] == "DEM stage failed."
        assert "metadata" not in response.text
        assert "traceback" not in response.text.casefold()
        _assert_no_sensitive_public_fields(response.text)


def test_run_detail_uses_persisted_public_safe_status_history() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run(settings, run_id="history-run", status=RunStatus.QUEUED, name="history"))
        append_run_event(settings, "history-run", "run_created")
        append_run_event(settings, "history-run", "run_queued")
        append_run_event(settings, "history-run", "run_started")
        append_run_event(settings, "history-run", "stage_started", stage_name="sar_rtc")
        write_stage_manifest(settings, "history-run", "sar_rtc", {"status": "running", "artifact_count": 0})

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/history-run")

        assert response.status_code == 200
        body = response.json()
        assert body["current_stage"] == "sar_rtc"
        assert [event["event_type"] for event in body["history"]] == [
            "run_created",
            "run_queued",
            "run_started",
            "stage_started",
        ]
        assert body["history"][-1] == {
            "timestamp": body["history"][-1]["timestamp"],
            "event_type": "stage_started",
            "label": "SAR RTC started",
            "message": "SAR RTC stage started.",
            "stage_name": "sar_rtc",
        }
        assert "artifact_count" not in response.text
        assert "metadata" not in response.text
        _assert_no_sensitive_public_fields(response.text)


def test_terminal_runs_without_stage_manifests_get_sparse_fallback_history() -> None:
    cases = [
        (RunStatus.DONE, "run_done"),
        (RunStatus.FAILED, "run_failed"),
        (RunStatus.STALE_FAILED, "run_stale_failed"),
    ]
    for status, terminal_event in cases:
        with TemporaryDirectory() as temp_dir:
            settings = _settings(Path(temp_dir))
            _upgrade_database(settings)
            asyncio.run(_seed_run(settings, run_id=f"{status.value}-sparse-run", status=status, name="sparse"))

            with TestClient(create_app(settings), raise_server_exceptions=False) as client:
                response = client.get(f"/runs/{status.value}-sparse-run")

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == status.value
            assert body["current_stage"] is None
            assert body["stages"] == []
            assert [event["event_type"] for event in body["history"]] == [
                "run_created",
                "run_queued",
                terminal_event,
            ]
            assert all(set(event) <= {"timestamp", "event_type", "label", "stage_name", "message"} for event in body["history"])
            assert all(not event["event_type"].startswith("stage_") for event in body["history"])
            assert all(event.get("stage_name") is None for event in body["history"])
            _assert_no_sensitive_public_fields(response.text)


def test_delete_terminal_run_removes_database_rows_and_run_directory() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        asyncio.run(_seed_run(settings, run_id=run_id, status=RunStatus.DONE, name="delete-me"))
        run_dir = settings.data_dir / "runs" / run_id
        nested_dir = run_dir / "nested"
        nested_dir.mkdir(parents=True)
        (run_dir / "objects_index.csv").write_bytes(b"id\n1\n")
        (nested_dir / "note.txt").write_bytes(b"remove")

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            delete_response = client.delete(f"/runs/{run_id}")
            list_response = client.get("/runs")
            detail_response = client.get(f"/runs/{run_id}")
            outputs_response = client.get(f"/runs/{run_id}/outputs")
            audit_response = client.get("/runs/deletion-audit")

        assert delete_response.status_code == 200
        body = delete_response.json()
        assert body == {
            "run_id": run_id,
            "deleted": True,
            "deleted_files_count": 2,
            "deleted_dirs_count": 1,
            "freed_bytes": len(b"id\n1\n") + len(b"remove"),
            "status": "deleted",
            "message": "Run deleted.",
        }
        assert not run_dir.exists()
        assert all(run["id"] != run_id for run in list_response.json())
        assert detail_response.status_code == 404
        assert outputs_response.status_code == 404
        _assert_no_sensitive_public_fields(delete_response.text)

        assert audit_response.status_code == 200
        audit_body = audit_response.json()
        assert audit_body["total_freed_bytes"] == body["freed_bytes"]
        assert len(audit_body["records"]) == 1
        assert audit_body["records"][0] == {
            "run_id": run_id,
            "run_name": "delete-me",
            "deleted_at": audit_body["records"][0]["deleted_at"],
            "deleted_files_count": 2,
            "deleted_dirs_count": 1,
            "freed_bytes": body["freed_bytes"],
            "status": "deleted",
            "message": "Run deleted.",
        }
        _assert_no_sensitive_public_fields(audit_response.text)


def test_delete_terminal_run_persists_safe_deletion_audit_without_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        asyncio.run(_seed_run(settings, run_id=run_id, status=RunStatus.FAILED, name="failed cleanup"))
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "artifact.bin").write_bytes(b"1234567")

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            delete_response = client.delete(f"/runs/{run_id}")
            audit_response = client.get("/runs/deletion-audit")

        assert delete_response.status_code == 200
        assert audit_response.status_code == 200
        assert audit_response.json()["total_freed_bytes"] == 7
        assert audit_response.json()["records"][0]["run_id"] == run_id
        assert audit_response.json()["records"][0]["run_name"] == "failed cleanup"
        assert audit_response.json()["records"][0]["freed_bytes"] == 7
        assert "artifact.bin" not in audit_response.text
        assert str(settings.data_dir) not in audit_response.text
        _assert_no_sensitive_public_fields(audit_response.text)


def test_delete_active_run_returns_conflict_and_preserves_files() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())
        asyncio.run(_seed_run(settings, run_id=run_id, status=RunStatus.QUEUED, name="active-delete"))
        run_dir = settings.data_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        artifact_path = run_dir / "keep.txt"
        artifact_path.write_text("keep", encoding="utf-8")

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.delete(f"/runs/{run_id}")
            detail_response = client.get(f"/runs/{run_id}")

        assert response.status_code == 409
        assert response.json() == {
            "error": "active_run_delete_blocked",
            "message": "Cannot delete active run.",
        }
        assert artifact_path.exists()
        assert detail_response.status_code == 200
        _assert_no_sensitive_public_fields(response.text)


def test_delete_missing_run_returns_not_found() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        run_id = str(uuid4())

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.delete(f"/runs/{run_id}")

        assert response.status_code == 404
        assert response.json() == {
            "error": "run_not_found",
            "message": "Run is unavailable.",
        }


def test_delete_run_rejects_traversal_and_absolute_identifiers() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            responses = [
                client.delete("/runs/.."),
                client.delete("/runs/..%2Fsecret"),
                client.delete("/runs/C:%5Csecret"),
                client.delete("/runs/%5C%5Cserver%5Cshare"),
                client.delete("/runs/%2Ftmp%2Fsecret"),
                client.delete("/runs/not-a-uuid"),
            ]

        assert all(response.status_code in {400, 404, 405} for response in responses)
        for response in responses:
            assert "secret" not in response.text.casefold()
            assert "tmp" not in response.text.casefold()
            assert "path" not in response.text.casefold()


def test_list_runs_q_filters_by_name_and_id_fragment() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        first_id = str(uuid4())
        second_id = str(uuid4())
        asyncio.run(
            _seed_run(
                settings,
                run_id=first_id,
                status=RunStatus.DONE,
                name="alpha signal",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=second_id,
                status=RunStatus.FAILED,
                name="beta window",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            by_name = client.get("/runs?q=alpha")
            by_id = client.get(f"/runs?q={second_id[:8]}")

        assert by_name.status_code == 200
        assert [row["id"] for row in by_name.json()] == [first_id]
        assert by_id.status_code == 200
        assert [row["id"] for row in by_id.json()] == [second_id]
        _assert_no_sensitive_public_fields(by_name.text)
        _assert_no_sensitive_public_fields(by_id.text)


def test_list_runs_status_filter_and_created_at_sorting() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        older_id = str(uuid4())
        newer_id = str(uuid4())
        failed_id = str(uuid4())
        asyncio.run(
            _seed_run(
                settings,
                run_id=older_id,
                status=RunStatus.DONE,
                name="older done",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=newer_id,
                status=RunStatus.DONE,
                name="newer done",
                created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=failed_id,
                status=RunStatus.FAILED,
                name="failed run",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            filtered = client.get("/runs?status=done&sort=created_at&order=asc")

        assert filtered.status_code == 200
        assert [row["id"] for row in filtered.json()] == [older_id, newer_id]
        assert all(row["status"] == "done" for row in filtered.json())
        _assert_no_sensitive_public_fields(filtered.text)


def test_list_runs_sorts_by_disk_usage_and_caps_limit() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        ids = [str(uuid4()) for _ in range(3)]
        for offset, run_id in enumerate(ids):
            asyncio.run(
                _seed_run(
                    settings,
                    run_id=run_id,
                    status=RunStatus.DONE,
                    name=f"run-{offset}",
                    disk_usage_bytes=(offset + 1) * 100,
                    output_file_count=offset + 1,
                    last_disk_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=offset),
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=offset),
                )
            )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            sorted_response = client.get("/runs?sort=disk_usage_bytes&order=desc&limit=500")

        assert sorted_response.status_code == 200
        body = sorted_response.json()
        assert [row["disk_usage_bytes"] for row in body] == [300, 200, 100]
        assert len(body) == 3
        _assert_no_sensitive_public_fields(sorted_response.text)


def test_list_runs_rejects_invalid_sort_and_order() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        asyncio.run(_seed_run(settings, run_id=str(uuid4()), status=RunStatus.DONE, name="single"))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            bad_sort = client.get("/runs?sort=latitude")
            bad_order = client.get("/runs?order=sideways")

        assert bad_sort.status_code == 400
        assert bad_sort.json() == {
            "error": "invalid_runs_query",
            "message": "Run query is invalid.",
        }
        assert bad_order.status_code == 400
        assert bad_order.json() == {
            "error": "invalid_runs_query",
            "message": "Run query is invalid.",
        }
        _assert_no_sensitive_public_fields(bad_sort.text)
        _assert_no_sensitive_public_fields(bad_order.text)


def test_cleanup_summary_returns_safe_storage_health_and_recommendations() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        large_done_id = str(uuid4())
        old_done_id = str(uuid4())
        stale_id = str(uuid4())
        active_id = str(uuid4())
        asyncio.run(
            _seed_run(
                settings,
                run_id=large_done_id,
                status=RunStatus.DONE,
                name="largest done",
                created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
                disk_usage_bytes=8_000_000_000,
                output_file_count=50,
                last_disk_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=old_done_id,
                status=RunStatus.FAILED,
                name="oldest terminal",
                created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
                disk_usage_bytes=1_500_000_000,
                output_file_count=20,
                last_disk_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=stale_id,
                status=RunStatus.STALE_FAILED,
                name="stale failed run",
                created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
                disk_usage_bytes=1_200_000_000,
                output_file_count=12,
                last_disk_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(
            _seed_run(
                settings,
                run_id=active_id,
                status=RunStatus.QUEUED,
                name="active run",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                disk_usage_bytes=500_000_000,
                output_file_count=4,
                last_disk_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        asyncio.run(_seed_deletion_audit_record(settings, run_name="deleted one", freed_bytes=321))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/cleanup-summary")

        assert response.status_code == 200
        body = response.json()
        assert body["total_runs"] == 4
        assert body["terminal_runs_count"] == 3
        assert body["active_runs_count"] == 1
        assert body["deleted_runs_count"] == 1
        assert body["total_freed_bytes"] == 321
        assert body["threshold_bytes"] == 10 * 1024 * 1024 * 1024
        assert body["total_disk_usage_bytes"] == 11_200_000_000
        assert body["cleanup_recommended"] is True
        assert body["warning_reason"] == "Stored runs exceed cleanup threshold."
        assert [row["id"] for row in body["largest_runs"]] == [large_done_id, old_done_id, stale_id]
        assert [row["id"] for row in body["oldest_terminal_runs"]] == [old_done_id, large_done_id, stale_id]
        assert [row["id"] for row in body["stale_failed_runs"]] == [stale_id]
        assert all(row["status"] != "running" for row in body["largest_runs"])
        _assert_no_sensitive_public_fields(response.text)


def test_cleanup_summary_recommends_review_for_large_stale_failed_runs_below_total_threshold() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        stale_id = str(uuid4())
        asyncio.run(
            _seed_run(
                settings,
                run_id=stale_id,
                status=RunStatus.STALE_FAILED,
                name="large stale",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                disk_usage_bytes=1_500_000_000,
                output_file_count=10,
                last_disk_scan_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/runs/cleanup-summary")

        assert response.status_code == 200
        body = response.json()
        assert body["cleanup_recommended"] is True
        assert body["warning_reason"] == "Large stale failed runs should be reviewed."
        assert body["total_disk_usage_bytes"] == 1_500_000_000
        assert [row["id"] for row in body["stale_failed_runs"]] == [stale_id]
        _assert_no_sensitive_public_fields(response.text)


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")


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
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
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


async def _seed_run(
    settings: Settings,
    *,
    run_id: str,
    status: RunStatus,
    name: str,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    disk_usage_bytes: int | None = None,
    output_file_count: int | None = None,
    last_disk_scan_at: datetime | None = None,
) -> None:
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
                created_at=created_at or datetime.now(timezone.utc),
                updated_at=updated_at or created_at or datetime.now(timezone.utc),
                disk_usage_bytes=disk_usage_bytes,
                output_file_count=output_file_count,
                last_disk_scan_at=last_disk_scan_at,
            )
        )
        await session.commit()
    await engine.dispose()


async def _seed_deletion_audit_record(settings: Settings, *, run_name: str, freed_bytes: int) -> None:
    from app.db.models import RunDeletionAudit

    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            RunDeletionAudit(
                run_id=str(uuid4()),
                run_name=run_name,
                deleted_at=datetime.now(timezone.utc),
                deleted_files_count=2,
                deleted_dirs_count=1,
                freed_bytes=freed_bytes,
                status="deleted",
                message="Run deleted.",
            )
        )
        await session.commit()
    await engine.dispose()


async def _noop_startup_active_run_recovery(session: AsyncSession) -> int:
    del session
    return 0


async def _allow_active_run_precheck(session: AsyncSession) -> None:
    del session


async def _failing_run_core_pipeline(*, run_id: str, settings: Settings, grid_spec_override=None) -> None:
    del grid_spec_override
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        assert run is not None
        run.status = RunStatus.FAILED
        await session.commit()
    await engine.dispose()
    raise RuntimeError("Synthetic pipeline failure for response-chain coverage.")


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _assert_no_sensitive_public_fields(text: str) -> None:
    lowered = text.casefold()
    for forbidden in ("latitude", "longitude", "geometry", "bounds", "transform", "sha256", "relative_path", "path"):
        assert forbidden not in lowered
