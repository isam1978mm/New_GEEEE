from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.services.operator_outputs import build_operator_output_tree


def _settings(root: Path) -> Settings:
    return Settings(data_dir=root, database_path=root / "test.db")


def test_operator_output_tree_distinguishes_missing_manifest_from_corrupt_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_id = "run-1"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)

    missing_tree = build_operator_output_tree(settings=settings, run_id=run_id)
    assert missing_tree.read_errors == []
    assert missing_tree.not_implemented == []

    manifest_path = run_dir / "QA" / "REPORT_640_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{not-json", encoding="utf-8")

    corrupt_tree = build_operator_output_tree(settings=settings, run_id=run_id)
    assert corrupt_tree.not_implemented == []
    assert len(corrupt_tree.read_errors) == 1
    error = corrupt_tree.read_errors[0]
    assert error.relative_path == "QA/REPORT_640_manifest.json"
    assert error.status == "manifest_read_error"
    assert error.source == "QA/REPORT_640_manifest.json"


def test_operator_output_tree_keeps_not_implemented_separate_from_read_errors(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_id = "run-1"
    run_dir = tmp_path / "runs" / run_id
    manifest_path = run_dir / "QA" / "REPORT_640_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        '{"reports":{"REPORT_640_missing.tif":{"status":"not_implemented_no_source_equivalent"}}}',
        encoding="utf-8",
    )

    tree = build_operator_output_tree(settings=settings, run_id=run_id)

    assert tree.read_errors == []
    assert len(tree.not_implemented) == 1
    assert tree.not_implemented[0].relative_path == "REPORT_640_missing.tif"
    assert tree.not_implemented[0].status == "not_implemented_no_source_equivalent"
