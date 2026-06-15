from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_init_reference_bundle as init_bundle


def test_creates_template_bundle_without_artifact_paths(tmp_path: Path) -> None:
    result = init_bundle.create_bundle(
        tmp_path / "data" / "private_references" / "notebook_frozen",
        "new_ipynb_d1_test",
        "local-version",
        "local-run",
        "local-operator",
        [],
        [],
        "2026-06-15T00:00:00Z",
    )

    bundle_root = Path(str(result["bundle_root"]))
    manifest_path = Path(str(result["manifest_path"]))
    assert bundle_root.is_dir()
    assert (bundle_root / "artifacts" / "new_ipynb_outputs").is_dir()
    assert (bundle_root / "logs").is_dir()
    assert manifest_path.name == "manifest.local.template.json"
    assert result["finalized_manifest"] is False

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["notebook_name"] == "new.ipynb"
    assert manifest["local_artifact_paths"] == []


def test_creates_final_manifest_with_relative_artifact_paths(tmp_path: Path) -> None:
    result = init_bundle.create_bundle(
        tmp_path / "data" / "private_references" / "notebook_frozen",
        "new_ipynb_d1_test",
        "local-version",
        "local-run",
        "local-operator",
        ["dem", "report"],
        ["dem/reference_dem.tif", "report/reference_report.json"],
        "2026-06-15T00:00:00Z",
    )

    manifest_path = Path(str(result["manifest_path"]))
    assert manifest_path.name == "manifest.local.json"
    assert result["finalized_manifest"] is True
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifact_families"] == ["dem", "report"]
    assert len(manifest["local_artifact_paths"]) == 2


def test_rejects_unsafe_bundle_id(tmp_path: Path) -> None:
    try:
        init_bundle.create_bundle(tmp_path, "bad/bundle", "v", "r", "o", [], [], "2026-06-15T00:00:00Z")
    except init_bundle.BundleInitError:
        return
    raise AssertionError("unsafe bundle id should fail")


def test_rejects_rooted_artifact_path(tmp_path: Path) -> None:
    try:
        init_bundle.create_bundle(tmp_path, "new_ipynb_d1_test", "v", "r", "o", [], ["/tmp/file.tif"], "2026-06-15T00:00:00Z")
    except init_bundle.BundleInitError:
        return
    raise AssertionError("rooted artifact path should fail")


def test_cli_json_summary(tmp_path: Path, capsys) -> None:
    rc = init_bundle.main([
        "--root",
        str(tmp_path / "data" / "private_references" / "notebook_frozen"),
        "--bundle-id",
        "new_ipynb_d1_test",
        "--notebook-version",
        "local-version",
        "--source-run-id",
        "local-run",
        "--operator",
        "local-operator",
        "--json",
    ])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["ok"] is True
    assert parsed["finalized_manifest"] is False
