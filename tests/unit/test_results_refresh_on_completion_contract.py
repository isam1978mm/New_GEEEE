from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"


# Keep this regression additive: refresh lifecycle only, no classifier/Option 5 replacement.
# This file also anchors CI on the final generated-SPA PR head.
def test_results_panels_remount_when_an_active_run_reaches_done() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert 'import { getRunDetail } from "../api/client";' in source
    assert 'run.state === "queued" || run.state === "running"' in source
    assert 'run.state === "done" && sawActiveRun' in source
    assert 'return <ResultsPanels key={`${runId}:${completionRevision}`} runId={runId} />;' in source


def test_results_refresh_fix_preserves_existing_classifier_and_nb_panels() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert '<ClassifierOnlyResultsPanel runId={runId} />' in source
    assert '<NBResultsPanel runId={runId} />' in source
    assert "Option5ResultsPanel" not in source
