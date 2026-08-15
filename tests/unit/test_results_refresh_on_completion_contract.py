from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"


def test_results_panels_remount_when_an_active_run_reaches_done() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert 'import { getRunDetail } from "../api/client";' in source
    assert 'run.state === "queued" || run.state === "running"' in source
    assert 'run.state === "done" && sawActiveRun' in source
    assert 'key={`classifier:${runId}:${completionRevision}`}' in source
    assert 'key={`nb:${runId}:${completionRevision}`}' in source


def test_results_refresh_fix_preserves_existing_classifier_and_nb_panels() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert '<ClassifierOnlyResultsPanel' in source
    assert '<NBResultsPanel' in source
    assert "Option5ResultsPanel" not in source
