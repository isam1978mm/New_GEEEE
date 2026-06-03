import json

import pytest

from app.pipeline.parity import (
    PARITY_SCHEMA_VERSION,
    STANDARD_PARITY_SUBDIRS,
    ParityManifestEntry,
    ParityManifestError,
    ParityPathError,
    ensure_standard_parity_dirs,
    resolve_parity_output_path,
    write_parity_manifest,
)


def test_resolve_parity_output_path_blocks_path_traversal(tmp_path):
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    with pytest.raises(ParityPathError):
        resolve_parity_output_path(run_dir, "../escape.tif")

    with pytest.raises(ParityPathError):
        resolve_parity_output_path(run_dir, "/absolute/escape.tif")


def test_ensure_standard_parity_dirs_creates_only_under_run_dir(tmp_path):
    run_dir = tmp_path / "run-1"

    dirs = ensure_standard_parity_dirs(run_dir)

    assert (run_dir / "parity").is_dir()
    assert (run_dir / "manifests").is_dir()
    for subdir in STANDARD_PARITY_SUBDIRS:
        assert (run_dir / "parity" / subdir).is_dir()
        assert dirs[subdir].resolve().relative_to(run_dir.resolve())


def test_manifest_json_writes_parses_and_preserves_notebook_name(tmp_path):
    run_dir = tmp_path / "run-1"
    notebook_name = "REPORT_640_FINAL_Zero_Point_Targets.tif"
    entry = ParityManifestEntry(
        source_path="app_native/pca_anomaly.tif",
        parity_path="parity/REPORT_640/" + notebook_name,
        notebook_name_or_pattern=notebook_name,
        family="REPORT_640 outputs",
        classification="notebook-parity report/semantic raster stage",
        artifact_class="LOCAL_SENSITIVE",
        notes="Original notebook name retained for parity inventory.",
    )

    manifest_path = write_parity_manifest(run_dir, "run-1", [entry])
    parsed = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert parsed["schema_version"] == PARITY_SCHEMA_VERSION
    assert parsed["run_id"] == "run-1"
    assert parsed["parity_root"] == "parity"
    assert parsed["entries"][0]["notebook_name_or_pattern"] == notebook_name
    assert parsed["entries"][0]["target_mode"] == "notebook_parity"
    assert parsed["entries"][0]["http_servable"] is False


def test_manifest_entries_mark_coordinate_and_probability_classifier_outputs():
    coordinate_entry = ParityManifestEntry(
        source_path="app_native/candidates.csv",
        parity_path="parity/maps/candidates.geojson",
        notebook_name_or_pattern="candidates.geojson",
        family="coordinate/map/KMZ/GeoJSON outputs",
        classification="coordinate-bearing",
        artifact_class="FILESYSTEM_ONLY",
        requires_coordinates=True,
    )
    probability_entry = ParityManifestEntry(
        source_path="experimental/class_scores.csv",
        parity_path="parity/experimental/class_scores.csv",
        notebook_name_or_pattern="AI probability classifier report",
        family="future probability-only classifier outputs",
        classification="probability-classifier output",
        target_mode="experimental_private",
        artifact_class="FILESYSTEM_ONLY",
        probability_only_required=True,
    )

    assert coordinate_entry.requires_coordinates is True
    assert coordinate_entry.http_servable is False
    assert probability_entry.probability_only_required is True
    assert probability_entry.http_servable is False


def test_probability_classifier_output_requires_probability_only_flag():
    with pytest.raises(ParityManifestError):
        ParityManifestEntry(
            source_path="experimental/class_scores.csv",
            parity_path="parity/experimental/class_scores.csv",
            notebook_name_or_pattern="AI classifier report",
            family="classifier/model outputs",
            classification="probability-classifier output",
            artifact_class="FILESYSTEM_ONLY",
        )


def test_secret_layers_and_report_640_classifications_are_representable():
    secret_entry = ParityManifestEntry(
        source_path="app_native/secret_layers.tif",
        parity_path="parity/root/secret_layers.tif",
        notebook_name_or_pattern="secret_layers.py semantic outputs",
        family="AI_BEH / AI_READY outputs",
        classification="notebook-parity semantic raster stage",
        artifact_class="LOCAL_SENSITIVE",
    )
    report_entry = ParityManifestEntry(
        source_path="app_native/report_640.tif",
        parity_path="parity/root/report_640.tif",
        notebook_name_or_pattern="REPORT_640 outputs",
        family="REPORT_640 outputs",
        classification="notebook-parity report/semantic raster stage",
        artifact_class="LOCAL_SENSITIVE",
    )

    assert secret_entry.classification == "notebook-parity semantic raster stage"
    assert report_entry.classification == "notebook-parity report/semantic raster stage"


def test_helper_defaults_do_not_create_public_shared_exposure():
    entry = ParityManifestEntry(
        source_path="app_native/dem.tif",
        parity_path="parity/DEM_GEO8_TIFS/dem.tif",
        notebook_name_or_pattern="DEM_GEO8_TIFS/*.tif",
        family="DEM/terrain outputs",
        classification="notebook-parity",
        artifact_class="LOCAL_SENSITIVE",
    )

    assert entry.target_mode == "notebook_parity"
    assert entry.http_servable is False
