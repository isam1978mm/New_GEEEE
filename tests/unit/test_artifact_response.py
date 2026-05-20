from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import ArtifactServeViolation
from app.services.storage import resolve_run_artifact_path


def test_resolve_run_artifact_path_blocks_parent_traversal_backslash(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "..\\escape.txt")


def test_resolve_run_artifact_path_blocks_parent_traversal_forward_slash(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "../escape.txt")


def test_resolve_run_artifact_path_blocks_normalized_parent_traversal(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "data/../data/db.sqlite")


def test_resolve_run_artifact_path_blocks_absolute_posix_path(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "/tmp/artifact.csv")


def test_resolve_run_artifact_path_blocks_windows_drive_path(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "C:\\temp\\artifact.csv")


def test_resolve_run_artifact_path_accepts_safe_nested_relative_path(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    expected = (tmp_path / "data" / "runs" / "run-1" / "subdir" / "artifact.csv").resolve()

    actual = resolve_run_artifact_path(settings, "run-1", "subdir/artifact.csv")

    assert actual == expected
