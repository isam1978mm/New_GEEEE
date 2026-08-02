from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "Option5ResultsPanel.tsx"
CLASSIFIER_PANEL = (
    ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierOnlyResultsPanel.tsx"
)
ADAPTER = ROOT / "frontend-v2" / "src" / "app" / "api" / "anomalyResults.ts"


def test_option5_is_a_separate_decision_focused_panel() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert "Option 5 Results" in source
    assert "Decision you can take" in source
    assert "Radar anomaly review" in source
    assert "NOT DEPTH" in source
    assert "Review order" in source
    assert "Review zone" in source
    assert "Option 5 only helps choose what area to review first" in source
    assert "does not provide excavation depth" in source


def test_option5_technical_numbers_are_secondary_and_not_physical_claims() -> None:
    source = PANEL.read_text(encoding="utf-8").lower()

    assert "technical option 5 numbers" in source
    assert "explain the ranking only" in source
    assert "not probabilities, measurements, settlement, physical confirmation, or depth" in source
    assert "estimated depth:" not in source
    assert "depth in metres" not in source
    assert "depth in meters" not in source
    assert "change detected" not in source
    assert "confirmed target" not in source


def test_option5_zone_table_is_relative_review_priority_only() -> None:
    source = PANEL.read_text(encoding="utf-8")
    lower = source.lower()

    assert "Share of anomaly area" in source
    assert "Review earlier" in source
    assert "Review after higher zones" in source
    assert "Review later" in source
    assert "relative priority inside this run" in lower
    assert "no temporal radar-change confirmation is available" in lower
    assert "A validated before/after radar pair is required" in source
    assert "This single-run object artifact cannot provide one" in source


def test_classifier_panel_is_restored_without_option5_content() -> None:
    source = CLASSIFIER_PANEL.read_text(encoding="utf-8")

    assert "Classifier Results" in source
    assert "Final area findings summary" in source
    assert "score level counts" in source
    assert "All objects, sorted by score" in source
    assert "Finding reason" in source
    assert "Row start" in source
    assert "Column end" in source
    assert "Radar anomaly review" not in source
    assert "Dual-window radar surface-change review" not in source
    assert "Option 5 Results" not in source


def test_option5_adapter_reads_only_the_existing_public_safe_object_artifact() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    assert 'OBJECTS_ARTIFACT_NAME = "objects_index"' in source
    assert 'OBJECTS_FILENAME = "objects_index.csv"' in source
    assert "mean_anomaly" in source
    assert "max_anomaly" in source
    assert "estimated_depth" not in source
    assert "coordinates" not in source.lower()


def test_option5_adapter_builds_cluster_zone_summaries_without_physical_units() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    assert "summarizeAnomalyZones" in source
    assert "areaWeightedMeanAnomaly" in source
    assert "areaShare" in source
    assert "relativeDisturbanceReview" in source
    assert '"higher" | "medium" | "lower" | "only zone"' in source
    assert "metres" not in source.lower()
    assert "meters" not in source.lower()
    assert "settlement" not in source.lower()
