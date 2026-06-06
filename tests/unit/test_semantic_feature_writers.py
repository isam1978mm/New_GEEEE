from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from app.pipeline.parity import ParityPathError
from app.pipeline.parity.semantic_feature_writers import (
    AI_BEH_EXTENDED_OUTPUT_NAMES,
    AI_BEH_RELATION_OUTPUT_NAMES,
    compute_ai_beh_extended_features,
    compute_ai_beh_relation_features,
    write_ai_beh_extended_feature_npy_outputs,
    write_ai_beh_relation_feature_npy_outputs,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
}


def _bands() -> dict[str, np.ndarray]:
    return {
        "B2": np.array([[1.5, 5.0], [2.0, 0.0]], dtype=np.float64),
        "B3": np.array([[1.0, 0.0], [2.0, 4.0]], dtype=np.float64),
        "B4": np.array([[3.0, 5.0], [6.0, 8.0]], dtype=np.float64),
        "B8": np.array([[7.0, -5.0], [10.0, 8.0]], dtype=np.float64),
        "B11": np.array([[9.0, 4.0], [12.0, 0.0]], dtype=np.float64),
        "B12": np.array([[3.0, 0.0], [6.0, 0.0]], dtype=np.float64),
    }


def test_ai_beh_relation_formula_family_computes_expected_values() -> None:
    outputs = compute_ai_beh_relation_features(_bands())

    assert set(outputs) == set(AI_BEH_RELATION_OUTPUT_NAMES)
    np.testing.assert_allclose(
        outputs["AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif"],
        np.array([[0.4, np.nan], [0.25, 0.0]], dtype=np.float32),
        equal_nan=True,
    )
    np.testing.assert_allclose(
        outputs["AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif"],
        np.array([[3.0, np.nan], [3.0, 2.0]], dtype=np.float32),
        equal_nan=True,
    )
    np.testing.assert_allclose(
        outputs["AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif"],
        np.array([[3.0, np.nan], [2.0, np.nan]], dtype=np.float32),
        equal_nan=True,
    )


def test_ai_beh_extended_formula_family_computes_expected_values() -> None:
    outputs = compute_ai_beh_extended_features(_bands())

    assert tuple(outputs) == AI_BEH_EXTENDED_OUTPUT_NAMES
    np.testing.assert_allclose(
        outputs["AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif"],
        np.array([[3.0 / 9.0, 0.0], [6.0 / 12.0, np.nan]], dtype=np.float32),
        equal_nan=True,
    )
    np.testing.assert_allclose(
        outputs["AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif"],
        np.array([[2.0, 1.0], [3.0, np.nan]], dtype=np.float32),
        equal_nan=True,
    )
    np.testing.assert_allclose(
        outputs["AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif"],
        np.array(
            [
                [10.0 / 9.001, 0.0 / 4.001],
                [16.0 / 12.001, 16.0 / 0.001],
            ],
            dtype=np.float32,
        ),
        rtol=1e-6,
        equal_nan=True,
    )


def test_ai_beh_extended_writer_returns_exactly_selected_canonical_names() -> None:
    outputs = compute_ai_beh_extended_features(_bands())

    assert tuple(outputs) == (
        "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
        "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
        "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
    )


def test_zero_and_near_zero_denominators_become_nan() -> None:
    bands = {
        "B2": np.array([[2.0]], dtype=np.float64),
        "B3": np.array([[1e-8]], dtype=np.float64),
        "B4": np.array([[1.0]], dtype=np.float64),
        "B8": np.array([[-1.0]], dtype=np.float64),
        "B11": np.array([[2.0]], dtype=np.float64),
        "B12": np.array([[1e-8]], dtype=np.float64),
    }

    outputs = compute_ai_beh_relation_features(bands, denominator_epsilon=1e-6)

    assert np.isnan(outputs["AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif"][0, 0])
    assert np.isnan(outputs["AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif"][0, 0])
    assert np.isnan(outputs["AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif"][0, 0])


def test_ai_beh_extended_zero_and_near_zero_denominators_become_nan() -> None:
    bands = {
        "B2": np.array([[2.0, 1e-8, 2.0]], dtype=np.float64),
        "B4": np.array([[1.0, 1.0, 1.0]], dtype=np.float64),
        "B8": np.array([[1.0, 1.0, 1.0]], dtype=np.float64),
        "B11": np.array([[1e-8, 2.0, -0.001]], dtype=np.float64),
        "B12": np.array([[1.0, 1.0, 1.0]], dtype=np.float64),
    }

    outputs = compute_ai_beh_extended_features(bands, denominator_epsilon=1e-6)

    assert np.isnan(outputs["AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif"][0, 0])
    assert np.isnan(outputs["AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif"][0, 1])
    assert np.isnan(outputs["AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif"][0, 2])


def test_outputs_use_documented_float32_dtype_policy() -> None:
    outputs = {
        **compute_ai_beh_relation_features(_bands()),
        **compute_ai_beh_extended_features(_bands()),
    }

    for array in outputs.values():
        assert array.dtype == np.float32


def test_ai_beh_extended_outputs_do_not_mutate_inputs() -> None:
    bands = _bands()
    originals = {name: array.copy() for name, array in bands.items()}

    compute_ai_beh_extended_features(bands)

    for name, original in originals.items():
        np.testing.assert_array_equal(bands[name], original)


def test_shape_mismatch_is_rejected() -> None:
    bands = _bands()
    bands["B12"] = np.ones((3, 3), dtype=np.float32)

    with pytest.raises(ValueError, match="same 2D shape"):
        compute_ai_beh_relation_features(bands)


def test_non_2d_inputs_are_rejected() -> None:
    bands = _bands()
    bands["B8"] = np.ones((1, 2, 2), dtype=np.float32)

    with pytest.raises(ValueError, match="2D"):
        compute_ai_beh_relation_features(bands)


def test_missing_required_band_is_rejected() -> None:
    bands = _bands()
    bands.pop("B11")

    with pytest.raises(ValueError, match="missing required bands"):
        compute_ai_beh_relation_features(bands)


def test_ai_beh_extended_missing_required_band_is_rejected() -> None:
    bands = _bands()
    bands.pop("B2")

    with pytest.raises(ValueError, match="missing required bands"):
        compute_ai_beh_extended_features(bands)


def test_writer_outputs_stay_under_run_dir_and_preserve_metadata(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    reference_profile = {
        "crs": "EPSG:32637",
        "transform": [10.0, 0.0, 500000.0, 0.0, -10.0, 4100000.0],
        "width": 2,
        "height": 2,
        "nodata": "nan",
    }

    report = write_ai_beh_relation_feature_npy_outputs(
        run_dir,
        _bands(),
        reference_profile=reference_profile,
    )

    assert report["writer_family"] == "ai_beh_relation_semantic_features"
    assert report["target_mode"] == "notebook_parity_private"
    assert report["runtime_output_verified"] is True
    assert report["notebook_value_parity_verified"] is False
    assert report["reference_profile"] == reference_profile
    for output_path in report["outputs"].values():
        path = Path(output_path)
        assert path.is_file()
        assert path.suffix == ".npy"
        assert path.resolve().is_relative_to(run_dir.resolve())


def test_ai_beh_extended_writer_outputs_stay_under_run_dir_and_private(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    report = write_ai_beh_extended_feature_npy_outputs(run_dir, _bands())

    assert report["writer_family"] == "ai_beh_extended_semantic_features"
    assert report["target_mode"] == "notebook_parity_private"
    assert report["artifact_class"] == "LOCAL_SENSITIVE"
    assert report["http_servable"] is False
    assert report["frontend_visible"] is False
    assert report["downloadable_via_api"] is False
    assert report["runtime_output_verified"] is True
    assert report["notebook_value_parity_verified"] is False
    assert tuple(report["outputs"]) == AI_BEH_EXTENDED_OUTPUT_NAMES
    for output_path in report["outputs"].values():
        path = Path(output_path)
        assert path.is_file()
        assert path.suffix == ".npy"
        assert path.resolve().is_relative_to(run_dir.resolve())


def test_writer_rejects_paths_outside_run_dir(tmp_path: Path) -> None:
    with pytest.raises(ParityPathError):
        write_ai_beh_relation_feature_npy_outputs(
            tmp_path / "run",
            _bands(),
            output_relative_dir="../outside",
        )
    with pytest.raises(ParityPathError):
        write_ai_beh_extended_feature_npy_outputs(
            tmp_path / "run",
            _bands(),
            output_relative_dir="../outside",
        )


def test_writer_creates_no_artifacts_outside_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_ai_beh_relation_feature_npy_outputs(run_dir, _bands())

    outside_files = [
        path
        for path in tmp_path.rglob("*")
        if path.is_file() and not path.resolve().is_relative_to(run_dir.resolve())
    ]
    assert outside_files == []
    assert not [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_phase_c_writer_adds_no_earth_engine_or_live_pipeline_calls() -> None:
    import app.pipeline.parity.semantic_feature_writers as module

    source = inspect.getsource(module)

    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "notebook_value_parity_verified=True" not in source
