from __future__ import annotations

import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import app.services.operator_overlay_preview as service_module
from app.config import Settings
from app.pipeline.parity.manifest import ParityPathError
from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
)
from app.pipeline.parity.private_map_artifact_writers import (
    write_private_geojson_feature_collection,
    write_private_heatmap_json,
    write_private_kmz_points,
)
from app.services.operator_overlay_preview import (
    build_operator_overlay_preview,
    _safe_run_relative_path,
)
from app.services.storage import get_run_dir


_RUN_ID = "run_authorized"
_SENSITIVE_KEYS = (
    "exact_coordinates",
    "raw_geometry",
    "kml_contents",
    "heatmap_point_payloads",
    "local_paths",
    "local_filesystem_paths",
    "private_hashes",
    "artifact_contents",
    "download_urls",
    "coordinates",
    "geometry",
    "bounds",
)


def _settings(root: Path, *, enabled: bool) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "db.sqlite",
        operator_private_overlay_preview_enabled=enabled,
    )


def _write_artifacts(settings: Settings, run_id: str = _RUN_ID) -> None:
    run_dir = get_run_dir(settings, run_id)
    write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=[
            {
                "type": "Feature",
                "properties": {"class_label": "Class_1"},
                "geometry": {"type": "Point", "coordinates": [36.1, 35.2]},
            }
        ],
    )
    write_private_kmz_points(
        run_dir=run_dir,
        points=[{"id": "p1", "latitude": 35.2, "longitude": 36.1}],
    )
    write_private_heatmap_json(
        run_dir=run_dir,
        points=[{"id": "h1", "latitude": 35.2, "longitude": 36.1, "weight": 0.5}],
    )


def _call(
    settings: Settings,
    *,
    run_id: str = _RUN_ID,
    artifact_family: str = PHASE_D1_GEOJSON_FAMILY_ID,
    access_mode: str = "operator_only_preview",
    actor_id: str | None = "operator_1",
    is_authenticated: bool = True,
    roles=("operator",),
    authorized_run_ids=(_RUN_ID,),
    request_id: str = "req_1",
):
    return build_operator_overlay_preview(
        settings=settings,
        run_id=run_id,
        requested_artifact_family=artifact_family,
        requested_access_mode=access_mode,
        actor_id=actor_id,
        is_authenticated=is_authenticated,
        roles=roles,
        authorized_run_ids=authorized_run_ids,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# Access gates
# ---------------------------------------------------------------------------
def test_default_off_denies_access() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=False)
        _write_artifacts(settings)
        result = _call(settings)
    assert result.allowed is False
    assert result.status_code == 403
    assert result.decision_status == "denied_default_off"
    assert result.body["outcome"] == "denied"


def test_unauthenticated_actor_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, is_authenticated=False)
    assert result.allowed is False
    assert result.decision_status == "denied_unauthenticated"


def test_non_operator_actor_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, roles=("viewer",))
    assert result.allowed is False
    assert result.decision_status == "denied_missing_operator_role"


def test_unauthorized_run_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, authorized_run_ids=("other_run",))
    assert result.allowed is False
    assert result.decision_status == "denied_run_not_authorized"


def test_unsupported_artifact_family_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, artifact_family="public_overlay_any")
    assert result.allowed is False
    assert result.decision_status == "denied_unsupported_artifact_family"


def test_redacted_public_mode_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, access_mode="redacted_public")
    assert result.allowed is False
    assert result.decision_status == "denied_public_exposure_blocked"


def test_public_exact_coordinate_mode_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, access_mode="public_exact_coordinate")
    assert result.allowed is False
    assert result.decision_status == "denied_public_exposure_blocked"


def test_valid_operator_only_preview_allowed_when_all_gates_pass() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings)
    assert result.allowed is True
    assert result.status_code == 200
    assert result.decision_status == "allowed_operator_preview"
    assert result.body["outcome"] == "allowed"
    assert result.body["item_count"] == 1
    assert result.body["preview_type"] == "geojson_feature_collection"
    assert result.body["filesystem_only"] is True
    assert result.body["http_servable"] is False
    assert result.body["downloadable_via_api"] is False
    assert result.body["frontend_visible"] == "operator_only"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
def test_every_decision_builds_audit_event() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        allowed = _call(settings)
        denied = _call(settings, is_authenticated=False)
    for result in (allowed, denied):
        event = result.audit_event
        for required in (
            "event_type",
            "actor_id",
            "run_id",
            "artifact_family",
            "access_mode",
            "access_outcome",
            "timestamp",
            "reason_code",
            "request_id",
            "client_context_redacted",
        ):
            assert required in event
        for key in _SENSITIVE_KEYS:
            assert key not in event


# ---------------------------------------------------------------------------
# Denial redaction
# ---------------------------------------------------------------------------
def test_denial_response_does_not_reveal_artifact_existence_or_sensitive_fields() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, authorized_run_ids=("other_run",))
    body = result.body
    assert set(body) == {
        "outcome",
        "status",
        "reason_code",
        "request_id",
        "message",
        "retry_allowed",
        "support_reference",
    }
    for key in (*_SENSITIVE_KEYS, "run_id", "artifact_family", "preview_payload", "item_count"):
        assert key not in body
    serialized = json.dumps(body).lower()
    assert "geojson" not in serialized
    assert "kmz" not in serialized
    assert ".npy" not in serialized


def test_denial_is_identical_whether_or_not_artifact_exists() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        with_artifact = _call(settings, is_authenticated=False, request_id="r")
    with TemporaryDirectory() as temp_dir2:
        settings2 = _settings(Path(temp_dir2), enabled=True)
        # no artifacts written
        without_artifact = _call(settings2, is_authenticated=False, request_id="r")
    assert with_artifact.body == without_artifact.body


# ---------------------------------------------------------------------------
# Preview reads / path safety / not_available
# ---------------------------------------------------------------------------
def test_authorized_geojson_preview_reads_only_under_run_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, artifact_family=PHASE_D1_GEOJSON_FAMILY_ID)
    payload = result.body["preview_payload"]
    assert payload["feature_count"] == 1
    assert payload["feature_kinds"] == ["Point"]
    _assert_no_path_or_url(result.body, settings)


def test_authorized_kmz_preview_reads_only_under_run_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, artifact_family=PHASE_D2_KMZ_FAMILY_ID)
    assert result.body["preview_type"] == "kmz_placemarks"
    assert result.body["preview_payload"]["placemark_count"] == 1
    _assert_no_path_or_url(result.body, settings)


def test_authorized_heatmap_preview_reads_only_under_run_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _write_artifacts(settings)
        result = _call(settings, artifact_family=PHASE_D3_HEATMAP_FAMILY_ID)
    payload = result.body["preview_payload"]
    assert payload["point_count"] == 1
    assert "weight_summary" in payload
    _assert_no_path_or_url(result.body, settings)


def test_authorized_missing_artifact_returns_not_available() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        # no artifacts written, but operator is fully authorized
        result = _call(settings, artifact_family=PHASE_D1_GEOJSON_FAMILY_ID)
    assert result.allowed is True
    assert result.status_code == 200
    assert result.body["outcome"] == "not_available"
    assert result.body["item_count"] is None
    assert result.body["preview_payload"] is None


def test_missing_artifact_does_not_leak_to_unauthorized_actor() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        # no artifacts; unauthorized actor must get a generic denial, not not_available
        result = _call(settings, is_authenticated=False)
    assert result.allowed is False
    assert result.body["outcome"] == "denied"
    assert "not_available" not in json.dumps(result.body)


def test_path_traversal_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        with pytest.raises(ParityPathError):
            _safe_run_relative_path(run_dir, "../../etc/passwd")
        with pytest.raises(ParityPathError):
            _safe_run_relative_path(run_dir, "/etc/passwd")


def _assert_no_path_or_url(body: dict, settings: Settings) -> None:
    serialized = json.dumps(body)
    assert str(settings.data_dir) not in serialized
    lowered = serialized.lower()
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "/runs/" not in lowered
    assert "/artifacts/" not in lowered
    assert "download_url" not in lowered
    assert "/download/" not in lowered
    # The safety flag downloadable_via_api must be present and false.
    assert body["downloadable_via_api"] is False


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------
def test_service_adds_no_earth_engine_or_orchestrator_hooks() -> None:
    source = inspect.getsource(service_module)
    lowered = source.lower()
    assert "import ee" not in source
    assert "ee.Authenticate" not in source
    assert "earthengine" not in lowered
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "google.colab" not in source
