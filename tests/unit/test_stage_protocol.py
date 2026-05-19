from __future__ import annotations

import pytest

from app.db.models.enums import ArtifactClass
from app.errors import ArtifactClassError
from app.pipeline._base import build_stage_artifact


def test_build_stage_artifact_requires_artifact_class() -> None:
    with pytest.raises(ArtifactClassError):
        build_stage_artifact(
            name="artifact",
            relative_path="artifact.bin",
            artifact_class=None,
        )


def test_build_stage_artifact_returns_artifact() -> None:
    artifact = build_stage_artifact(
        name="artifact",
        relative_path="artifact.bin",
        artifact_class=ArtifactClass.LOCAL_SENSITIVE,
    )

    assert artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE
