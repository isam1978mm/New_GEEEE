from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import Settings
from app.db.models import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.classifier import ClassifierStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME


def test_classifier_stage_writes_redacted_public_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "gee_screening.db")
    grid_spec = build_run_grid(43.6532, -79.3832)
    _write_classifier_inputs(run_dir, grid_spec.size)

    result = asyncio.run(
        ClassifierStage().run(
            StageContext(run_id="run-1", settings=settings, run_dir=run_dir)
        )
    )

    artifacts = {artifact.name: artifact for artifact in result.artifacts}
    expected_paths = {
        "experimental_classifications": "experimental/classifications.csv",
        "experimental_summary": "experimental/summary.json",
        "experimental_neutral_labels": "experimental/neutral_target_labels.json",
    }
    assert {name: artifact.relative_path for name, artifact in artifacts.items()} == expected_paths
    for artifact in artifacts.values():
        assert artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
        assert artifact.http_servable is True
        assert (run_dir / artifact.relative_path).is_file()

    classifications = list(
        csv.DictReader((run_dir / "experimental" / "classifications.csv").open("r", encoding="utf-8", newline=""))
    )
    assert len(classifications) == 2
    assert all(row["class_id"].startswith("Class_") for row in classifications)
    assert all("lat" not in {key.casefold() for key in row} for row in classifications)

    summary = json.loads((run_dir / "experimental" / "summary.json").read_text(encoding="utf-8"))
    assert summary["object_count"] == 2
    assert summary["cluster_count"] == 1

    neutral_labels = json.loads(
        (run_dir / "experimental" / "neutral_target_labels.json").read_text(encoding="utf-8")
    )
    assert len(neutral_labels["object_labels"]) == 2
    assert neutral_labels["cluster_labels"][0]["dominant_class_id"].startswith("Class_")


def _write_classifier_inputs(run_dir: Path, grid_size: int) -> None:
    hypercube = np.zeros((grid_size, grid_size, 3), dtype=np.float32)
    hypercube[:, :, 0] = 0.44
    hypercube[:, :, 1] = 0.71
    hypercube[:, :, 2] = 1.0
    np.save(run_dir / HYPERCUBE_NPY_NAME, hypercube)

    anomaly = np.zeros((grid_size, grid_size), dtype=np.float32)
    anomaly[32:36, 40:44] = 0.96
    anomaly[48:52, 56:60] = 0.83
    Image.fromarray(anomaly).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")

    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max"],
        [
            {"object_id": 1, "cluster_id": 0, "row_min": 32, "row_max": 35, "col_min": 40, "col_max": 43},
            {"object_id": 2, "cluster_id": 0, "row_min": 48, "row_max": 51, "col_min": 56, "col_max": 59},
        ],
    )
    _write_csv(
        run_dir / CLUSTERS_SUMMARY_NAME,
        ["cluster_id", "object_count", "total_area_px", "mean_object_area_px", "max_object_anomaly"],
        [{"cluster_id": 0, "object_count": 2, "total_area_px": 32, "mean_object_area_px": 16.0, "max_object_anomaly": 0.96}],
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
