from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app.config import Settings
from app.services.redaction import verify_redacted
from app.services.v6_app_flow import (
    V6_PRIVATE_INPUT_RELATIVE_PATH,
    V6PrivatePackageAccessContext,
    generate_private_v6_package,
    resolve_private_v6_package_download,
    review_private_v6_package,
)
from app.services.v6_package_observability import (
    LOGGER_NAME,
    assert_safe_v6_observation_payload,
    get_v6_package_flow_counters_snapshot,
    reset_v6_package_flow_counters_for_tests,
)
from app.services.v6_real_gee_runtime import V6AoiBounds
from app.services.v6_real_package import V6RealPackageInputs
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import V6RequestZone


FORBIDDEN_LOG_FRAGMENTS = (
    "authorization",
    "access_token",
    "bearer",
    "candidate_rows",
    "feature_rows",
    "scored_candidates",
    "request_zones",
    "spatial_payload",
    "geometry",
    "coordinates",
    "bounds",
    "bbox",
    "zip_path",
    "package_path",
    "input_path",
    "output_dir",
    "provider_credentials",
)


def _settings(root: Path, *, enabled: bool = True) -> Settings:
    return Settings(
        data_dir=root,
        database_path=root / "test.db",
        v6_package_flow_enabled=enabled,
        operator_auth_trusted_proxy_enabled=True,
        operator_run_authorizations={"operator-1": ["run-1"]},
    )


def _access(*, authenticated: bool = True, roles: tuple[str, ...] = ("operator",)) -> V6PrivatePackageAccessContext:
    return V6PrivatePackageAccessContext(
        actor_id="operator-1",
        is_authenticated=authenticated,
        roles=roles,
        authorized_run_ids=(),
        request_id="req_observe",
    )


def _candidate(cell_id: str, rank: int) -> V6ScoredCandidate:
    return V6ScoredCandidate(
        cell_id=cell_id,
        candidate_score=0.85,
        remote_sensing_contrast=0.6,
        s2_confidence=1.0,
        builtup_warning=0,
        cropland_heavy_warning=0,
        water_edge_warning=0,
        modern_linear_edge_warning=0,
        v6_building_warning=0,
        v6_road_like_warning=0,
        false_positive_warning_count=0,
        v6_false_positive_warning_count=0,
        v6_false_positive_penalty=0.0,
        v6_quality_adjusted_score=0.85,
        v6_no_warning_bonus=1.0,
        v6_review_priority_score=0.85,
        final_priority_rank_v6=rank,
    )


def _package_inputs() -> V6RealPackageInputs:
    zones = (
        V6RequestZone(
            "V6_RZ_001",
            "V6_CELL_R001_C001",
            "V6_QUOTE_001",
            1,
            0.85,
            0,
            V6AoiBounds(0, 10, 1, 11),
        ),
    )
    return V6RealPackageInputs(
        run_id="REAL_RUN_FIXTURE_001",
        timestamp="20260103T010203Z",
        scored_candidates=(_candidate("V6_CELL_R001_C001", 1),),
        request_zones=zones,
    )


def _touch_input_file(settings: Settings, run_id: str = "run-1") -> None:
    input_file = settings.data_dir / "runs" / run_id / V6_PRIVATE_INPUT_RELATIVE_PATH
    input_file.parent.mkdir(parents=True, exist_ok=True)
    input_file.write_text("{}", encoding="utf-8")


def setup_function() -> None:
    reset_v6_package_flow_counters_for_tests()


def test_generate_records_safe_metadata_counter_and_log(tmp_path: Path, monkeypatch, caplog) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        result = generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 200
    assert result.body["outcome"] == "generated"
    assert result.body["warning_count"] == 0
    verify_redacted(result.body)

    snapshot = get_v6_package_flow_counters_snapshot()
    assert snapshot["action|generate|generated"] == 1
    assert snapshot["status|generate|200"] == 1
    assert snapshot["rollback_state|enabled|generated"] == 1

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "v6_package_flow_event" in log_text
    assert '"action":"generate"' in log_text
    assert '"payload_count":' in log_text
    assert '"zip_entry_count":' in log_text
    for forbidden in FORBIDDEN_LOG_FRAGMENTS:
        assert forbidden not in log_text.lower()


def test_review_and_retrieve_record_safe_metadata_counters(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())
    generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    review_result = review_private_v6_package(settings=settings, run_id="run-1", access_context=_access())
    retrieve_result = resolve_private_v6_package_download(settings=settings, run_id="run-1", access_context=_access())

    assert review_result.status_code == 200
    assert review_result.body["outcome"] == "available"
    assert retrieve_result.status_code == 200
    assert retrieve_result.file_path is not None

    snapshot = get_v6_package_flow_counters_snapshot()
    assert snapshot["action|generate|generated"] == 1
    assert snapshot["action|review|available"] == 1
    assert snapshot["action|retrieve|available"] == 1
    assert snapshot["status|retrieve|200"] == 1


def test_disabled_package_flow_records_denied_and_rollback_disabled_without_reading_inputs(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=False)

    result = review_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 403
    assert result.body["outcome"] == "denied"
    verify_redacted(result.body)
    assert not (settings.data_dir / "runs" / "run-1" / V6_PRIVATE_INPUT_RELATIVE_PATH).exists()

    snapshot = get_v6_package_flow_counters_snapshot()
    assert snapshot["action|review|denied"] == 1
    assert snapshot["status|review|403"] == 1
    assert snapshot["rollback_state|disabled|denied"] == 1
    assert snapshot["denied|package_flow_disabled|review"] == 1


def test_missing_operator_role_records_safe_denial_reason(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    result = generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access(roles=("viewer",)))

    assert result.status_code == 403
    assert result.body["outcome"] == "denied"

    snapshot = get_v6_package_flow_counters_snapshot()
    assert snapshot["action|generate|denied"] == 1
    assert snapshot["denied|operator_role_missing|generate"] == 1


def test_observation_payload_guard_rejects_private_fields() -> None:
    with pytest.raises(ValueError):
        assert_safe_v6_observation_payload({"candidate_rows": []})
    with pytest.raises(ValueError):
        assert_safe_v6_observation_payload({"coordinates": [0, 0]})
    with pytest.raises(ValueError):
        assert_safe_v6_observation_payload({"authorization": "Bearer secret"})
