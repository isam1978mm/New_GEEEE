"""Unit tests for the D2 frozen reference-bundle validator and its CLI.

All bundles here are synthetic and created under pytest ``tmp_path``; no real
frozen reference artifacts are read or committed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.cli import reference_bundle as cli
from app.services.reference_bundle_validator import (
    REFERENCE_MANIFEST_NAME,
    STATUS_ERROR,
    STATUS_INVALID,
    STATUS_VALID,
    validate_reference_bundle,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_file(bundle: Path, relative_path: str, data: bytes) -> dict:
    target = bundle / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "relative_path": relative_path,
        "sha256": _sha256(data),
        "size_bytes": len(data),
        "role": "raster",
    }


def _write_manifest(bundle: Path, files: list[dict], **overrides) -> None:
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-01-01T00:00:00Z",
        "bundle_name": "synthetic_bundle_local_only",
        "files": files,
    }
    manifest.update(overrides)
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _make_valid_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    files = [
        _write_file(bundle, "rasters/curv_laplacian_640.tif", b"laplacian-bytes"),
        _write_file(bundle, "rasters/curv_plan_640.tif", b"plan-bytes-data"),
    ]
    _write_manifest(bundle, files)
    return bundle


# --- valid path --------------------------------------------------------------


def test_valid_bundle_passes(tmp_path: Path) -> None:
    bundle = _make_valid_bundle(tmp_path)
    result = validate_reference_bundle(bundle)

    assert result.status == STATUS_VALID
    assert result.is_valid is True
    assert result.file_count == 2
    assert result.total_bytes == len(b"laplacian-bytes") + len(b"plan-bytes-data")
    assert result.missing_count == 0
    assert result.checksum_mismatch_count == 0
    assert result.invalid_path_count == 0
    assert result.issues == ()


# --- structural / error cases ------------------------------------------------


def test_missing_bundle_directory_errors(tmp_path: Path) -> None:
    result = validate_reference_bundle(tmp_path / "does-not-exist")
    assert result.status == STATUS_ERROR
    assert result.error is not None


def test_missing_manifest_fails(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_ERROR
    assert REFERENCE_MANIFEST_NAME in (result.error or "")


def test_missing_required_field_errors(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    file_entry = _write_file(bundle, "a.bin", b"data")
    # Manifest without 'repo_commit'.
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "created_at": "2026-01-01T00:00:00Z",
        "bundle_name": "b",
        "files": [file_entry],
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_ERROR
    assert "repo_commit" in (result.error or "")


def test_unparseable_manifest_errors(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / REFERENCE_MANIFEST_NAME).write_text("{not-json", encoding="utf-8")
    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_ERROR


# --- per-file invalid cases --------------------------------------------------


def test_missing_file_fails(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    entry = {
        "relative_path": "rasters/absent.tif",
        "sha256": _sha256(b"whatever"),
        "size_bytes": 8,
    }
    _write_manifest(bundle, [entry])

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_INVALID
    assert result.missing_count == 1
    assert any(issue.issue == "missing" for issue in result.issues)


def test_checksum_mismatch_fails(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    entry = _write_file(bundle, "a.bin", b"correct-bytes")
    entry["sha256"] = _sha256(b"different-bytes")  # wrong checksum, same size unaffected
    _write_manifest(bundle, [entry])

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_INVALID
    assert result.checksum_mismatch_count == 1
    assert any(issue.issue == "checksum_mismatch" for issue in result.issues)


def test_size_mismatch_fails(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    entry = _write_file(bundle, "a.bin", b"twelve_bytes")
    entry["size_bytes"] = 999  # declared size differs from actual
    _write_manifest(bundle, [entry])

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_INVALID
    assert result.size_mismatch_count == 1
    assert any(issue.issue == "size_mismatch" for issue in result.issues)


def test_absolute_path_rejected(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    abs_path = (tmp_path / "outside.bin")
    abs_path.write_bytes(b"data")
    entry = {
        "relative_path": str(abs_path),
        "sha256": _sha256(b"data"),
        "size_bytes": 4,
    }
    _write_manifest(bundle, [entry])

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_INVALID
    assert result.invalid_path_count == 1
    assert any(issue.issue == "invalid_path" for issue in result.issues)


def test_parent_escape_path_rejected(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "secret.bin"
    outside.write_bytes(b"data")
    entry = {
        "relative_path": "../secret.bin",
        "sha256": _sha256(b"data"),
        "size_bytes": 4,
    }
    _write_manifest(bundle, [entry])

    result = validate_reference_bundle(bundle)
    assert result.status == STATUS_INVALID
    assert result.invalid_path_count == 1


def test_empty_file_flagged_unless_allowed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    entry = _write_file(bundle, "empty.bin", b"")
    _write_manifest(bundle, [entry])

    flagged = validate_reference_bundle(bundle)
    assert flagged.status == STATUS_INVALID
    assert flagged.empty_count == 1

    allowed = validate_reference_bundle(bundle, allow_empty_files=True)
    assert allowed.status == STATUS_VALID
    assert allowed.empty_count == 0


# --- CLI ---------------------------------------------------------------------


def test_cli_default_output_is_safe_summary_only(tmp_path: Path, capsys) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    # Use a path-bearing relative path that must never appear in default output.
    secret_segment = "lat_35.59499_lon_36.12694"
    entry = _write_file(bundle, f"{secret_segment}/raster.tif", b"")  # empty -> invalid
    _write_manifest(bundle, [entry])

    exit_code = cli.main(["--bundle-dir", str(bundle)])
    out = capsys.readouterr().out

    assert exit_code == 1  # invalid bundle -> nonzero
    payload = json.loads(out)
    assert set(payload) == {
        "status",
        "file_count",
        "total_bytes",
        "missing_count",
        "size_mismatch_count",
        "checksum_mismatch_count",
        "invalid_path_count",
        "empty_count",
        "error",
    }
    # Default output must not print detailed paths.
    assert secret_segment not in out
    assert "relative_path" not in out
    assert "bundle_name" not in out


def test_cli_show_details_includes_paths(tmp_path: Path, capsys) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    entry = _write_file(bundle, "rasters/missing.tif", b"x")
    # Force a missing-file issue by deleting the file but keeping the manifest.
    (bundle / "rasters" / "missing.tif").unlink()
    _write_manifest(bundle, [entry])

    exit_code = cli.main(["--bundle-dir", str(bundle), "--show-details"])
    out = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(out)
    assert "issues" in payload
    assert "bundle_name" in payload
    assert any(item["relative_path"] == "rasters/missing.tif" for item in payload["issues"])


def test_cli_valid_bundle_returns_zero(tmp_path: Path, capsys) -> None:
    bundle = _make_valid_bundle(tmp_path)
    exit_code = cli.main(["--bundle-dir", str(bundle)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert json.loads(out)["status"] == STATUS_VALID
