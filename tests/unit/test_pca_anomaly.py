from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage, compute_pca_anomaly
from app.services.storage import read_manifest


def test_compute_pca_anomaly_is_seeded_and_normalized() -> None:
    cube = np.zeros((4, 4, 3), dtype=np.float32)
    cube[:, :, 0] = np.arange(16, dtype=np.float32).reshape(4, 4)
    cube[:, :, 1] = cube[:, :, 0] * 2.0
    cube[:, :, 2] = cube[:, :, 0] * 0.5

    anomaly_a, report_a = compute_pca_anomaly(cube, nodata=-9999.0, seed=0)
    anomaly_b, report_b = compute_pca_anomaly(cube, nodata=-9999.0, seed=0)

    assert np.allclose(anomaly_a, anomaly_b)
    assert report_a["seed"] == 0
    assert report_a["explained_variance_ratio"] == report_b["explained_variance_ratio"]
    assert "eigenvalues" in report_a
    assert "explained_variance" in report_a
    assert float(np.min(anomaly_a)) >= 0.0
    assert float(np.max(anomaly_a)) <= 1.0


def test_compute_pca_anomaly_can_return_raw_score_separate_from_display_stretch() -> None:
    nodata = -9999.0
    base = np.arange(36, dtype=np.float32).reshape(6, 6)
    cube = np.zeros((6, 6, 3), dtype=np.float32)
    cube[:, :, 0] = base
    cube[:, :, 1] = base**2
    cube[:, :, 2] = np.flipud(base)

    anomaly, raw_score, report = compute_pca_anomaly(cube, nodata=nodata, seed=0, return_raw_score=True)

    valid = raw_score != nodata
    assert raw_score.shape == anomaly.shape
    assert np.all(np.isfinite(raw_score[valid]))
    assert np.all(raw_score[valid] >= 0.0)
    assert float(np.min(anomaly[valid])) >= 0.0
    assert float(np.max(anomaly[valid])) <= 1.0
    assert not np.allclose(raw_score[valid], anomaly[valid])
    assert report["raw_score_method"] == "pca_projected_component_magnitude"
    assert report["display_stretch_method"] == "percentile_1_99_on_valid_raw_score"
    assert report["raw_score_range"]["max"] is not None


def test_compute_pca_anomaly_excludes_degenerate_feature_channels() -> None:
    nodata = -9999.0
    cube = np.zeros((5, 5, 4), dtype=np.float32)
    cube[:, :, 0] = np.arange(25, dtype=np.float32).reshape(5, 5)
    cube[:, :, 1] = 7.0
    cube[:, :, 2] = nodata
    cube[:, :, 3] = 1.0

    anomaly, report = compute_pca_anomaly(cube, nodata=nodata, seed=0, valid_mask_channel=True)

    assert np.all(anomaly != nodata)
    assert report["input_feature_channel_count"] == 3
    assert report["feature_channel_count"] == 1
    assert report["included_feature_channels"] == [0]
    excluded = {item["channel_index"]: item["reason"] for item in report["excluded_feature_channels"]}
    assert excluded == {1: "near_constant", 2: "no_finite_values"}
    assert report["pca_feature_policy"] == "exclude_valid_mask_all_nodata_and_near_constant_channels"


def test_compute_pca_anomaly_blocks_low_valid_fraction() -> None:
    nodata = -9999.0
    cube = np.zeros((10, 10, 3), dtype=np.float32)
    base = np.arange(100, dtype=np.float32).reshape(10, 10)
    cube[:, :, 0] = base
    cube[:, :, 1] = base * 2.0
    cube[:, :, 2] = 0.0
    cube[0:3, 0:3, 2] = 1.0

    with pytest.raises(StageError, match="valid pixel fraction"):
        compute_pca_anomaly(cube, nodata=nodata, seed=0, min_valid_pixel_fraction=0.10)


def test_pca_anomaly_stage_writes_classified_outputs_and_report() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        cube = np.zeros((grid_spec.size, grid_spec.size, 3), dtype=np.float32)
        cube[:, :, 0] = 1.0
        cube[:, :, 1] = 2.0
        cube[:, :, 2] = np.linspace(0.0, 1.0, grid_spec.size * grid_spec.size, dtype=np.float32).reshape(grid_spec.size, grid_spec.size)
        np.save(run_dir / "hypercube.npy", cube)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(PcaAnomalyStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "pca_anomaly_tif",
            "pca_anomaly_raw_npy",
            "pca_eigenvalues",
            "parity_qa_summary",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "pca_anomaly_tif": ArtifactClass.LOCAL_SENSITIVE,
            "pca_anomaly_raw_npy": ArtifactClass.LOCAL_SENSITIVE,
            "pca_eigenvalues": ArtifactClass.LOCAL_SENSITIVE,
            "parity_qa_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        sidecar = read_manifest(raster_sidecar_path(run_dir / "pca_anomaly.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform
        raw_score = np.load(run_dir / "pca_anomaly_raw.npy")
        assert raw_score.shape == (grid_spec.size, grid_spec.size)
        report = read_manifest(run_dir / "pca_eigenvalues.json")
        assert report["seed"] == 0
        assert report["raw_score_method"] == "pca_projected_component_magnitude"
        assert report["display_stretch_method"] == "percentile_1_99_on_valid_raw_score"
        assert "eigenvalues" in report or "explained_variance" in report
        qa_summary = json.loads((run_dir / "QA" / "parity" / "parity_qa_summary.json").read_text(encoding="utf-8"))
        assert qa_summary["seed"] == 0
        assert qa_summary["components_count"] == 1
        assert qa_summary["input_feature_channel_count"] == 3
        assert qa_summary["feature_channel_count"] == 1
        assert qa_summary["excluded_feature_channel_count"] == 2
        assert qa_summary["pca_feature_policy"] == "exclude_valid_mask_all_nodata_and_near_constant_channels"
        assert qa_summary["valid_pixel_fraction"] == 1.0
        assert qa_summary["min_valid_pixel_fraction"] == 0.05
        assert qa_summary["raw_score_method"] == "pca_projected_component_magnitude"
        assert qa_summary["display_stretch_method"] == "percentile_1_99_on_valid_raw_score"
        assert qa_summary["raw_score_range"]["max"] is not None


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
