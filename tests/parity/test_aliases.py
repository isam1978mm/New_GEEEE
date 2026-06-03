import json

import pytest

from app.pipeline.parity.aliases import (
    DEFAULT_RASTER_TENSOR_ALIAS_SPECS,
    AliasSpec,
    AliasSourceMissingError,
    copy_alias,
    create_alias_plan,
    get_default_alias_spec,
)
from app.pipeline.parity.manifest import ParityPathError


def _write_bytes(path, data: bytes = b"fixture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_alias_plan_preserves_source_and_notebook_target_name(tmp_path):
    run_dir = tmp_path / "run"
    _write_bytes(run_dir / "dem.tif", b"dem")

    plan = create_alias_plan(run_dir, get_default_alias_spec("dem_640"))

    assert plan.source_path == (run_dir / "dem.tif").resolve()
    assert plan.parity_path == (run_dir / "parity" / "DEM_GEO8_TIFS" / "DEM_640.tif").resolve()
    assert plan.parity_run_path == "parity/DEM_GEO8_TIFS/DEM_640.tif"
    assert plan.entry.notebook_name_or_pattern == "DEM_640.tif"
    assert plan.entry.source_path == "dem.tif"


def test_dem_alias_copy_writes_file_and_manifest_entry(tmp_path):
    run_dir = tmp_path / "run"
    _write_bytes(run_dir / "dem.tif", b"dem-bytes")

    result = copy_alias(run_dir, "run-dem", get_default_alias_spec("dem_640"))
    manifest = _read_json(result.manifest_path)
    entry = manifest["entries"][0]

    assert result.status == "copied"
    assert (run_dir / "parity" / "DEM_GEO8_TIFS" / "DEM_640.tif").read_bytes() == b"dem-bytes"
    assert entry["runtime_output_verified"] is True
    assert entry["notebook_value_parity_verified"] is False
    assert entry["target_mode"] == "notebook_parity"
    assert entry["target_mode"] != "public_shared"
    assert entry["http_servable"] is False
    assert entry["requires_coordinates"] is False
    assert entry["probability_only_required"] is False


def test_sar_alias_copy_example(tmp_path):
    run_dir = tmp_path / "run"
    _write_bytes(run_dir / "npy_radar_bands" / "VV_dB.npy", b"npy-vv")

    result = copy_alias(run_dir, "run-sar", get_default_alias_spec("radar_vv_db_npy"))

    assert result.status == "copied"
    assert (
        run_dir / "parity" / "NPY_RADAR_BANDS" / "RADAR_VV_dB_640_app.npy"
    ).read_bytes() == b"npy-vv"
    assert result.entry.family == "SAR/radar outputs"
    assert result.entry.artifact_class == "FILESYSTEM_ONLY"


def test_hypercube_alias_copy_example(tmp_path):
    run_dir = tmp_path / "run"
    _write_bytes(run_dir / "hypercube.npy", b"cube")

    result = copy_alias(run_dir, "run-cube", get_default_alias_spec("hypercube_npy"))

    assert result.status == "copied"
    assert (
        run_dir / "parity" / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy"
    ).read_bytes() == b"cube"
    assert result.entry.family == "hypercube/tensor outputs"
    assert result.entry.notebook_value_parity_verified is False


def test_alias_copy_blocks_source_path_traversal(tmp_path):
    run_dir = tmp_path / "run"
    spec = AliasSpec(
        id="bad_source",
        source_paths=("../outside.tif",),
        parity_path="DEM_GEO8_TIFS/outside.tif",
        notebook_name_or_pattern="outside.tif",
        family="DEM/terrain outputs",
    )

    with pytest.raises(ParityPathError, match="path traversal"):
        create_alias_plan(run_dir, spec)


def test_alias_copy_blocks_parity_path_traversal(tmp_path):
    run_dir = tmp_path / "run"
    _write_bytes(run_dir / "dem.tif", b"dem")
    spec = AliasSpec(
        id="bad_target",
        source_paths=("dem.tif",),
        parity_path="../escape.tif",
        notebook_name_or_pattern="escape.tif",
        family="DEM/terrain outputs",
    )

    with pytest.raises(ParityPathError, match="path traversal"):
        create_alias_plan(run_dir, spec)


def test_missing_source_fails_clearly(tmp_path):
    run_dir = tmp_path / "run"

    with pytest.raises(AliasSourceMissingError, match="dem.tif"):
        copy_alias(run_dir, "run-missing", get_default_alias_spec("dem_640"))


def test_default_alias_specs_do_not_default_to_public_or_http_serving(tmp_path):
    run_dir = tmp_path / "run"
    for spec in DEFAULT_RASTER_TENSOR_ALIAS_SPECS:
        _write_bytes(run_dir / spec.source_paths[0], spec.id.encode("utf-8"))
        result = copy_alias(run_dir, f"run-{spec.id}", spec)

        assert result.entry.target_mode == "notebook_parity"
        assert result.entry.target_mode != "public_shared"
        assert result.entry.http_servable is False
        assert result.entry.requires_coordinates is False
