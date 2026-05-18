from __future__ import annotations

from app.config import Settings
from app.pipeline.manifest import save_grid_manifest, save_stage_manifest
from app.services.grid import build_grid_manifest
from app.services.storage import get_redacted_cache_dir, initialize_run_storage, read_manifest


def test_initialize_run_storage_creates_run_and_redacted_dirs(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    run_dir = initialize_run_storage(settings, "run-1")

    assert run_dir.exists()
    assert get_redacted_cache_dir(settings, "run-1").exists()


def test_save_grid_manifest_persists_internal_grid_manifest(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    grid_manifest = build_grid_manifest(43.6532, -79.3832)

    manifest_path = save_grid_manifest(settings, "run-1", grid_manifest)

    manifest = read_manifest(manifest_path)
    assert manifest["crs_family"] == "utm"
    assert manifest["epsg"] == grid_manifest.epsg


def test_save_stage_manifest_marks_manifest_local_sensitive(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")

    manifest_path = save_stage_manifest(
        settings,
        "run-1",
        "dem",
        {"status": "done"},
    )

    manifest = read_manifest(manifest_path)
    assert manifest["artifact_class"] == "LOCAL_SENSITIVE"
    assert manifest["stage_name"] == "dem"
    assert manifest["status"] == "done"
