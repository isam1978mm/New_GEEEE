from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.h5_operator_summary import (
    H5OperatorSummaryError,
    assert_h5_operator_summary_is_redacted,
    load_h5_operator_aggregate_summary,
)


_PATH = "/operator/h5/aggregate-summary"


def _settings(root: Path, *, trusted_proxy_enabled: bool = True) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "gee_screening.db",
        operator_auth_trusted_proxy_enabled=trusted_proxy_enabled,
    )


def _operator_headers(*, roles: str = "operator", authenticated: bool = True) -> dict[str, str]:
    return {
        "X-Operator-Authenticated": "true" if authenticated else "false",
        "X-Operator-Id": "operator_1",
        "X-Operator-Roles": roles,
        "X-Request-Id": "req_h5_test",
    }


def _safe_summary() -> dict[str, object]:
    return {
        "status": "h4_private_offline_inference_completed",
        "pipeline_stage": "h5_operator_aggregate_summary",
        "feature_set_type": "real_i2_source_context_v1",
        "training_type": "h3_scientific_real_feature_baseline",
        "total_row_count": 868,
        "feature_matrix_rows": 868,
        "feature_column_count": 8,
        "score_min": 0.00004185,
        "score_max": 0.97847171,
        "score_mean": 0.2499092531797235,
        "rows_by_source": {"C05": 217, "C06": 217, "C07": 217, "POS-01": 217},
        "rows_by_split": {"holdout": 84, "test": 88, "train": 608, "val": 88},
        "score_band_counts": {},
        "score_band_counts_status": "not_available_from_aggregate_summary",
        "prediction_files_written": True,
        "api_frontend_changed": False,
        "overlays_created": False,
        "row_level_output_included": False,
        "private_paths_included": False,
    }


def test_service_strips_private_paths_and_row_level_fields_from_private_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        summary_path = Path(temp_dir) / "h4_prediction_summary.private.json"
        summary_path.write_text(
            json.dumps(
                {
                    "status": "h4_private_offline_inference_completed",
                    "feature_set_type": "real_i2_source_context_v1",
                    "training_type": "h3_scientific_real_feature_baseline",
                    "score_rows_written": 868,
                    "feature_matrix_rows": 868,
                    "feature_column_count": 8,
                    "score_min": 0.00004185,
                    "score_max": 0.97847171,
                    "score_mean": 0.2499092531797235,
                    "rows_by_source": {"C05": 217, "C06": 217, "C07": 217, "POS-01": 217},
                    "rows_by_split": {"holdout": 84, "test": 88, "train": 608, "val": 88},
                    "predictions_path": "C:\\Dev\\New_GEE_PRIVATE\\H4_INFERENCE\\h4_predictions.private.csv",
                }
            ),
            encoding="utf-8",
        )

        safe = load_h5_operator_aggregate_summary(summary_path)

    assert safe["total_row_count"] == 868
    assert safe["row_level_output_included"] is False
    assert safe["private_paths_included"] is False
    text = json.dumps(safe, sort_keys=True)
    assert "predictions_path" not in text
    assert "h4_predictions.private.csv" not in text
    assert "sample_id" not in text
    assert "positive_score" not in text


def test_redaction_guard_rejects_forbidden_row_level_fields() -> None:
    with pytest_raises_h5_error():
        assert_h5_operator_summary_is_redacted({"summary": {"sample_id": "private_sample"}})


def test_operator_route_requires_operator_role_and_returns_only_aggregate_fields() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), trusted_proxy_enabled=True)
        with patch("app.api.h5_operator_summary.load_h5_operator_aggregate_summary", return_value=_safe_summary()):
            with TestClient(create_app(settings), raise_server_exceptions=False) as client:
                denied = client.get(_PATH, headers=_operator_headers(roles="viewer"))
                allowed = client.get(_PATH, headers=_operator_headers())

    assert denied.status_code == 403
    assert denied.json()["outcome"] == "denied"

    assert allowed.status_code == 200
    body = allowed.json()
    assert body["outcome"] == "allowed"
    assert body["access_mode"] == "operator_only_aggregate"
    assert body["summary"]["total_row_count"] == 868
    assert body["summary"]["row_level_output_included"] is False
    assert body["downloadable_via_api"] is False
    assert body["overlays_created"] is False
    text = allowed.text.lower()
    assert "sample_id" not in text
    assert "positive_score" not in text
    assert "predictions_path" not in text
    assert "h4_predictions.private.csv" not in text
    assert "c:\\" not in text


class pytest_raises_h5_error:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        assert exc_type is H5OperatorSummaryError
        return True
