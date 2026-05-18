from __future__ import annotations

from app.db.models import Artifact, ArtifactClass, Run, RunStatus


def test_run_model_has_internal_coordinate_fields_and_status_enum() -> None:
    assert Run.__table__.c.latitude.nullable is False
    assert Run.__table__.c.longitude.nullable is False
    assert Run.__table__.c.status.nullable is False
    assert RunStatus.QUEUED.value == "queued"


def test_artifact_model_has_required_persistence_fields() -> None:
    columns = Artifact.__table__.c
    assert columns.relative_path.nullable is False
    assert columns.size_bytes.nullable is False
    assert columns.artifact_class.nullable is False
    assert columns.http_servable.nullable is False
    assert ArtifactClass.FILESYSTEM_ONLY.value == "FILESYSTEM_ONLY"
