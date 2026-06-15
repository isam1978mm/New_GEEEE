from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_compare_app_reference_inventory as compare


def make_manifest(tmp_path: Path, paths: list[str]) -> Path:
    manifest = {
        "bundle_id": "new_ipynb_d1_test",
        "notebook_name": "new.ipynb",
        "notebook_version": "local-version",
        "collected_at": "2026-06-15T00:00:00Z",
        "operator": "local-operator",
        "source_run_id": "local-run",
        "artifact_families": ["dem", "report"],
        "local_artifact_paths": paths,
        "notes": "local only",
    }
    manifest_path = tmp_path / "manifest.local.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_family_from_path() -> None:
    assert compare._family_from_reference_path("bundle/artifacts/dem/file.tif") == "dem"


def test_inventory_compare_passes_when_names_exist(tmp_path: Path) -> None:
    manifest_path = make_manifest(
        tmp_path,
        ["bundle/artifacts/dem/a.tif", "bundle/artifacts/report/b.json"],
    )
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "a.tif").write_text("x", encoding="utf-8")
    (app_dir / "b.json").write_text("{}", encoding="utf-8")

    result = compare.compare_inventory(manifest_path, app_dir)
    assert result["status"] == "passed"
    assert result["matched_reference_name_count"] == 2
    assert result["missing_reference_name_count"] == 0


def test_inventory_compare_reports_missing_names(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path, ["bundle/artifacts/dem/a.tif"])
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "other.tif").write_text("x", encoding="utf-8")

    result = compare.compare_inventory(manifest_path, app_dir)
    assert result["status"] == "incomplete"
    assert result["missing_reference_name_count"] == 1
    assert result["missing_reference_names"] == ["a.tif"]
