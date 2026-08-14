from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"
CLASSIFIER = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierOnlyResultsPanel.tsx"
NB_PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "NBResultsPanel.tsx"
MAIN = ROOT / "app" / "main.py"


def test_nb_panel_is_additive_and_does_not_restore_option5() -> None:
    wrapper = WRAPPER.read_text(encoding="utf-8")
    assert "ClassifierOnlyResultsPanel" in wrapper
    assert "NBResultsPanel" in wrapper
    assert "Option5ResultsPanel" not in wrapper


def test_nb_fields_live_outside_classifier_panel() -> None:
    classifier = CLASSIFIER.read_text(encoding="utf-8")
    nb_panel = NB_PANEL.read_text(encoding="utf-8")
    assert "NB metal signature" not in classifier
    assert "NB depth" not in classifier
    for label in (
        "NB metal signature",
        "NB void signature",
        "NB ceramic signature",
        "NB mass signature",
        "NB false-signature score",
        "NB best object interpretation",
        "NB depth",
    ):
        assert label in nb_panel
    assert "default 3.0 m display fallback is not used" in nb_panel
    assert "calibrated Numerical Depth Estimate" in nb_panel


def test_nb_api_router_is_additive() -> None:
    source = MAIN.read_text(encoding="utf-8")
    assert "nb_results_router" in source
    assert "app.include_router(nb_results_router)" in source
