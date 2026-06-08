"""Unit tests for scripts/d1_validate_reference_manifest.py. No network, no file writes by the tool."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_validate_reference_manifest as validator

_ROOT = Path(__file__).parent.parent.parent
_EXAMPLE = _ROOT / "docs" / "examples" / "d1-reference-manifest.local.example.json"


def _valid_manifest() -> dict:
    return {
        "bundle_id": "example_bundle_local_only",
        "notebook_name": "example_notebook",
        "notebook_version": "example-version",
        "collected_at": "2026-01-01T00:00:00Z",
        "operator": "example_operator",
        "source_run_id": "example_run_id",
        "artifact_families": ["example_artifact_family"],
        "local_artifact_paths": [
            "data/private_references/notebook_frozen/example_bundle_local_only/artifacts/example_file.ext"
        ],
        "notes": "local only placeholder",
    }


def _write(tmp_path: Path, manifest: dict) -> Path:
    p = tmp_path / "manifest.local.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Valid path
# ---------------------------------------------------------------------------

def test_valid_manifest_passes() -> None:
    results = validator.validate_manifest(_valid_manifest(), allow_external=False)
    assert not validator._has_fail(results)


def test_strict_mode_valid_manifest_exits_zero(tmp_path: Path) -> None:
    p = _write(tmp_path, _valid_manifest())
    assert validator.main(["--manifest", str(p), "--strict"]) == 0


def test_placeholder_docs_example_loads_and_validates() -> None:
    assert validator.main(["--manifest", str(_EXAMPLE), "--strict"]) == 0


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

def test_missing_required_field_fails(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    del manifest["bundle_id"]
    results = validator.validate_manifest(manifest, allow_external=False)
    req = next(r for r in results if r["check"] == "required_keys")
    assert req["status"] == "FAIL"
    p = _write(tmp_path, manifest)
    assert validator.main(["--manifest", str(p), "--strict"]) == 1


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def test_url_artifact_path_fails() -> None:
    manifest = _valid_manifest()
    manifest["local_artifact_paths"] = ["https://example.test/ref/file.bin"]
    results = validator.validate_manifest(manifest, allow_external=False)
    paths = next(r for r in results if r["check"] == "local_artifact_paths")
    assert paths["status"] == "FAIL"


def test_absolute_external_path_fails() -> None:
    manifest = _valid_manifest()
    manifest["local_artifact_paths"] = ["/etc/secret/reference.bin"]
    results = validator.validate_manifest(manifest, allow_external=False)
    paths = next(r for r in results if r["check"] == "local_artifact_paths")
    assert paths["status"] == "FAIL"


def test_absolute_external_path_allowed_with_flag_warns_not_fails() -> None:
    manifest = _valid_manifest()
    manifest["local_artifact_paths"] = ["/some/operator/external/reference.bin"]
    results = validator.validate_manifest(manifest, allow_external=True)
    paths = next(r for r in results if r["check"] == "local_artifact_paths")
    assert paths["status"] == "PASS"


# ---------------------------------------------------------------------------
# Suspicious keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_key", ["coordinates", "geometry", "bounds", "bbox", "latitude", "longitude", "crs", "transform"])
def test_suspicious_coordinate_geometry_keys_fail(bad_key: str) -> None:
    manifest = _valid_manifest()
    manifest[bad_key] = "anything"
    results = validator.validate_manifest(manifest, allow_external=False)
    sus = next(r for r in results if r["check"] == "suspicious_keys")
    assert sus["status"] == "FAIL"


@pytest.mark.parametrize("bad_key", ["sha256", "hash"])
def test_suspicious_hash_keys_fail(bad_key: str) -> None:
    manifest = _valid_manifest()
    manifest[bad_key] = "deadbeef"
    results = validator.validate_manifest(manifest, allow_external=False)
    sus = next(r for r in results if r["check"] == "suspicious_keys")
    assert sus["status"] == "FAIL"


def test_nested_suspicious_key_fails() -> None:
    manifest = _valid_manifest()
    manifest["family_inventory"] = {"family_a": {"geometry": [1, 2, 3]}}
    results = validator.validate_manifest(manifest, allow_external=False)
    sus = next(r for r in results if r["check"] == "suspicious_keys")
    assert sus["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Output safety
# ---------------------------------------------------------------------------

def test_json_output_is_valid_and_safe(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    p = _write(tmp_path, _valid_manifest())
    validator.main(["--manifest", str(p), "--json"])
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "checks" in parsed
    assert parsed["ok"] is True


def test_validator_does_not_print_artifact_contents(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    # Create a manifest whose artifact path points at a file containing a secret marker.
    secret_marker = "SECRET-ARTIFACT-CONTENT-DO-NOT-PRINT"
    artifact_dir = tmp_path / "data" / "private_references" / "notebook_frozen" / "b" / "artifacts"
    artifact_dir.mkdir(parents=True)
    artifact_file = artifact_dir / "ref.bin"
    artifact_file.write_text(secret_marker, encoding="utf-8")

    manifest = _valid_manifest()
    manifest["local_artifact_paths"] = ["data/private_references/notebook_frozen/b/artifacts/ref.bin"]
    p = _write(tmp_path, manifest)

    validator.main(["--manifest", str(p)])
    out = capsys.readouterr().out
    # The validator must never read or echo artifact file contents.
    assert secret_marker not in out


def test_strict_mode_exits_nonzero_on_failure(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["local_artifact_paths"] = ["https://example.test/x"]
    p = _write(tmp_path, manifest)
    assert validator.main(["--manifest", str(p), "--strict"]) == 1


def test_url_manifest_path_is_rejected() -> None:
    assert validator.main(["--manifest", "https://example.test/manifest.json", "--strict"]) == 1
