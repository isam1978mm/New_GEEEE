from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.cli import hypercube_tensor_verify as cli
from app.pipeline.parity.hypercube_tensor_verify import (
    HYPERCUBE_TENSOR_REPORT_RELATIVE_PATH,
    HYPERCUBE_TENSOR_SPECS,
    HYPERCUBE_TENSOR_VERIFICATION_SCHEMA_VERSION,
    verify_hypercube_tensor_parity,
)
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME


def _load_report(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_npy(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, values)


def _write_tensor_outputs(root: Path, *, base_value: float = 1.0, reference_names: bool = False) -> None:
    hypercube = np.arange(36, dtype=np.float32).reshape(9, 2, 2) + np.float32(base_value)
    radar = np.arange(16, dtype=np.float32).reshape(2, 2, 4) + np.float32(base_value)
    _write_npy(root / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy", hypercube)
    radar_name = "RADAR_STACK_HWC_640_source_locked_demo.npy" if reference_names else "RADAR_STACK_HWC_640_app.npy"
    _write_npy(root / "NPY_STACKS" / radar_name, radar)


def _write_bundle_manifest(bundle: Path) -> None:
    files = []
    for path in sorted((bundle / "NPY_STACKS").glob("*.npy")):
        data = path.read_bytes()
        files.append(
            {
                "relative_path": path.relative_to(bundle).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "role": "hypercube_tensor",
            }
        )
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z",
        "bundle_name": "synthetic_hypercube_tensor_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _valid_bundle(tmp_path: Path, *, base_value: float = 1.0) -> Path:
    bundle = tmp_path / "bundle"
    _write_tensor_outputs(bundle, base_value=base_value, reference_names=True)
    _write_bundle_manifest(bundle)
    return bundle


def _write_grid_manifest(root: Path, *, origin_x: float, origin_y: float) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "epsg": 32637,
        "scale_m": 10,
        "size_px": 640,
        "crs_transform": [10.0, 0.0, origin_x, 0.0, -10.0, origin_y],
    }
    (root / "grid_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_reference_run_manifest(root: Path, *, origin_x: float, origin_y: float) -> None:
    path = root / "QA" / "RUN_MANIFEST.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "CRS": "EPSG:32637",
        "SCALE": 10,
        "OUT_SIZE": 640,
        "crsTransform": [10.0, 0.0, origin_x, 0.0, -10.0, origin_y],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_specs_are_source_locked_to_json_and_notebook() -> None:
    sourcelocked = json.loads(
        Path("docs/parity_expected_outputs_sourcelocked.json").read_text(encoding="utf-8")
    )
    entries = {entry["id"]: entry for entry in sourcelocked["entries"]}
    tensor_paths = set(entries["hypercube_tensor_outputs"]["paths"])
    assert "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy" in tensor_paths
    assert "NPY_STACKS/RADAR_STACK_HWC_640_*.npy" in tensor_paths

    specs = {spec.logical_name: spec for spec in HYPERCUBE_TENSOR_SPECS}
    assert specs["final_tesla_v7_2_hypercube_npy"].reference_locators == (
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
    )
    assert specs["radar_stack_hwc_640_npy"].reference_locators == (
        "NPY_STACKS/RADAR_STACK_HWC_640_*.npy",
    )

    notebook = json.loads(Path("notebooks/new.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert 'stack_path = os.path.join(STACKS_DIR, f"RADAR_STACK_HWC_640_{tag}.npy")' in source
    assert "np.save(stack_path, cube)" in source
    assert 'npy_out = os.path.join(STACK_DIR, "FINAL_TESLA_V7_2_HYPERCUBE.npy")' in source
    assert "np.save(npy_out, hypercube)" in source


def test_matching_tensors_pass_and_report_required_fields(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)

    result = verify_hypercube_tensor_parity(app_dir, bundle, tmp_path / "run", "run-pass")
    report = _load_report(result.report_path)
    outputs = {item["logical_name"]: item for item in report["outputs"]}
    hypercube = outputs["final_tesla_v7_2_hypercube_npy"]
    radar = outputs["radar_stack_hwc_640_npy"]

    assert result.overall_status == "passed"
    assert report["schema_version"] == HYPERCUBE_TENSOR_VERIFICATION_SCHEMA_VERSION
    assert hypercube["status"] == "passed"
    assert hypercube["app_present"] is True
    assert hypercube["reference_present"] is True
    assert hypercube["shape_match"] is True
    assert hypercube["dtype_match"] is True
    assert hypercube["app_finite_count"] == 36
    assert hypercube["app_nan_count"] == 0
    assert hypercube["app_inf_count"] == 0
    assert hypercube["reference_finite_count"] == 36
    assert hypercube["reference_nan_count"] == 0
    assert hypercube["reference_inf_count"] == 0
    assert hypercube["compared_element_count"] == 36
    assert hypercube["max_abs_diff"] == 0.0
    assert hypercube["mean_abs_diff"] == 0.0
    assert hypercube["allclose_pass"] is True
    assert hypercube["sha256_match"] is True
    assert radar["status"] == "passed"
    assert radar["compared_element_count"] == 16
    assert hypercube["channel_count"] == 9
    assert hypercube["per_channel"][0]["channel_name"] == "AI_READY_640_Secret_Gold_Halo"
    assert radar["channel_count"] == 4
    assert radar["per_channel"][0]["channel_name"] == "VV_dB"


def test_non_comparable_grid_blocks_real_parity_classification(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)
    _write_grid_manifest(app_dir, origin_x=100.0, origin_y=200.0)
    _write_reference_run_manifest(bundle, origin_x=1000.0, origin_y=2000.0)

    result = verify_hypercube_tensor_parity(app_dir, bundle, tmp_path / "run", "run-grid")
    report = _load_report(result.report_path)

    assert result.overall_status == "blocked_needs_app_hypercube_tensor_run"
    assert report["run_contract"]["status"] == "not_comparable"
    assert report["run_contract"]["epsg_match"] is True
    assert report["run_contract"]["scale_match"] is True
    assert report["run_contract"]["size_match"] is True
    assert report["run_contract"]["transform_match"] is False
    assert report["run_contract"]["origin_delta"] == [-900.0, -1800.0]


def test_missing_app_output_is_incomplete(tmp_path: Path) -> None:
    bundle = _valid_bundle(tmp_path)

    result = verify_hypercube_tensor_parity(tmp_path / "app", bundle, tmp_path / "run", "run-missing")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert {item["status"] for item in report["outputs"]} == {"missing_app_output"}


def test_shape_dtype_and_value_mismatches_are_reported(tmp_path: Path) -> None:
    bundle = _valid_bundle(tmp_path)
    app_shape = tmp_path / "app-shape"
    app_dtype = tmp_path / "app-dtype"
    app_value = tmp_path / "app-value"
    _write_tensor_outputs(app_shape)
    _write_tensor_outputs(app_dtype)
    _write_tensor_outputs(app_value)
    _write_npy(app_shape / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy", np.ones((8, 2, 2), dtype=np.float32))
    _write_npy(app_dtype / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy", np.ones((9, 2, 2), dtype=np.int16))
    bad = np.arange(36, dtype=np.float32).reshape(9, 2, 2) + np.float32(1.0)
    bad[0, 0, 0] = 999.0
    _write_npy(app_value / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy", bad)

    shape = verify_hypercube_tensor_parity(app_shape, bundle, tmp_path / "run-shape", "run-shape")
    dtype = verify_hypercube_tensor_parity(app_dtype, bundle, tmp_path / "run-dtype", "run-dtype")
    value = verify_hypercube_tensor_parity(app_value, bundle, tmp_path / "run-value", "run-value")

    assert _output_status(shape.report_path, "final_tesla_v7_2_hypercube_npy") == "shape_mismatch"
    assert _output_status(dtype.report_path, "final_tesla_v7_2_hypercube_npy") == "dtype_mismatch"
    assert _output_status(value.report_path, "final_tesla_v7_2_hypercube_npy") == "value_mismatch"


def _output_status(report_path: Path, logical_name: str) -> str:
    report = _load_report(report_path)
    return str({item["logical_name"]: item for item in report["outputs"]}[logical_name]["status"])


def test_report_path_traversal_is_blocked(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)

    try:
        verify_hypercube_tensor_parity(
            app_dir,
            bundle,
            tmp_path / "run",
            "run-bad-path",
            report_relative_path="../escape.json",
        )
    except ValueError as exc:
        assert "path traversal" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("path traversal should be blocked")


def test_verifier_does_not_create_tif_or_npy_under_run_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)
    run_dir = tmp_path / "run"

    result = verify_hypercube_tensor_parity(app_dir, bundle, run_dir, "run-no-output-writes")

    assert result.report_path == run_dir / HYPERCUBE_TENSOR_REPORT_RELATIVE_PATH
    assert not [path for path in run_dir.rglob("*") if path.suffix.lower() in {".npy", ".tif", ".tiff"}]


def test_cli_refuses_invalid_reference_bundle(tmp_path: Path, capsys) -> None:
    app_dir = tmp_path / "app"
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    _write_tensor_outputs(app_dir)

    exit_code = cli.main(["--app-output-dir", str(app_dir), "--bundle-dir", str(bundle)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "reference_invalid"
    assert "outputs" not in payload


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app_dir),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
        ]
    )
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert payload["overall_status"] == "passed"
    assert str(tmp_path) not in out
    assert ".npy" not in out
    assert "report_path" not in out
    assert "final_tesla_v7_2_hypercube_npy" in payload["per_output"]


def test_cli_show_details_includes_relative_paths(tmp_path: Path, capsys) -> None:
    app_dir = tmp_path / "app"
    bundle = _valid_bundle(tmp_path)
    _write_tensor_outputs(app_dir)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app_dir),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
            "--show-details",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["report_path"] == HYPERCUBE_TENSOR_REPORT_RELATIVE_PATH
    assert "outputs" in payload
    assert all(not Path(item["app_path"]).is_absolute() for item in payload["outputs"])
    assert any(item["app_sha256"] for item in payload["outputs"])
