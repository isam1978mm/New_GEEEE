import csv
import json
import zipfile
from pathlib import Path

import pytest

from app.pipeline.parity.v6_package import (
    V6_PACKAGE_IMPORT_SCHEMA_VERSION,
    V6_REQUIRED_INPUT_FILES,
    V6PackageValidationError,
    import_v6_package,
)


TIMESTAMPED_CSV = "lawful_gee_candidate_scout_top_25_20260101T120000Z.csv"
TIMESTAMPED_GEOJSON = "lawful_gee_candidate_scout_top_25_20260101T120000Z.geojson"


def _feature_collection() -> str:
    return json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"candidate_id": "c1"},
                    "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                }
            ],
        }
    )


def _write_csv(path: Path, header: list[str], row: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow(row)


def _write_complete_package(package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(package_dir / TIMESTAMPED_CSV, ["candidate_id"], ["c1"])
    (package_dir / TIMESTAMPED_GEOJSON).write_text(
        _feature_collection(),
        encoding="utf-8",
    )
    _write_csv(
        package_dir / "top25_enhanced_v6.csv",
        ["candidate_id", "candidate_score"],
        ["c1", "0.91"],
    )
    (package_dir / "top25_enhanced_v6.geojson").write_text(
        _feature_collection(),
        encoding="utf-8",
    )
    _write_csv(
        package_dir / "quality_diagnostics_all_cells_v6.csv",
        ["cell_id"],
        ["cell-1"],
    )
    _write_csv(
        package_dir / "stable_candidate_priority_list_v6.csv",
        ["candidate_id", "review_priority_score"],
        ["c1", "0.88"],
    )
    _write_csv(package_dir / "request_zones_v6.csv", ["zone_id"], ["z1"])
    (package_dir / "request_zones_v6.geojson").write_text(
        _feature_collection(),
        encoding="utf-8",
    )
    _write_csv(package_dir / "paid_imagery_quote_template_v6.csv", ["zone_id"], ["z1"])
    _write_csv(
        package_dir / "paid_imagery_quote_comparison_v6.csv",
        ["zone_id"],
        ["z1"],
    )
    (package_dir / "paid_archive_request_summary.txt").write_text(
        "summary\n",
        encoding="utf-8",
    )
    (package_dir / "visual_inspection_map.html").write_text(
        "<!doctype html><title>map</title>",
        encoding="utf-8",
    )


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in sorted(source_dir.iterdir()):
            archive.write(path, path.name)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_import_from_directory_writes_manifest_hashes_and_preserves_names(tmp_path):
    source_dir = tmp_path / "source"
    run_dir = tmp_path / "run"
    _write_complete_package(source_dir)

    result = import_v6_package(source_dir, run_dir=run_dir, run_id="run-1")
    manifest = _read_json(result.import_manifest_path)

    assert manifest["schema_version"] == V6_PACKAGE_IMPORT_SCHEMA_VERSION
    assert manifest["source_type"] == "directory"
    assert manifest["missing_required_files"] == []
    assert {item["file_name"] for item in manifest["package_files"]} == set(
        V6_REQUIRED_INPUT_FILES
    ) | {TIMESTAMPED_CSV, TIMESTAMPED_GEOJSON}
    for item in manifest["package_files"]:
        assert len(item["sha256"]) == 64
        assert item["size_bytes"] > 0
        assert (run_dir / item["parity_path"]).is_file()
    assert (run_dir / "parity" / "maps" / "visual_inspection_map.html").is_file()


def test_import_from_zip_succeeds_with_complete_package(tmp_path):
    source_dir = tmp_path / "source"
    source_zip = tmp_path / "v6.zip"
    run_dir = tmp_path / "run"
    _write_complete_package(source_dir)
    _zip_directory(source_dir, source_zip)

    result = import_v6_package(source_zip, run_dir=run_dir, run_id="run-zip")
    manifest = _read_json(result.import_manifest_path)

    assert manifest["source_type"] == "zip"
    assert manifest["validation_status"] == "valid"
    assert (run_dir / "parity" / "root" / "top25_enhanced_v6.csv").is_file()
    assert (run_dir / "parity" / "maps" / "visual_inspection_map.html").is_file()


def test_missing_required_file_fails_clearly(tmp_path):
    source_dir = tmp_path / "source"
    _write_complete_package(source_dir)
    (source_dir / "request_zones_v6.csv").unlink()

    with pytest.raises(V6PackageValidationError, match="request_zones_v6.csv"):
        import_v6_package(source_dir, run_dir=tmp_path / "run", run_id="run-missing")


def test_bad_csv_columns_fail_clearly(tmp_path):
    source_dir = tmp_path / "source"
    _write_complete_package(source_dir)
    _write_csv(source_dir / "top25_enhanced_v6.csv", ["candidate_id"], ["c1"])

    with pytest.raises(V6PackageValidationError, match="top25_enhanced_v6.csv"):
        import_v6_package(source_dir, run_dir=tmp_path / "run", run_id="run-bad-csv")


def test_bad_geojson_fails_clearly(tmp_path):
    source_dir = tmp_path / "source"
    _write_complete_package(source_dir)
    (source_dir / "request_zones_v6.geojson").write_text("{bad json", encoding="utf-8")

    with pytest.raises(V6PackageValidationError, match="request_zones_v6.geojson"):
        import_v6_package(source_dir, run_dir=tmp_path / "run", run_id="run-bad-json")


def test_zip_path_traversal_is_blocked(tmp_path):
    source_dir = tmp_path / "source"
    source_zip = tmp_path / "v6.zip"
    _write_complete_package(source_dir)
    _zip_directory(source_dir, source_zip)

    with zipfile.ZipFile(source_zip, "a") as archive:
        archive.writestr("../escape.txt", "escape")

    with pytest.raises(V6PackageValidationError, match="path traversal"):
        import_v6_package(source_zip, run_dir=tmp_path / "run", run_id="run-traverse")


def test_rebuild_zip_is_created_with_original_filenames(tmp_path):
    source_dir = tmp_path / "source"
    run_dir = tmp_path / "run"
    _write_complete_package(source_dir)

    result = import_v6_package(
        source_dir,
        run_dir=run_dir,
        run_id="run-rebuild",
        rebuild_zip=True,
    )
    manifest = _read_json(result.import_manifest_path)

    assert result.rebuilt_zip_path is not None
    assert result.rebuilt_zip_path.is_file()
    assert len(manifest["rebuilt_zip_sha256"]) == 64
    with zipfile.ZipFile(result.rebuilt_zip_path) as archive:
        assert set(archive.namelist()) == set(V6_REQUIRED_INPUT_FILES) | {
            TIMESTAMPED_CSV,
            TIMESTAMPED_GEOJSON,
        }


def test_parity_manifest_marks_private_coordinate_outputs(tmp_path):
    source_dir = tmp_path / "source"
    run_dir = tmp_path / "run"
    _write_complete_package(source_dir)

    result = import_v6_package(
        source_dir,
        run_dir=run_dir,
        run_id="run-parity",
        rebuild_zip=True,
    )
    parity_manifest = _read_json(result.parity_manifest_path)
    entries = {entry["notebook_name_or_pattern"]: entry for entry in parity_manifest["entries"]}

    for entry in parity_manifest["entries"]:
        assert entry["target_mode"] != "public_shared"
        assert entry["http_servable"] is False

    for name in (
        TIMESTAMPED_GEOJSON,
        "top25_enhanced_v6.geojson",
        "request_zones_v6.geojson",
        "visual_inspection_map.html",
    ):
        assert entries[name]["requires_coordinates"] is True
        assert entries[name]["artifact_class"] == "FILESYSTEM_ONLY"
        assert entries[name]["classification"] == "coordinate-bearing"
