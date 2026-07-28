from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"
ADAPTER = ROOT / "frontend-v2" / "src" / "app" / "api" / "anomalyResults.ts"


def test_option5_panel_labels_anomaly_as_not_depth() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert "Radar anomaly review" in source
    assert "NOT DEPTH" in source
    assert "unitless, within-run PCA anomaly scores" in source
    assert "not a probability" in source
    assert "not a depth estimate" in source
    assert "Depth estimate: not available" in source
    assert "Global and local numerical calibration remain disabled" in source


def test_option5_panel_does_not_claim_measured_change_or_numerical_depth() -> None:
    source = PANEL.read_text(encoding="utf-8").lower()

    assert "a change measurement" in source
    assert "estimated depth:" not in source
    assert "depth in metres" not in source
    assert "depth in meters" not in source
    assert "change detected" not in source
    assert "confirmed target" not in source


def test_option5_adapter_reads_only_the_existing_public_safe_object_artifact() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    assert 'OBJECTS_ARTIFACT_NAME = "objects_index"' in source
    assert 'OBJECTS_FILENAME = "objects_index.csv"' in source
    assert "mean_anomaly" in source
    assert "max_anomaly" in source
    assert "estimated_depth" not in source
    assert "coordinates" not in source.lower()
