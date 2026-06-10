"""Unit tests for the D1A scope audit with the D1B source-locked baseline.

All bundles are synthetic and created under pytest ``tmp_path``; no real frozen
D1 reference artifacts are read or committed.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.cli import reference_scope_audit as cli
from app.pipeline.parity.reference_scope_audit import (
    DEM_FAMILY,
    DEM_SOURCE_LOCKED_OUTPUTS,
    REFERENCE_MANIFEST_NAME,
    STATUS_COMPLETE,
    STATUS_ERROR,
    STATUS_INCOMPLETE,
    TIER_ACCEPTED_NON_REPRODUCIBLE,
    TIER_PARKED_V6,
    TIER_REQUIRED,
    audit_reference_scope,
    load_expected_entries,
)


def _write_manifest(bundle: Path, relative_paths: list[str]) -> None:
    bundle.mkdir(parents=True, exist_ok=True)
    files = [
        {"relative_path": p, "sha256": "0" * 64, "size_bytes": 1, "role": "raster"}
        for p in relative_paths
    ]
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z",
        "bundle_name": "synthetic_scope_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _sourcelocked_baseline(tmp_path: Path) -> Path:
    """A small tiered baseline file mirroring the D1B source-locked schema."""

    doc = {
        "schema": "parity_expected_outputs_sourcelocked_v1",
        "scope_tiers": [
            TIER_REQUIRED,
            TIER_PARKED_V6,
            TIER_ACCEPTED_NON_REPRODUCIBLE,
        ],
        "entries": [
            {
                "id": "dem_source_locked",
                "family": DEM_FAMILY,
                "scope_tier": TIER_REQUIRED,
                "paths": list(DEM_SOURCE_LOCKED_OUTPUTS),
            },
            {
                "id": "report_640_outputs",
                "family": "REPORT_640 outputs",
                "scope_tier": TIER_REQUIRED,
                "paths": ["REPORT_640_Pottery_Report.tif"],
            },
            {
                "id": "v6_candidate_package_outputs",
                "family": "v6 candidate package outputs",
                "scope_tier": TIER_PARKED_V6,
                "paths": [
                    "paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip",
                    "request_zones_v6.csv",
                ],
            },
            {
                "id": "pre_rtc_sar_intermediates",
                "family": "pre-RTC SAR intermediates",
                "scope_tier": TIER_ACCEPTED_NON_REPRODUCIBLE,
                "paths": ["QA/sar/intermediates/pair_median/x.npy"],
            },
        ],
    }
    path = tmp_path / "sourcelocked.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _required_present_paths() -> list[str]:
    return list(DEM_SOURCE_LOCKED_OUTPUTS) + ["REPORT_640_Pottery_Report.tif"]


# --- DEM source-lock from notebook evidence ----------------------------------


def test_dem_baseline_is_source_locked_no_stale_names() -> None:
    paths = set(DEM_SOURCE_LOCKED_OUTPUTS)
    # Notebook writes aspect_deg, not aspect; and does NOT write tri/twi.
    assert "DEM_GEO8_TIFS/aspect_deg_640.tif" in paths
    assert "DEM_GEO8_TIFS/aspect_640.tif" not in paths
    assert "DEM_GEO8_TIFS/tri_100m_640.tif" not in paths
    assert "DEM_GEO8_TIFS/twi_640.tif" not in paths
    # The three curvature variants remain required.
    for curv in ("curv_laplacian_640", "curv_plan_640", "curv_profile_640"):
        assert f"DEM_GEO8_TIFS/{curv}.tif" in paths


def test_real_curvature_outputs_remain_required(tmp_path: Path) -> None:
    baseline = _sourcelocked_baseline(tmp_path)
    bundle = tmp_path / "bundle"
    # Bundle has every required path EXCEPT the curvature trio.
    present = [p for p in _required_present_paths() if "curv_" not in p]
    _write_manifest(bundle, present)

    result = audit_reference_scope(bundle, expected_outputs_path=baseline)
    assert result.status == STATUS_INCOMPLETE
    missing = result.missing_paths_by_family[DEM_FAMILY]
    assert "DEM_GEO8_TIFS/curv_laplacian_640.tif" in missing
    assert result.missing_required_count == 3


# --- tier behavior -----------------------------------------------------------


def test_parked_v6_does_not_fail_required_status(tmp_path: Path) -> None:
    baseline = _sourcelocked_baseline(tmp_path)
    bundle = tmp_path / "bundle"
    # All required present; NO V6 outputs present.
    _write_manifest(bundle, _required_present_paths())

    result = audit_reference_scope(bundle, expected_outputs_path=baseline)
    assert result.status == STATUS_COMPLETE  # missing V6 did not fail it
    assert result.counts_by_tier[TIER_PARKED_V6]["missing"] == 2
    assert result.missing_required_count == 0


def test_accepted_non_reproducible_does_not_fail_required_status(tmp_path: Path) -> None:
    baseline = _sourcelocked_baseline(tmp_path)
    bundle = tmp_path / "bundle"
    _write_manifest(bundle, _required_present_paths())

    result = audit_reference_scope(bundle, expected_outputs_path=baseline)
    assert result.status == STATUS_COMPLETE
    assert result.counts_by_tier[TIER_ACCEPTED_NON_REPRODUCIBLE]["missing"] == 1


def test_complete_when_all_required_present(tmp_path: Path) -> None:
    baseline = _sourcelocked_baseline(tmp_path)
    bundle = tmp_path / "bundle"
    _write_manifest(bundle, _required_present_paths() + ["extra/app_native.tif"])

    result = audit_reference_scope(bundle, expected_outputs_path=baseline)
    assert result.status == STATUS_COMPLETE
    assert result.missing_required_count == 0
    assert result.extra_count == 1
    assert "extra/app_native.tif" in result.extra_paths


def test_default_baseline_loads_and_is_source_locked() -> None:
    # The committed source-locked baseline drives the default load.
    entries = load_expected_entries()
    dem_required = {
        e.path for e in entries if e.family == DEM_FAMILY and e.scope_tier == TIER_REQUIRED
    }
    assert dem_required == set(DEM_SOURCE_LOCKED_OUTPUTS)
    assert any(e.scope_tier == TIER_PARKED_V6 for e in entries)


# --- error handling ----------------------------------------------------------


def test_malformed_manifest_fails_safely(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / REFERENCE_MANIFEST_NAME).write_text("{not-json", encoding="utf-8")
    result = audit_reference_scope(bundle, expected_outputs_path=_sourcelocked_baseline(tmp_path))
    assert result.status == STATUS_ERROR
    assert result.error is not None


def test_missing_manifest_fails_safely(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = audit_reference_scope(bundle, expected_outputs_path=_sourcelocked_baseline(tmp_path))
    assert result.status == STATUS_ERROR
    assert REFERENCE_MANIFEST_NAME in (result.error or "")


# --- CLI ---------------------------------------------------------------------


def test_cli_default_output_does_not_expose_detailed_paths(tmp_path: Path, capsys) -> None:
    secret_segment = "lat_35.59499_lon_36.12694"
    present = [p for p in DEM_SOURCE_LOCKED_OUTPUTS if "curv_" not in p]
    present.append(f"{secret_segment}/raster.tif")
    bundle = tmp_path / "bundle"
    _write_manifest(bundle, present)

    exit_code = cli.main(["--bundle-dir", str(bundle)])
    out = capsys.readouterr().out

    assert exit_code == 1  # curvature missing in default baseline
    payload = json.loads(out)
    assert set(payload) == {
        "status",
        "expected_required_count",
        "present_required_count",
        "missing_required_count",
        "extra_count",
        "missing_by_family",
        "present_by_family",
        "counts_by_tier",
        "error",
    }
    assert secret_segment not in out
    assert "extra_paths" not in out
    assert "missing_paths_by_family" not in out
    assert "curv_laplacian_640" not in out


def test_cli_show_details_includes_paths(tmp_path: Path, capsys) -> None:
    present = [p for p in DEM_SOURCE_LOCKED_OUTPUTS if "curv_" not in p]
    bundle = tmp_path / "bundle"
    _write_manifest(bundle, present)

    exit_code = cli.main(["--bundle-dir", str(bundle), "--show-details"])
    out = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(out)
    assert "missing_paths_by_family" in payload
    assert "missing_paths_by_tier" in payload
    assert "DEM_GEO8_TIFS/curv_laplacian_640.tif" in payload["missing_paths_by_family"][DEM_FAMILY]
