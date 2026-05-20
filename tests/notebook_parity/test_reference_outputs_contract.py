from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "reference_run_v1"
REFERENCE_MANIFEST_PATH = FIXTURE_ROOT / "reference_manifest.json"
IRON_SWIR_PROVENANCE_PATH = Path("docs/IRON_SWIR_PROVENANCE.md")

EXPECTED_OPTION_A = "Accepted decision: **Option A**"
IRON_SWIR_OPTION_A_RULE = "option_a_corrected_app_reference"
REJECTED_IRON_SWIR_RULES = {
    "checked_in_notebook_raster",
    "sign_flipped_notebook_raster",
}

FLOAT_TOLERANCES: dict[str, float] = {
    "dem.tif": 1e-5,
    "dem.npy": 1e-5,
    "VV_dB.tif": 1e-4,
    "VH_dB.tif": 1e-4,
    "logRatio_dB.tif": 1e-4,
    "incidence.tif": 1e-4,
    "slope.tif": 1e-4,
    "aspect.tif": 1e-4,
    "curvature.tif": 1e-4,
    "TPI.tif": 1e-4,
    "TRI.tif": 1e-4,
    "roughness.tif": 1e-4,
    "TWI.tif": 1e-4,
    "lst.tif": 1e-3,
    "NDVI.tif": 1e-4,
    "NDWI.tif": 1e-4,
    "NDMI.tif": 1e-4,
    "NBR.tif": 1e-4,
    "IRONOX.tif": 1e-4,
    "IRON_SWIR.tif": 1e-6,
    "BSI.tif": 1e-4,
    "hypercube.tif": 1e-5,
    "hypercube.npy": 1e-5,
    "pca_anomaly.tif": 1e-5,
    "pca_eigenvalues.json": 1e-6,
    "hypercube_band_stats.csv": 1e-6,
    "hypercube_norm_params.csv": 1e-6,
    "objects_index.csv": 1e-6,
    "clusters_summary.csv": 1e-6,
    "alignment_qa.json": 1e-6,
}

RASTER_FILES = {
    "dem.tif",
    "VV_dB.tif",
    "VH_dB.tif",
    "logRatio_dB.tif",
    "incidence.tif",
    "slope.tif",
    "aspect.tif",
    "curvature.tif",
    "TPI.tif",
    "TRI.tif",
    "roughness.tif",
    "TWI.tif",
    "lst.tif",
    "NDVI.tif",
    "NDWI.tif",
    "NDMI.tif",
    "NBR.tif",
    "IRONOX.tif",
    "IRON_SWIR.tif",
    "BSI.tif",
    "hypercube.tif",
    "pca_anomaly.tif",
}

NPY_FILES = {
    "dem.npy",
    "hypercube.npy",
}

CSV_FILES = {
    "hypercube_band_order.csv",
    "hypercube_band_stats.csv",
    "hypercube_norm_params.csv",
    "objects_index.csv",
    "clusters_summary.csv",
}

JSON_FILES = {
    "grid_manifest.json",
    "pca_eigenvalues.json",
    "alignment_qa.json",
}

FORBIDDEN_COORD_COLUMNS = {
    "latitude",
    "longitude",
    "lat",
    "lon",
    "lng",
    "geometry",
    "bounds",
    "bbox",
    "crs_transform",
    "transform",
}


@dataclass(frozen=True, slots=True)
class ManifestContext:
    root: Path
    reference_root: Path
    app_root: Path
    artifacts: dict[str, dict[str, Any]]


def test_reference_manifest_exists_or_skips() -> None:
    manifest = load_reference_manifest()

    assert manifest.reference_root.is_dir()
    assert manifest.app_root.is_dir()
    assert manifest.artifacts


def test_reference_rasters_match_contract_or_skip() -> None:
    require_option_a()
    manifest = load_reference_manifest()
    raster_names = sorted(name for name in manifest.artifacts if name in RASTER_FILES)
    if not raster_names:
        pytest.skip(f"missing reference artifact file: {REFERENCE_MANIFEST_PATH.as_posix()}")

    for name in raster_names:
        reference_path, app_path = resolve_artifact_pair(manifest, name)
        compare_raster_pair(name, reference_path, app_path)


def test_reference_arrays_match_contract_or_skip() -> None:
    require_option_a()
    manifest = load_reference_manifest()
    array_names = sorted(name for name in manifest.artifacts if name in NPY_FILES)
    if not array_names:
        pytest.skip(f"missing reference artifact file: {REFERENCE_MANIFEST_PATH.as_posix()}")

    for name in array_names:
        reference_path, app_path = resolve_artifact_pair(manifest, name)
        compare_npy_pair(name, reference_path, app_path)


def test_reference_tabular_and_json_match_contract_or_skip() -> None:
    require_option_a()
    manifest = load_reference_manifest()
    artifact_names = sorted(name for name in manifest.artifacts if name in CSV_FILES or name in JSON_FILES)
    if not artifact_names:
        pytest.skip(f"missing reference artifact file: {REFERENCE_MANIFEST_PATH.as_posix()}")

    for name in artifact_names:
        reference_path, app_path = resolve_artifact_pair(manifest, name)
        if name in CSV_FILES:
            compare_csv_pair(name, reference_path, app_path)
        else:
            compare_json_pair(name, reference_path, app_path)


def test_iron_swir_manifest_requires_option_a_rule(tmp_path: Path) -> None:
    manifest_path = write_reference_manifest(
        tmp_path,
        iron_swir_entry={
            "reference": "reference/IRON_SWIR.tif",
            "app": "app/IRON_SWIR.tif",
        },
    )
    manifest = load_reference_manifest_from_path(manifest_path)

    with pytest.raises(AssertionError, match="IRON_SWIR.tif reference manifest entry must declare comparison_rule"):
        validate_iron_swir_reference_rule(manifest.artifacts["IRON_SWIR.tif"])


def test_iron_swir_manifest_rejects_sign_flipped_notebook_rule(tmp_path: Path) -> None:
    manifest_path = write_reference_manifest(
        tmp_path,
        iron_swir_entry={
            "reference": "reference/IRON_SWIR.tif",
            "app": "app/IRON_SWIR.tif",
            "comparison_rule": "sign_flipped_notebook_raster",
        },
    )
    manifest = load_reference_manifest_from_path(manifest_path)

    with pytest.raises(AssertionError, match="must not use a checked-in notebook or sign-flipped notebook raster"):
        validate_iron_swir_reference_rule(manifest.artifacts["IRON_SWIR.tif"])


def test_iron_swir_manifest_accepts_option_a_rule(tmp_path: Path) -> None:
    manifest_path = write_reference_manifest(
        tmp_path,
        iron_swir_entry={
            "reference": "reference/IRON_SWIR.tif",
            "app": "app/IRON_SWIR.tif",
            "comparison_rule": IRON_SWIR_OPTION_A_RULE,
        },
    )
    manifest = load_reference_manifest_from_path(manifest_path)

    validate_iron_swir_reference_rule(manifest.artifacts["IRON_SWIR.tif"])


def require_option_a() -> None:
    text = IRON_SWIR_PROVENANCE_PATH.read_text(encoding="utf-8")
    if EXPECTED_OPTION_A not in text:
        pytest.skip(f"IRON_SWIR provenance decision is unresolved or not Option A: {IRON_SWIR_PROVENANCE_PATH.as_posix()}")


def load_reference_manifest() -> ManifestContext:
    return load_reference_manifest_from_path(REFERENCE_MANIFEST_PATH)


def load_reference_manifest_from_path(manifest_path: Path) -> ManifestContext:
    if not manifest_path.is_file():
        pytest.skip(f"missing reference artifact file: {manifest_path.as_posix()}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    reference_root = (manifest_path.parent / payload["reference_dir"]).resolve()
    app_root = (manifest_path.parent / payload["app_dir"]).resolve()
    artifacts = payload["artifacts"]
    return ManifestContext(
        root=manifest_path.parent.resolve(),
        reference_root=reference_root,
        app_root=app_root,
        artifacts=artifacts,
    )


def resolve_artifact_pair(manifest: ManifestContext, artifact_name: str) -> tuple[Path, Path]:
    entry = manifest.artifacts[artifact_name]
    if artifact_name == "IRON_SWIR.tif":
        validate_iron_swir_reference_rule(entry)
    reference_path = (manifest.root / entry.get("reference", f"{manifest.reference_root.name}/{artifact_name}")).resolve()
    app_path = (manifest.root / entry.get("app", f"{manifest.app_root.name}/{artifact_name}")).resolve()
    if not reference_path.is_file():
        pytest.skip(f"missing reference artifact file: {reference_path.as_posix()}")
    if not app_path.is_file():
        pytest.skip(f"missing reference artifact file: {app_path.as_posix()}")
    return reference_path, app_path


def validate_iron_swir_reference_rule(entry: dict[str, Any]) -> None:
    comparison_rule = entry.get("comparison_rule")
    assert comparison_rule, (
        "IRON_SWIR.tif reference manifest entry must declare comparison_rule="
        f"'{IRON_SWIR_OPTION_A_RULE}' for Option A validation"
    )
    assert comparison_rule not in REJECTED_IRON_SWIR_RULES, (
        "IRON_SWIR.tif reference manifest must not use a checked-in notebook or sign-flipped notebook raster; "
        f"got comparison_rule={comparison_rule!r}"
    )
    assert comparison_rule == IRON_SWIR_OPTION_A_RULE, (
        "IRON_SWIR.tif reference manifest must declare comparison_rule="
        f"'{IRON_SWIR_OPTION_A_RULE}' and compare against the corrected analytical/app reference "
        "using (B11 - B12) / (B11 + B12)"
    )


def compare_raster_pair(name: str, reference_path: Path, app_path: Path) -> None:
    reference_array = load_tiff_array(reference_path)
    app_array = load_tiff_array(app_path)

    assert reference_array.shape == app_array.shape

    reference_sidecar = load_sidecar(reference_path)
    app_sidecar = load_sidecar(app_path)

    assert reference_sidecar["crs"] == app_sidecar["crs"]
    assert reference_sidecar["transform"] == app_sidecar["transform"]
    assert reference_sidecar["nodata"] == app_sidecar["nodata"]
    assert reference_sidecar["dtype"] == app_sidecar["dtype"]
    assert (reference_sidecar["height"], reference_sidecar["width"]) == (app_sidecar["height"], app_sidecar["width"])

    assert_arrays_close(reference_array, app_array, tolerance_for(name))


def compare_npy_pair(name: str, reference_path: Path, app_path: Path) -> None:
    reference_array = np.load(reference_path)
    app_array = np.load(app_path)

    assert reference_array.shape == app_array.shape
    assert reference_array.dtype == app_array.dtype
    assert_arrays_close(reference_array, app_array, tolerance_for(name))

    if name == "hypercube.npy":
        assert reference_array.shape[-1] >= 1
        reference_valid_mask = reference_array[..., -1]
        app_valid_mask = app_array[..., -1]
        assert_arrays_close(reference_valid_mask, app_valid_mask, 0.0)


def compare_csv_pair(name: str, reference_path: Path, app_path: Path) -> None:
    with reference_path.open(encoding="utf-8", newline="") as handle:
        reference_rows = list(csv.DictReader(handle))
        reference_columns = list(reference_rows[0].keys()) if reference_rows else []
    with app_path.open(encoding="utf-8", newline="") as handle:
        app_rows = list(csv.DictReader(handle))
        app_columns = list(app_rows[0].keys()) if app_rows else []

    assert reference_columns == app_columns
    assert len(reference_rows) == len(app_rows)
    if name in {"objects_index.csv", "clusters_summary.csv"}:
        normalized_columns = {column.casefold() for column in reference_columns}
        assert normalized_columns.isdisjoint(FORBIDDEN_COORD_COLUMNS)

    for reference_row, app_row in zip(reference_rows, app_rows, strict=True):
        assert list(reference_row.keys()) == list(app_row.keys())
        for key in reference_row:
            compare_scalar(reference_row[key], app_row[key], tolerance_for(name))


def compare_json_pair(name: str, reference_path: Path, app_path: Path) -> None:
    reference_payload = json.loads(reference_path.read_text(encoding="utf-8"))
    app_payload = json.loads(app_path.read_text(encoding="utf-8"))
    compare_json_values(reference_payload, app_payload, tolerance_for(name), path=name)


def compare_json_values(reference_value: Any, app_value: Any, tolerance: float, *, path: str) -> None:
    if isinstance(reference_value, dict):
        assert isinstance(app_value, dict), path
        assert list(reference_value.keys()) == list(app_value.keys()), path
        for key in reference_value:
            compare_json_values(reference_value[key], app_value[key], tolerance, path=f"{path}.{key}")
        return
    if isinstance(reference_value, list):
        assert isinstance(app_value, list), path
        assert len(reference_value) == len(app_value), path
        for index, (left, right) in enumerate(zip(reference_value, app_value, strict=True)):
            compare_json_values(left, right, tolerance, path=f"{path}[{index}]")
        return
    compare_scalar(reference_value, app_value, tolerance)


def compare_scalar(reference_value: Any, app_value: Any, tolerance: float) -> None:
    if is_number(reference_value) and is_number(app_value):
        assert math.isclose(float(reference_value), float(app_value), rel_tol=0.0, abs_tol=tolerance)
        return
    assert reference_value == app_value


def assert_arrays_close(reference_array: np.ndarray, app_array: np.ndarray, tolerance: float) -> None:
    assert reference_array.shape == app_array.shape
    finite_mask = np.isfinite(reference_array) & np.isfinite(app_array)
    assert np.array_equal(np.isnan(reference_array), np.isnan(app_array))
    if np.any(finite_mask):
        max_error = np.max(np.abs(reference_array[finite_mask] - app_array[finite_mask]))
        assert float(max_error) <= tolerance


def load_sidecar(raster_path: Path) -> dict[str, Any]:
    sidecar_path = raster_path.with_name(f"{raster_path.name}.meta.json")
    if not sidecar_path.is_file():
        pytest.skip(f"missing reference artifact file: {sidecar_path.as_posix()}")
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


def load_tiff_array(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        frames = []
        for index in range(getattr(image, "n_frames", 1)):
            image.seek(index)
            frames.append(np.array(image, dtype=np.float32))
    if len(frames) == 1:
        return frames[0]
    return np.stack(frames, axis=0)


def tolerance_for(name: str) -> float:
    return FLOAT_TOLERANCES.get(name, 0.0)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool)


def write_reference_manifest(tmp_path: Path, *, iron_swir_entry: dict[str, Any]) -> Path:
    manifest_path = tmp_path / "reference_manifest.json"
    payload = {
        "reference_dir": "reference",
        "app_dir": "app",
        "artifacts": {
            "IRON_SWIR.tif": iron_swir_entry,
        },
    }
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path
