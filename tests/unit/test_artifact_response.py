from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import ArtifactServeViolation
from app.services.storage import resolve_run_artifact_path


def test_resolve_run_artifact_path_blocks_parent_traversal(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    with pytest.raises(ArtifactServeViolation):
        resolve_run_artifact_path(settings, "run-1", "..\\escape.txt")
