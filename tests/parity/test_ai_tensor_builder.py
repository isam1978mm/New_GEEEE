import csv
import json

import numpy as np

from app.pipeline.parity.ai_tensor_builder import (
    FULL_TENSOR_BAND_SPECS,
    build_plan_b29_ai_tensors_from_bands,
    write_plan_b29_ai_tensor_builder_outputs,
)


def _source_bands(size: int = 32) -> dict[str, np.ndarray]:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    base = (xx + yy) / max(float(2 * size - 2), 1.0)
    bands = {}
    for index, (name, _keywords) in enumerate(FULL_TENSOR_BAND_SPECS, start=1):
        bands[name] = np.mod(base + index * 0.017, 1.0).astype(np.float32)
    return bands


def test_plan_b29_builds_expected_tensor_shapes_and_ranges():
    products = build_plan_b29_ai_tensors_from_bands(_source_bands())

    assert products["full_tensor"].shape == (52, 32, 32)
    assert products["yolo_rgb"].shape == (3, 32, 32)
    assert products["cnn_tensor"].shape == (24, 32, 32)
    assert products["swin_tensor"].shape == (16, 32, 32)
    assert products["pca_rgb"].shape == (3, 32, 32)
    assert products["negative_mask"].shape == (32, 32)

    for key in ["full_tensor", "yolo_rgb", "cnn_tensor", "swin_tensor", "pca_rgb", "negative_mask"]:
        arr = products[key]
        assert arr.dtype == np.float32
        assert np.isfinite(arr).all()

    assert float(products["yolo_rgb"].min()) >= 0.0
    assert float(products["yolo_rgb"].max()) <= 1.0
    assert set(np.unique(products["negative_mask"])) <= {0.0, 1.0}
    assert products["missing_source_bands_zero_filled"] == []


def test_plan_b29_zero_fills_missing_sources_but_preserves_shape():
    bands = _source_bands()
    bands.pop("Secret_Gold_Halo")

    products = build_plan_b29_ai_tensors_from_bands(bands)

    assert products["full_tensor"].shape == (52, 32, 32)
    assert "Secret_Gold_Halo" in products["missing_source_bands_zero_filled"]


def test_plan_b29_writes_filesystem_only_tensor_outputs(tmp_path):
    paths = write_plan_b29_ai_tensor_builder_outputs(
        tmp_path,
        "run-29",
        source_bands=_source_bands(),
    )

    expected = {
        "full_tensor",
        "yolo_rgb",
        "yolo_visual",
        "cnn_tensor",
        "swin_tensor",
        "pca_rgb",
        "negative_mask",
        "report_json",
        "bands_csv",
    }
    assert set(paths) == expected
    for path in paths.values():
        assert path.is_file()

    full = np.load(paths["full_tensor"])
    yolo = np.load(paths["yolo_rgb"])
    cnn = np.load(paths["cnn_tensor"])
    swin = np.load(paths["swin_tensor"])
    pca = np.load(paths["pca_rgb"])
    negative = np.load(paths["negative_mask"])

    assert full.shape == (52, 32, 32)
    assert yolo.shape == (3, 32, 32)
    assert cnn.shape == (24, 32, 32)
    assert swin.shape == (16, 32, 32)
    assert pca.shape == (3, 32, 32)
    assert negative.shape == (32, 32)

    report = json.loads(paths["report_json"].read_text(encoding="utf-8"))
    assert report["source_cell"] == "cell_148"
    assert report["status"] == "implemented_tensor_builder_only"
    assert report["privacy"] == "FILESYSTEM_ONLY"
    assert report["http_servable"] is False
    assert report["frontend_visible"] is False
    assert report["downloadable_via_api"] is False
    assert report["trains_models"] is False
    assert report["runs_inference"] is False
    assert report["downloads_weights"] is False
    assert report["adds_heavy_ml_dependencies"] is False
    assert report["creates_model_artifacts"] is False
    assert report["shapes"]["full"] == [52, 32, 32]
    assert report["shapes"]["yolo"] == [3, 32, 32]
    assert report["shapes"]["cnn"] == [24, 32, 32]
    assert report["shapes"]["swin"] == [16, 32, 32]

    with paths["bands_csv"].open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert {row["tensor"] for row in rows} == {"full", "YOLOv11", "CNN", "Swin/SegFormer", "PCA_RGB", "negative_mask"}


def test_plan_b29_module_does_not_expose_model_execution_functions():
    import app.pipeline.parity.ai_tensor_builder as module

    forbidden_prefixes = (
        "train_",
        "infer_",
        "predict_",
        "classify_",
        "run_model_",
        "load_model_",
        "download_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]
    assert forbidden == []
