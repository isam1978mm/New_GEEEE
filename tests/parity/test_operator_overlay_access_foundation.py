from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import app.pipeline.parity.operator_overlay_access_foundation as module
from app.pipeline.parity.operator_overlay_access_foundation import (
    ALLOWED_ACCESS_DECISION_STATUSES,
    FUTURE_SLICE_11_G2_SCHEMA_VERSION,
    OPERATOR_ROLE,
    OverlayAccessRequest,
    build_audit_event,
    build_redacted_denial_response,
    evaluate_overlay_access,
    get_operator_overlay_access_foundation_policy,
    write_future_slice_11_g2_auth_role_audit_foundation_report,
)
from app.pipeline.parity.operator_overlay_implementation_design import (
    ALLOWED_ACCESS_MODE,
    ALLOWED_ARTIFACT_FAMILIES,
    BLOCKED_PUBLIC_EXPOSURE_MODES,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
    ".jsonl",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
    ".parquet",
}

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
)


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig" + " target",
        "def" + "initely",
        "disc" + "overy",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def _wording_violation(content: str, term: str) -> bool:
    if " " in term:
        return term in content
    return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", content) is not None


def _valid_request(**overrides) -> OverlayAccessRequest:
    base = {
        "actor_id": "operator_1",
        "is_authenticated": True,
        "roles": (OPERATOR_ROLE,),
        "run_id": "run_authorized",
        "requested_artifact_family": ALLOWED_ARTIFACT_FAMILIES[0],
        "requested_access_mode": ALLOWED_ACCESS_MODE,
        "operator_overlay_preview_enabled": True,
        "request_id": "req_1",
        "authorized_run_ids": ("run_authorized",),
    }
    base.update(overrides)
    return OverlayAccessRequest(**base)


# ---------------------------------------------------------------------------
# Access decisions
# ---------------------------------------------------------------------------
def test_default_off_config_denies_access() -> None:
    decision = evaluate_overlay_access(_valid_request(operator_overlay_preview_enabled=False))
    assert decision.allowed is False
    assert decision.status == "denied_default_off"


def test_unauthenticated_actor_is_denied() -> None:
    decision = evaluate_overlay_access(_valid_request(is_authenticated=False))
    assert decision.allowed is False
    assert decision.status == "denied_unauthenticated"


def test_actor_without_operator_role_is_denied() -> None:
    decision = evaluate_overlay_access(_valid_request(roles=("viewer", "analyst")))
    assert decision.allowed is False
    assert decision.status == "denied_missing_operator_role"


def test_actor_without_per_run_authorization_is_denied() -> None:
    decision = evaluate_overlay_access(_valid_request(authorized_run_ids=("other_run",)))
    assert decision.allowed is False
    assert decision.status == "denied_run_not_authorized"

    decision_cb = evaluate_overlay_access(
        _valid_request(authorized_run_ids=None, authorization_result=False)
    )
    assert decision_cb.status == "denied_run_not_authorized"


def test_unsupported_artifact_family_is_denied() -> None:
    decision = evaluate_overlay_access(
        _valid_request(requested_artifact_family="public_overlay_any")
    )
    assert decision.allowed is False
    assert decision.status == "denied_unsupported_artifact_family"


def test_redacted_public_mode_is_denied() -> None:
    decision = evaluate_overlay_access(
        _valid_request(requested_access_mode="redacted_public")
    )
    assert decision.allowed is False
    assert decision.status == "denied_public_exposure_blocked"


def test_public_exact_coordinate_mode_is_denied() -> None:
    decision = evaluate_overlay_access(
        _valid_request(requested_access_mode="public_exact_coordinate")
    )
    assert decision.allowed is False
    assert decision.status == "denied_public_exposure_blocked"


def test_unknown_mode_is_denied_as_unsupported() -> None:
    decision = evaluate_overlay_access(
        _valid_request(requested_access_mode="some_unknown_mode")
    )
    assert decision.allowed is False
    assert decision.status == "denied_unsupported_access_mode"


def test_valid_operator_only_preview_request_is_allowed_when_all_gates_pass() -> None:
    decision = evaluate_overlay_access(_valid_request())
    assert decision.allowed is True
    assert decision.status == "allowed_operator_preview"
    assert decision.redacted_denial is None
    assert decision.public_exposure_changes is False
    assert decision.artifact_serving_changes is False


def test_allowed_via_authorization_result_callback_value() -> None:
    decision = evaluate_overlay_access(
        _valid_request(authorized_run_ids=None, authorization_result=True)
    )
    assert decision.allowed is True
    assert decision.status == "allowed_operator_preview"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
def test_every_access_decision_requires_audit() -> None:
    for request in (
        _valid_request(),
        _valid_request(is_authenticated=False),
        _valid_request(operator_overlay_preview_enabled=False),
        _valid_request(requested_access_mode="redacted_public"),
    ):
        decision = evaluate_overlay_access(request)
        assert decision.audit_required is True


def test_audit_event_includes_required_safe_fields_and_excludes_sensitive_fields() -> None:
    decision = evaluate_overlay_access(_valid_request())
    event = build_audit_event(decision, actor_id="operator_1")

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
    serialized = json.dumps(event)
    assert "coordinates" not in serialized.lower()


def test_audit_event_records_denied_outcome() -> None:
    decision = evaluate_overlay_access(_valid_request(is_authenticated=False))
    event = build_audit_event(decision, actor_id=None)
    assert event["access_outcome"] == "denied"
    assert event["actor_id"] == "anonymous"


# ---------------------------------------------------------------------------
# Redacted denial response
# ---------------------------------------------------------------------------
def test_redacted_denial_response_excludes_sensitive_fields_and_existence() -> None:
    decision = evaluate_overlay_access(_valid_request(authorized_run_ids=("other_run",)))
    response = build_redacted_denial_response(decision)

    assert set(response) == {
        "status",
        "reason_code",
        "request_id",
        "message",
        "retry_allowed",
        "support_reference",
    }
    for key in (*_SENSITIVE_KEYS, "private_artifact_existence", "file_names", "artifact_family", "run_id"):
        assert key not in response
    serialized = json.dumps(response).lower()
    assert "coordinates" not in serialized
    assert "geometry" not in serialized
    assert "kml" not in serialized
    assert ".geojson" not in serialized
    assert ".kmz" not in serialized


def test_redacted_denial_is_identical_across_denial_causes() -> None:
    causes = (
        _valid_request(operator_overlay_preview_enabled=False),
        _valid_request(is_authenticated=False),
        _valid_request(authorized_run_ids=("other_run",)),
        _valid_request(requested_artifact_family="public_overlay_any"),
    )
    bodies = []
    for request in causes:
        decision = evaluate_overlay_access(request)
        body = dict(build_redacted_denial_response(decision))
        body.pop("request_id")
        bodies.append(body)
    assert all(body == bodies[0] for body in bodies)


def test_allowed_decision_has_no_denial_body() -> None:
    decision = evaluate_overlay_access(_valid_request())
    try:
        build_redacted_denial_response(decision)
    except ValueError:
        return
    raise AssertionError("expected ValueError for an allowed decision")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def test_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_future_slice_11_g2_auth_role_audit_foundation_report(
        run_dir=run_dir,
        run_id="future-slice-11",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == (
        run_dir / "manifests" / "future_slice_11_g2_auth_role_audit_foundation.json"
    )
    assert report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == FUTURE_SLICE_11_G2_SCHEMA_VERSION
    assert payload["foundation_id"] == "future_slice_11_g2_auth_role_audit_foundation"
    assert payload["g2_auth_role_audit_foundation_only"] is True
    assert payload["api_route_added"] is False
    assert payload["frontend_ui_added"] is False
    assert payload["overlay_runtime_added"] is False
    assert payload["artifact_serving_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["artifact_generation"] is False
    assert payload["allowed_access_modes"] == [ALLOWED_ACCESS_MODE]
    assert set(BLOCKED_PUBLIC_EXPOSURE_MODES) <= set(payload["denied_access_modes"])
    assert set(payload["counts_by_status"]) == ALLOWED_ACCESS_DECISION_STATUSES
    required_fields = {
        "schema_version",
        "run_id",
        "created_at",
        "foundation_id",
        "allowed_artifact_families",
        "allowed_access_modes",
        "denied_access_modes",
        "decision_policy",
        "redacted_denial_policy",
        "audit_policy",
        "sample_decisions",
        "counts_by_status",
        "notes",
    }
    assert required_fields <= set(payload)
    # The default sample set includes one allowed and several denied decisions.
    assert payload["counts_by_status"]["allowed_operator_preview"] == 1


def test_report_creates_no_map_coordinate_or_artifact_files(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_future_slice_11_g2_auth_role_audit_foundation_report(
        run_dir=run_dir,
        run_id="future-slice-11-no-artifacts",
    )
    created = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_policy_exposes_decision_redaction_and_audit_sections() -> None:
    policy = get_operator_overlay_access_foundation_policy()
    assert policy["operator_role_required"] == "operator"
    assert policy["default_off_required"] is True
    assert policy["allowed_access_modes"] == [ALLOWED_ACCESS_MODE]
    assert "exact_coordinates" in policy["audit_policy"]["forbidden_fields"]
    assert "artifact_contents" in policy["audit_policy"]["forbidden_fields"]
    assert policy["redacted_denial_policy"]["must_not_reveal_artifact_existence"] is True


# ---------------------------------------------------------------------------
# Safety boundaries
# ---------------------------------------------------------------------------
def test_module_adds_no_route_artifact_read_or_earth_engine_hooks() -> None:
    source = inspect.getsource(module)
    lowered = source.lower()

    assert "APIRouter" not in source
    assert "FastAPI" not in source
    assert "BackgroundTasks" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "add_api_route" not in source
    assert "open(" not in source
    assert ".read_bytes(" not in source
    assert "np.load" not in source
    assert "zipfile" not in lowered
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "import ee" not in source
    assert "ee.Authenticate" not in source
    assert "earthengine" not in lowered
    assert "google.colab" not in source
    assert "drive.mount" not in source


def test_no_api_or_frontend_or_serving_files_reference_this_slice() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for relative in ("app/api", "app/main.py"):
        path = repo_root / relative
        files = path.rglob("*.py") if path.is_dir() else [path]
        for file_path in files:
            if not file_path.is_file():
                continue
            text = file_path.read_text(encoding="utf-8")
            assert "operator_overlay_access_foundation" not in text
            assert "operator/private-overlays" not in text


def test_doc_and_module_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/operator_overlay_access_foundation.py"),
        Path("docs/FUTURE_SLICE_11_G2_AUTH_ROLE_AUDIT_FOUNDATION.md"),
    )
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in paths if path.exists()
    )
    assert all(not _wording_violation(combined, term) for term in _claim_terms())
