from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"


# Keep this regression additive: refresh lifecycle only, no classifier/Option 5 replacement.
# Final-head CI anchor after the generated SPA assets were committed by validation.
def test_results_panels_remount_when_run_reaches_done_even_if_done_is_seen_first() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert 'import { getRunDetail } from "../api/client";' in source
    assert 'run.state === "queued" || run.state === "running"' in source
    assert 'if (run.state === "done")' in source
    assert "sawActiveRun" not in source
    assert 'return <ResultsPanels key={`${runId}:${completionRevision}`} runId={runId} />;' in source


def test_results_refresh_fix_preserves_existing_classifier_and_nb_panels() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert '<ClassifierOnlyResultsPanel runId={runId} />' in source
    assert '<NBResultsPanel runId={runId} />' in source
    assert "Option5ResultsPanel" not in source
