from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.services.redaction import verify_redacted
from app.services.v6_app_flow import (
    V6_PRIVATE_INPUT_RELATIVE_PATH,
    V6_PRIVATE_PACKAGE_RELATIVE_DIR,
    V6PrivatePackageAccessContext,
    generate_private_v6_package,
    resolve_private_v6_package_download,
    review_private_v6_package,
)
from app.services.v6_real_gee_runtime import V6AoiBounds
from app.services.v6_real_package import V6RealPackageInputs
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import V6RequestZone


def _settings(root: Path, *, enabled: bool = True) -> Settings:
    return Settings(
        data_dir=root,
        database_path=root / "test.db",
        v6_package_flow_enabled=enabled,
        operator_auth_trusted_proxy_enabled=True,
        operator_run_authorizations={"operator-1": ["run-1"]},
    )


def _access(*, roles: tuple[str, ...] = ("operator",)) -> V6PrivatePackageAccessContext:
    return V6PrivatePackageAccessContext(
        actor_id="operator-1",
        is_authenticated=True,
        roles=roles,
        authorized_run_ids=(),
        request_id="req_test",
    )


def _candidate(cell_id: str, rank: int, *, score: float = 0.75, warnings: int = 0) -> V6ScoredCandidate:
    return V6ScoredCandidate(
        cell_id=cell_id,
        candidate_score=score,
        remote_sensing_contrast=0.6,
        s2_confidence=1.0,
        builtup_warning=0,
        cropland_heavy_warning=0,
        water_edge_warning=0,
        modern_linear_edge_warning=0,
        v6_building_warning=0,
        v6_road_like_warning=0,
        false_positive_warning_count=warnings,
        v6_false_positive_warning_count=warnings,
        v6_false_positive_penalty=warnings * 0.07,
        v6_quality_adjusted_score=score,
        v6_no_warning_bonus=1.0 if warnings == 0 else 0.5,
        v6_review_priority_score=score,
        final_priority_rank_v6=rank,
    )


def _package_inputs() -> V6RealPackageInputs:
    candidates = (
        _candidate("V6_CELL_R001_C001", 1, score=0.91),
        _candidate("V6_CELL_R001_C002", 2, score=0.72, warnings=1),
    )
    zone_shape = V6AoiBounds(0, 10, 1, 11)
    zones = (
        V6RequestZone("V6_RZ_001", "V6_CELL_R001_C001", "V6_QUOTE_001", 1, 0.91, 0, zone_shape),
        V6RequestZone("V6_RZ_002", "V6_CELL_R001_C002", "V6_QUOTE_002", 2, 0.72, 1, zone_shape),
    )
    return V6RealPackageInputs(
        run_id="REAL_RUN_FIXTURE_001",
        timestamp="20260103T010203Z",
        scored_candidates=candidates,
        request_zones=zones,
    )


def _touch_input_file(settings: Settings, run_id: str = "run-1") -> None:
    input_file = settings.data_dir / "runs" / run_id / V6_PRIVATE_INPUT_RELATIVE_PATH
    input_file.parent.mkdir(parents=True, exist_ok=True)
    input_file.write_text("{}", encoding="utf-8")


def _package_dir(settings: Settings, run_id: str = "run-1") -> Path:
    return settings.data_dir / "runs" / run_id / V6_PRIVATE_PACKAGE_RELATIVE_DIR


def test_generate_private_v6_package_writes_package_and_returns_safe_metadata(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())

    result = generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 200
    assert result.body["outcome"] == "generated"
    assert result.body["package_ready"] is True
    assert result.body["payload_count"] == 12
    assert result.body["generation_token"] == "20260103T010203Z"
    verify_redacted(result.body)
    output_dir = _package_dir(settings)
    assert (output_dir / "V6_REAL_GENERATED_20260103T010203Z.zip").is_file()


def test_review_private_v6_package_returns_safe_metadata_after_generate(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())
    generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    result = review_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 200
    assert result.body["outcome"] == "available"
    assert result.body["package_ready"] is True
    assert result.body["package_pair_verified"] is True
    assert result.body["generation_token"] == "20260103T010203Z"
    assert result.body["issue_count"] == 0
    verify_redacted(result.body)


def test_review_private_v6_package_blocks_invalid_validation_status(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())
    generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    report_path = _package_dir(settings) / "V6_REAL_GENERATED_validation_20260103T010203Z.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["validation_status"] = "invalid"
    report["issues"] = ["forced-invalid"]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    review = review_private_v6_package(settings=settings, run_id="run-1", access_context=_access())
    download = resolve_private_v6_package_download(settings=settings, run_id="run-1", access_context=_access())

    assert review.status_code == 200
    assert review.body["outcome"] == "not_available"
    assert review.body["package_ready"] is False
    assert review.body["package_pair_verified"] is False
    assert review.body["issue_count"] == 1
    assert download.file_path is None
    assert download.body["package_ready"] is False
    verify_redacted(review.body)


def test_review_private_v6_package_rejects_mismatched_zip_report_pair(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())
    generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    package_dir = _package_dir(settings)
    original_zip = package_dir / "V6_REAL_GENERATED_20260103T010203Z.zip"
    mismatched_zip = package_dir / "V6_REAL_GENERATED_20260104T010203Z.zip"
    mismatched_report = package_dir / "V6_REAL_GENERATED_validation_20260104T010203Z.json"
    mismatched_zip.write_bytes(original_zip.read_bytes())
    mismatched_report.write_text(
        json.dumps(
            {
                "validation_status": "generated_synthetic_package_verified",
                "zip_filename": "V6_REAL_GENERATED_20260103T010203Z.zip",
                "payload_count": 12,
                "zip_entry_count": 13,
                "category_counts": {},
                "issues": [],
            }
        ),
        encoding="utf-8",
    )

    review = review_private_v6_package(settings=settings, run_id="run-1", access_context=_access())
    download = resolve_private_v6_package_download(settings=settings, run_id="run-1", access_context=_access())

    assert review.body["generation_token"] == "20260104T010203Z"
    assert review.body["package_ready"] is False
    assert review.body["package_pair_verified"] is False
    assert review.body["zip_filename"] == "V6_REAL_GENERATED_20260104T010203Z.zip"
    assert download.file_path is None
    assert download.body["package_ready"] is False
    verify_redacted(review.body)


def test_resolve_private_v6_package_download_returns_file_only_after_generate(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)
    monkeypatch.setattr("app.services.v6_app_flow.load_v6_real_package_inputs", lambda _: _package_inputs())
    generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    result = resolve_private_v6_package_download(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 200
    assert result.body["package_ready"] is True
    assert result.body["package_pair_verified"] is True
    assert result.file_path is not None
    assert result.file_path.is_file()
    assert result.file_name == "V6_REAL_GENERATED_20260103T010203Z.zip"


def test_v6_package_flow_is_default_off_and_does_not_create_output(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=False)
    _touch_input_file(settings)

    result = generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access())

    assert result.status_code == 403
    assert result.body["outcome"] == "denied"
    verify_redacted(result.body)
    output_dir = _package_dir(settings)
    assert not output_dir.exists()


def test_v6_package_flow_requires_operator_role(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _touch_input_file(settings)

    result = generate_private_v6_package(settings=settings, run_id="run-1", access_context=_access(roles=("viewer",)))

    assert result.status_code == 403
    assert result.body["reason_code"] == "ACCESS_DENIED"
    verify_redacted(result.body)
