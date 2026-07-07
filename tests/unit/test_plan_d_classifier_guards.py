from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image

from app.pipeline.stages.classifier import _build_neutral_labels, _normalize_feature, build_classifier_results
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME


def test_classifier_uses_valid_mask_for_patch_features(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    grid_spec = build_run_grid(0.0, 0.0)
    hypercube = np.zeros((grid_spec.size, grid_spec.size, 3), dtype=np.float32)
    hypercube[32:36, 40:44, 0:2] = 1000.0
    hypercube[32:36, 40:44, 2] = 0.0
    hypercube[32, 40, 0:2] = 0.2
    hypercube[32, 40, 2] = 1.0
    np.save(run_dir / HYPERCUBE_NPY_NAME, hypercube)

    anomaly = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
    anomaly[32:36, 40:44] = 0.6
    Image.fromarray(anomaly).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")
    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max"],
        [{"object_id": 1, "cluster_id": 0, "row_min": 32, "row_max": 35, "col_min": 40, "col_max": 43}],
    )
    _write_csv(
        run_dir / CLUSTERS_SUMMARY_NAME,
        ["cluster_id", "object_count", "total_area_px", "mean_object_area_px", "max_object_anomaly"],
        [{"cluster_id": 0, "object_count": 1, "total_area_px": 16, "mean_object_area_px": 16.0, "max_object_anomaly": 0.6}],
    )

    classifications, _summary = build_classifier_results(run_dir)

    assert len(classifications) == 1
    assert float(classifications[0]["class_score"]) < 0.4


def test_classifier_preserves_negative_feature_values_before_scoring(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    grid_spec = build_run_grid(0.0, 0.0)
    hypercube = np.zeros((grid_spec.size, grid_spec.size, 3), dtype=np.float32)
    hypercube[48:52, 60:64, 0:2] = -0.75
    hypercube[48:52, 60:64, 2] = 1.0
    np.save(run_dir / HYPERCUBE_NPY_NAME, hypercube)

    anomaly = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
    Image.fromarray(anomaly).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")
    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max"],
        [{"object_id": 1, "cluster_id": 0, "row_min": 48, "row_max": 51, "col_min": 60, "col_max": 63}],
    )
    _write_csv(
        run_dir / CLUSTERS_SUMMARY_NAME,
        ["cluster_id", "object_count", "total_area_px", "mean_object_area_px", "max_object_anomaly"],
        [{"cluster_id": 0, "object_count": 1, "total_area_px": 16, "mean_object_area_px": 16.0, "max_object_anomaly": 0.0}],
    )

    classifications, _summary = build_classifier_results(run_dir)

    assert _normalize_feature(-1.25) == -1.25
    assert _normalize_feature(float("nan")) == 0.0
    assert classifications[0]["signal_mean"] == -0.75
    assert classifications[0]["signal_peak"] == 0.0
    assert classifications[0]["signal_spread"] == 0.0
    assert classifications[0]["class_score"] == 0.0


def test_cluster_dominant_class_id_is_most_frequent_not_alphabetical() -> None:
    labels = _build_neutral_labels(
        [
            {"object_id": 1, "cluster_id": 0, "class_id": "Class_B", "class_family": "x", "class_score": 0.8},
            {"object_id": 2, "cluster_id": 0, "class_id": "Class_A", "class_family": "x", "class_score": 0.9},
            {"object_id": 3, "cluster_id": 0, "class_id": "Class_B", "class_family": "x", "class_score": 0.7},
        ],
        {"classifier_version": "test", "object_count": 3, "cluster_count": 1},
    )

    assert labels["cluster_labels"][0]["dominant_class_id"] == "Class_B"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
