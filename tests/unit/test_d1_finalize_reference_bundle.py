from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_finalize_reference_bundle as finalizer


def make_bundle(tmp_path: Path) -> Path:
    bundle_root = tmp_path / "data" / "private_references" / "notebook_frozen" / "new_ipynb_d1_test"
    artifacts = bundle_root / "artifacts"
    (artifacts / "dem").mkdir(parents=True)
    (artifacts / "report").mkdir(parents=True)
    (bundle_root / "logs").mkdir()
    (bundle_root / "manifest.local.template.json").write_text(
        json.dumps(
            {
                "bundle_id": "new_ipynb_d1_test",
                "notebook_name": "new.ipynb",
                "notebook_version": "local-version",
                "collected_at": "2026-06-15T00:00:00Z",
                "operator": "local-operator",
                "source_run_id": "local-run",
                "artifact_families": ["new_ipynb_outputs"],
                "local_artifact_paths": [],
                "notes": "template",
            }
        ),
        encoding="utf-8",
    )
    (artifacts / "dem" / "reference_dem.tif").write_text("placeholder", encoding="utf-8")
    (artifacts / "report" / "reference_report.json").write_text("{}", encoding="utf-8")
    return bundle_root


def test_finalize_bundle_writes_manifest_from_artifacts(tmp_path: Path) -> None:
    bundle_root = make_bundle(tmp_path)
    result = finalizer.finalize_bundle(bundle_root, collected_at="2026-06-15T00:00:00Z")

    manifest_path = Path(str(result["manifest_path"]))
    assert manifest_path.name == "manifest.local.json"
    assert result["artifact_count"] == 2
    assert result["family_count"] == 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["bundle_id"] == "new_ipynb_d1_test"
    assert manifest["artifact_families"] == ["dem", "report"]
    assert len(manifest["local_artifact_paths"]) == 2


def test_finalize_bundle_fails_when_no_artifacts(tmp_path: Path) -> None:
    bundle_root = tmp_path / "data" / "private_references" / "notebook_frozen" / "empty"
    (bundle_root / "artifacts").mkdir(parents=True)
    try:
        finalizer.finalize_bundle(bundle_root)
    except finalizer.BundleFinalizeError:
        return
    raise AssertionError("empty artifact folder should fail")


def test_cli_json_summary(tmp_path: Path, capsys) -> None:
    bundle_root = make_bundle(tmp_path)
    rc = finalizer.main([
        "--bundle-root",
        str(bundle_root),
        "--collected-at",
        "2026-06-15T00:00:00Z",
        "--json",
    ])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["ok"] is True
    assert parsed["artifact_count"] == 2
