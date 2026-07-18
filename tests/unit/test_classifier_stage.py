from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.config import Settings
from app.db.models import ArtifactClass
from app.errors import StageError
from app.pipeline._base import StageContext
from app.pipeline.stages.classifier import (
    ClassifierStage,
    build_final_area_findings_summary,
    classify_area_finding,
)
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME


def test_classifier_stage_writes_core_artifacts_with_legacy_aliases(tmp_path: Path) -> None:
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
        "classifier_classifications": "classifier/classifications.csv",
        "classifier_summary": "classifier/summary.json",
        "classifier_neutral_labels": "classifier/neutral_target_labels.json",
        "experimental_classifications": "experimental/classifications.csv",
        "experimental_summary": "experimental/summary.json",
        "experimental_neutral_labels": "experimental/neutral_target_labels.json",
    }
    assert {name: artifact.relative_path for name, artifact in artifacts.items()} == expected_paths
    for artifact in artifacts.values():
        assert artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
        assert artifact.http_servable is True
        assert (run_dir / artifact.relative_path).is_file()
    assert artifacts["experimental_summary"].metadata == {"alias_for": "classifier_summary", "deprecated": True}

    classifications = list(
        csv.DictReader((run_dir / "classifier" / "classifications.csv").open("r", encoding="utf-8", newline=""))
    )
    assert len(classifications) == 2
    assert all(row["class_id"].startswith("Class_") for row in classifications)
    assert all(row["classifier_version"] == "core_v1" for row in classifications)
    assert all(row["classifier_quality"] == "input_contract_validated" for row in classifications)
    assert all("lat" not in {key.casefold() for key in row} for row in classifications)

    summary = json.loads((run_dir / "classifier" / "summary.json").read_text(encoding="utf-8"))
    assert summary["classifier_stage"] == "core"
    assert summary["classifier_quality"] == "input_contract_validated"
    assert summary["classifier_version"] == "core_v1"
    assert summary["output_contract"] == "core_classifier_outputs_v2"
    assert summary["input_contract"] == "classifier_inputs_v1"
    assert summary["object_count"] == 2
    assert summary["cluster_count"] == 1
    final_findings = summary["final_area_findings"]
    assert final_findings["summary_version"] == "final_area_findings_v1"
    assert final_findings["score_type"] == "app_score"
    assert final_findings["depth_status"] == "not_available"
    assert final_findings["ranked_findings"]
    assert "app score" in final_findings["summary_text_easy_english"]

    legacy_summary = json.loads((run_dir / "experimental" / "summary.json").read_text(encoding="utf-8"))
    assert legacy_summary == summary

    neutral_labels = json.loads(
        (run_dir / "classifier" / "neutral_target_labels.json").read_text(encoding="utf-8")
    )
    assert neutral_labels["classifier_stage"] == "core"
    assert neutral_labels["classifier_quality"] == "input_contract_validated"
    assert len(neutral_labels["object_labels"]) == 2
    assert neutral_labels["cluster_labels"][0]["dominant_class_id"].startswith("Class_")


def test_classifier_stage_blocks_shape_mismatch(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "gee_screening.db")
    _write_classifier_inputs(run_dir, 64)
    Image.fromarray(np.zeros((32, 32), dtype=np.float32)).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")

    with pytest.raises(StageError, match="shape mismatch"):
        asyncio.run(ClassifierStage().run(StageContext(run_id="run-1", settings=settings, run_dir=run_dir)))


def test_classifier_stage_blocks_out_of_bounds_object(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "gee_screening.db")
    _write_classifier_inputs(run_dir, 64)
    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max"],
        [{"object_id": 1, "cluster_id": 0, "row_min": 60, "row_max": 65, "col_min": 40, "col_max": 43}],
    )

    with pytest.raises(StageError, match="bounds exceed raster shape"):
        asyncio.run(ClassifierStage().run(StageContext(run_id="run-1", settings=settings, run_dir=run_dir)))


def test_classifier_stage_blocks_missing_required_object_column(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "gee_screening.db")
    _write_classifier_inputs(run_dir, 64)
    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min"],
        [{"object_id": 1, "cluster_id": 0, "row_min": 32, "row_max": 35, "col_min": 40}],
    )

    with pytest.raises(StageError, match="missing required columns"):
        asyncio.run(ClassifierStage().run(StageContext(run_id="run-1", settings=settings, run_dir=run_dir)))


def test_classifier_stage_blocks_invalid_integer_object_value(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "gee_screening.db")
    _write_classifier_inputs(run_dir, 64)
    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max"],
        [{"object_id": 1, "cluster_id": 0, "row_min": "bad", "row_max": 35, "col_min": 40, "col_max": 43}],
    )

    with pytest.raises(StageError, match="invalid integer value"):
        asyncio.run(ClassifierStage().run(StageContext(run_id="run-1", settings=settings, run_dir=run_dir)))


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


def test_classify_area_finding_uses_score_and_shape() -> None:
    elongated = classify_area_finding(
        score=0.82,
        row_min=1,
        row_max=1,
        col_min=1,
        col_max=6,
    )
    compact = classify_area_finding(
        score=0.82,
        row_min=1,
        row_max=2,
        col_min=1,
        col_max=2,
    )
    area_like = classify_area_finding(
        score=0.82,
        row_min=1,
        row_max=5,
        col_min=1,
        col_max=5,
    )

    assert elongated["finding_label"] == "ENTRANCE_SHAFT_TRACE"
    assert compact["finding_label"] == "COMPACT_CHAMBER_POINT"
    assert area_like["finding_label"] == "CHAMBER_VOID_AREA"


def test_final_area_findings_summary_uses_app_score_not_probability() -> None:
    summary = build_final_area_findings_summary(
        [
            {
                "finding_label": "CHAMBER_VOID_AREA",
                "finding_score": 0.82,
            },
            {
                "finding_label": "POSSIBLE_ENTRANCE_SHAFT",
                "finding_score": 0.66,
            },
            {
                "finding_label": "CHAMBER_VOID_AREA",
                "finding_score": 0.74,
            },
        ],
        run_id="run-test",
        data_quality_status="input_contract_validated",
    )

    assert summary["result_status"] == "result_available"
    assert summary["best_finding"] == "CHAMBER_VOID_AREA"
    assert summary["best_finding_score"] == 0.82
    assert summary["score_type"] == "app_score"
    assert summary["ranked_findings"][0]["supporting_candidate_count"] == 2
    assert "82%" in summary["summary_text_easy_english"]
    assert "probability" not in summary["summary_text_easy_english"].casefold()


def test_final_area_findings_summary_reports_no_strong_result() -> None:
    summary = build_final_area_findings_summary(
        [
            {
                "finding_label": "BACKGROUND_AREA",
                "finding_score": 0.31,
            }
        ],
        run_id="run-test",
        data_quality_status="input_contract_validated",
    )

    assert summary["result_status"] == "no_strong_result"
    assert summary["best_finding"] is None
    assert summary["best_finding_score"] is None
    assert summary["depth_status"] == "not_available"
