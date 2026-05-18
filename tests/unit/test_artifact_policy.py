from __future__ import annotations

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.schemas.artifact import ArtifactInternal
from app.services.artifact_policy import can_serve_artifact


def make_artifact(artifact_class: ArtifactClass, http_servable: bool = True) -> ArtifactInternal:
    return ArtifactInternal(
        run_id="run-1",
        name="artifact.txt",
        relative_path="artifact.txt",
        artifact_class=artifact_class,
        http_servable=http_servable,
    )


def test_filesystem_only_artifacts_are_never_served() -> None:
    decision = can_serve_artifact(make_artifact(ArtifactClass.FILESYSTEM_ONLY), Settings())
    assert decision.allow is False
    assert decision.reason == "class_iv_filesystem_only"


def test_local_sensitive_artifacts_are_blocked_under_network_bind() -> None:
    settings = Settings(allow_network_bind=True)
    decision = can_serve_artifact(make_artifact(ArtifactClass.LOCAL_SENSITIVE), settings)
    assert decision.allow is False
    assert decision.reason == "class_i_blocked_under_network_bind"


def test_non_http_servable_artifacts_are_blocked() -> None:
    decision = can_serve_artifact(
        make_artifact(ArtifactClass.REDACTED_PUBLIC, http_servable=False),
        Settings(),
    )
    assert decision.allow is False
    assert decision.reason == "artifact_not_http_servable"


def test_redacted_and_preview_artifacts_are_servable() -> None:
    for artifact_class in (ArtifactClass.REDACTED_PUBLIC, ArtifactClass.PREVIEW_ONLY):
        decision = can_serve_artifact(make_artifact(artifact_class), Settings())
        assert decision.allow is True
        assert decision.reason == "ok"
