from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"


def test_classifier_results_page_keeps_classifier_ui_and_does_not_mount_option5_panel() -> None:
    source = PANEL.read_text(encoding="utf-8")
    assert 'import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";' in source
    assert "<ClassifierOnlyResultsPanel runId={runId} />" in source
    assert "Option5ResultsPanel" not in source
