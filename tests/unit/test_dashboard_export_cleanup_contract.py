from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERVIEW = ROOT / "frontend-v2" / "src" / "app" / "components" / "OverviewTab.tsx"
EXPORTS = ROOT / "frontend-v2" / "src" / "app" / "components" / "ExportsTab.tsx"


def test_dashboard_does_not_render_private_local_key_download_list() -> None:
    source = OVERVIEW.read_text(encoding="utf-8")

    assert 'from "./KeyDownloads"' not in source
    assert "<KeyDownloads" not in source
    assert "Private Local Outputs" not in source
    assert "Recent Runs" in source


def test_exports_use_the_four_operator_facing_categories() -> None:
    source = EXPORTS.read_text(encoding="utf-8")

    for label in (
        "Result & Classifier",
        "Location & Field",
        "Paid Imagery",
        "Technical / Advanced Outputs",
    ):
        assert label in source

    assert "Export Categories" in source
    assert "DEMs, rasters, hypercubes, arrays, manifests, QA/support files and compatibility copies." in source


def test_classifier_exports_prefer_canonical_files_without_hiding_legacy_downloads() -> None:
    source = EXPORTS.read_text(encoding="utf-8")

    assert '"classifier/summary.json"' in source
    assert '"classifier/classifications.csv"' in source
    assert '"experimental/summary.json"' in source
    assert '"experimental/classifications.csv"' in source
    assert 'return preferredClassifierAvailable ? "technical-advanced" : "result-classifier";' in source


def test_export_cleanup_preserves_existing_download_urls_and_paths() -> None:
    source = EXPORTS.read_text(encoding="utf-8")

    assert "filesByPath.set(file.path, file);" in source
    assert "href={file.downloadUrl}" in source
    assert "download={file.name}" in source
    assert "does not move, rename or republish them" in source
