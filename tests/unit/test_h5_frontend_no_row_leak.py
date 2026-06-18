from __future__ import annotations

from pathlib import Path


API_CLIENT = Path("frontend-v2/src/app/api/h5OperatorSummary.ts")
PANEL = Path("frontend-v2/src/app/components/H5OperatorAggregateSummaryPanel.tsx")
PARENT_PANEL = Path("frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx")

_FORBIDDEN_ROW_LEVEL_TOKENS = (
    "sample_id",
    "positive_score",
    "predictions_path",
    "h4_predictions.private.csv",
    "model_artifact_path",
    "feature_matrix_path",
    "feature_values",
    "rawCsv",
    "downloadUrl",
    "<a ",
    "href=",
    "download=",
)

_ALLOWED_AGGREGATE_TOKENS = (
    "totalRowCount",
    "featureColumnCount",
    "scoreMin",
    "scoreMax",
    "scoreMean",
    "scoreBandCounts",
    "scoreBandCountsStatus",
    "rowsBySource",
    "rowsBySplit",
    "rowLevelOutputIncluded",
    "privatePathsIncluded",
    "overlaysCreated",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_h5_frontend_files_exist() -> None:
    assert API_CLIENT.is_file()
    assert PANEL.is_file()
    assert PARENT_PANEL.is_file()


def test_h5_frontend_client_maps_aggregate_only_contract() -> None:
    content = _read(API_CLIENT)

    assert "/operator/h5/aggregate-summary" in content
    assert "H5OperatorAggregateSummary" in content
    for token in _ALLOWED_AGGREGATE_TOKENS:
        assert token in content

    lowered = content.lower()
    for token in _FORBIDDEN_ROW_LEVEL_TOKENS:
        assert token.lower() not in lowered


def test_h5_frontend_panel_renders_only_aggregate_boundary() -> None:
    content = _read(PANEL)

    assert "H5 operator aggregate summary" in content
    assert "Aggregate prediction summary" in content
    assert "No row-level output" in content
    assert "No row-level" in content
    assert "private paths" in content
    assert "overlays" in content
    assert "Score bands" in content
    assert "Score band status" in content
    assert "formatCounts(summary.scoreBandCounts)" in content
    assert "formatCounts(summary.rowsBySource)" in content
    assert "formatCounts(summary.rowsBySplit)" in content

    lowered = content.lower()
    for token in _FORBIDDEN_ROW_LEVEL_TOKENS:
        assert token.lower() not in lowered


def test_h5_panel_is_nested_under_existing_operator_private_gate() -> None:
    content = _read(PARENT_PANEL)

    assert "H5OperatorAggregateSummaryPanel" in content
    assert "operatorAccessToken={resolvedOperatorAccessToken}" in content
    assert "Operator-only private preview" in content
