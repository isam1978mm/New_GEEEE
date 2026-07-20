from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_depth_s1_matched_feature_completeness as audit
import extract_depth_s1_matched_features as extractor


PRIVATE_ID = "S1A_PRIVATE_IMAGE_ID"
PRIVATE_COORDINATE_TEXT = "-97.1234"


def _stats(base: float) -> dict[str, float | int | None]:
    values: dict[str, float | int | None] = {}
    for index, key in enumerate(extractor.STATISTIC_KEYS):
        values[key] = 25 if key.endswith("_count") else base + index / 100.0
    return values


def _payload() -> dict[str, object]:
    return {
        "schema_version": extractor.PRIVATE_OUTPUT_SCHEMA,
        "status": "matched_s1_feature_extraction_complete",
        "selection_contract": {},
        "feature_names": list(extractor.FEATURE_NAMES),
        "statistics_per_feature": list(extractor.STATISTIC_NAMES),
        "transition_rows_excluded": 1,
        "coordinates_included": False,
        "geometry_included": False,
        "rows": [
            {
                "period": "pre",
                "image_id": PRIVATE_ID,
                "timestamp": "2019-01-01T00:00:00+00:00",
                "site": _stats(1.0),
                "background": _stats(0.5),
                "site_minus_background": {},
            },
            {
                "period": "post",
                "image_id": "S1A_PRIVATE_POST",
                "timestamp": "2021-01-01T00:00:00+00:00",
                "site": _stats(2.0),
                "background": _stats(1.5),
                "site_minus_background": {},
            },
        ],
        "private_note": PRIVATE_COORDINATE_TEXT,
    }


def _write(path: Path, payload: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps(payload or _payload()), encoding="utf-8")


def test_repository_local_input_is_rejected() -> None:
    with pytest.raises(audit.DepthS1FeatureCompletenessError, match="outside the repository"):
        audit.audit_private_feature_completeness(ROOT / "private_features.json")


def test_complete_private_table_reports_no_missing_statistics(tmp_path: Path) -> None:
    path = tmp_path / "features.json"
    _write(path)

    result = audit.audit_private_feature_completeness(path)

    assert result["status"] == "matched_s1_feature_completeness_complete"
    assert result["row_count"] == 2
    assert result["expected_statistic_count"] == 80
    assert result["missing_statistic_count"] == 0
    assert result["affected_row_count"] == 0
    assert result["all_missing_explained_by_zero_count"] is False


def test_zero_valid_pixel_percentiles_are_classified_without_imputation(tmp_path: Path) -> None:
    path = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    site = first["site"]
    assert isinstance(site, dict)
    site["vv_db_count"] = 0
    site["vv_db_p25"] = None
    site["vv_db_median"] = None
    site["vv_db_p75"] = None
    _write(path, payload)

    result = audit.audit_private_feature_completeness(path)

    assert result["status"] == "matched_s1_feature_completeness_missing_due_to_zero_valid_pixels"
    assert result["missing_statistic_count"] == 3
    assert result["missing_explained_by_zero_count"] == 3
    assert result["all_missing_explained_by_zero_count"] is True
    assert result["affected_row_count"] == 1
    assert result["rows_with_zero_valid_pixels"] == 1
    assert result["missing_by_feature"]["vv_db"] == 3
    assert result["zero_count_by_side"]["site"] == 1


def test_positive_count_missing_value_remains_unexplained(tmp_path: Path) -> None:
    path = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    site = first["site"]
    assert isinstance(site, dict)
    site["vh_db_median"] = None
    _write(path, payload)

    result = audit.audit_private_feature_completeness(path)

    assert result["status"] == "matched_s1_feature_completeness_missing_unexplained"
    assert result["missing_statistic_count"] == 1
    assert result["missing_explained_by_zero_count"] == 0
    assert result["all_missing_explained_by_zero_count"] is False


def test_invalid_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "features.json"
    payload = _payload()
    payload["schema_version"] = "wrong"
    _write(path, payload)

    with pytest.raises(audit.DepthS1FeatureCompletenessError, match="schema"):
        audit.audit_private_feature_completeness(path)


def test_aggregate_result_leaks_no_private_ids_coordinates_values_or_paths(tmp_path: Path) -> None:
    path = tmp_path / "features.json"
    _write(path)

    result = audit.audit_private_feature_completeness(path)
    rendered = json.dumps(result)

    assert PRIVATE_ID not in rendered
    assert PRIVATE_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered
    assert result["image_ids_printed"] is False
    assert result["coordinates_printed"] is False
    assert result["feature_values_printed"] is False
    assert result["private_paths_printed"] is False
