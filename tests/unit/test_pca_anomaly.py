from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
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

        assert [artifact.name for artifact in result.artifacts] == ["pca_anomaly_tif", "pca_eigenvalues", "parity_qa_summary"]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "pca_anomaly_tif": ArtifactClass.LOCAL_SENSITIVE,
            "pca_eigenvalues": ArtifactClass.LOCAL_SENSITIVE,
            "parity_qa_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        sidecar = read_manifest(raster_sidecar_path(run_dir / "pca_anomaly.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform
        report = read_manifest(run_dir / "pca_eigenvalues.json")
        assert report["seed"] == 0
        assert "eigenvalues" in report or "explained_variance" in report
        qa_summary = json.loads((run_dir / "QA" / "parity" / "parity_qa_summary.json").read_text(encoding="utf-8"))
        assert qa_summary["seed"] == 0
        assert qa_summary["components_count"] == 3


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
