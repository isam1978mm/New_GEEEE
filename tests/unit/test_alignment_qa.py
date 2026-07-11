from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
import rasterio
from affine import Affine
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import GridDriftError
from app.pipeline._base import StageContext
from app.pipeline.stages.alignment_qa import AlignmentQaStage, build_alignment_reports, collect_raster_sidecars
from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid


def test_build_alignment_reports_summarizes_grid_aligned_rasters() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_raster(run_dir / "dem.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "pca_anomaly.tif", np.full((grid_spec.size, grid_spec.size), 0.8, dtype=np.float32), grid_spec)

        audit_rows, summary, mask_selection = build_alignment_reports(run_dir, grid_spec)

        assert len(audit_rows) == 2
        assert summary["pass"] is True
        assert summary["checked_raster_count"] == 2
        assert summary["max_center_offset_px"] == 0.0
        assert mask_selection["anchor_artifact"] in {"dem.tif", "pca_anomaly.tif"}


def test_alignment_qa_recursively_collects_official_nested_rasters() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_raster(run_dir / "dem.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "DEM_GEO8_TIFS" / "DEM_640.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "QA" / "QA_GRID_validmask_640.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "PRIVATE" / "secret.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "experimental" / "debug.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)

        collected = {path.relative_to(run_dir).as_posix() for path, _sidecar in collect_raster_sidecars(run_dir)}
        audit_rows, summary, _mask_selection = build_alignment_reports(run_dir, grid_spec)
        audit_names = {str(row["artifact_name"]) for row in audit_rows}
        expected = {
            "DEM_GEO8_TIFS/DEM_640.tif",
            "QA/QA_GRID_validmask_640.tif",
            "dem.tif",
        }

        assert collected == expected
        assert audit_names == expected
        assert summary["checked_raster_count"] == 3
        assert summary["pass"] is True


def test_alignment_qa_stage_writes_reports_as_redacted_public() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_raster(run_dir / "dem.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "pca_anomaly.tif", np.full((grid_spec.size, grid_spec.size), 0.8, dtype=np.float32), grid_spec)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "alignment_qa",
            "alignment_audit",
            "alignment_mask_selection",
            "alignment_summary_redacted",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "alignment_qa": ArtifactClass.REDACTED_PUBLIC,
            "alignment_audit": ArtifactClass.REDACTED_PUBLIC,
            "alignment_mask_selection": ArtifactClass.REDACTED_PUBLIC,
            "alignment_summary_redacted": ArtifactClass.LOCAL_SENSITIVE,
        }
        with (run_dir / "alignment_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        summary = json.loads((run_dir / "alignment_qa.json").read_text(encoding="utf-8"))
        assert summary["pass"] is True
        redacted_summary = json.loads((run_dir / "QA" / "alignment" / "alignment_summary_redacted.json").read_text(encoding="utf-8"))
        assert redacted_summary["pass"] is True
        assert "transform" not in redacted_summary
        assert "bounds" not in redacted_summary


def test_alignment_qa_stage_raises_on_transform_drift() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_raster(run_dir / "dem.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        _write_raster(run_dir / "pca_anomaly.tif", np.full((grid_spec.size, grid_spec.size), 0.8, dtype=np.float32), grid_spec)
        pca_path = run_dir / "pca_anomaly.tif"
        with rasterio.open(pca_path) as dataset:
            data = dataset.read(1)
            profile = dataset.profile
        profile["transform"] = profile["transform"] * Affine.translation(1, 0)
        with rasterio.open(pca_path, "w", **profile) as dataset:
            dataset.write(data, 1)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        with pytest.raises(GridDriftError):
            asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))

        summary_path = run_dir / "alignment_qa.json"
        assert summary_path.is_file()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["pass"] is False
        assert "pca_anomaly.tif" in summary["failing_artifacts"]

        summary_text = summary_path.read_text(encoding="utf-8")
        for forbidden in (
            "transform",
            "bounds",
            "bbox",
            "crs_transform",
            "hash",
            "checksum",
            "fingerprint",
            str(run_dir),
        ):
            assert forbidden not in summary_text
        bounds = grid_spec.manifest.bounds_m
        for numeric_fragment in (
            str(bounds["xmin"]),
            str(bounds["xmax"]),
            str(bounds["ymin"]),
            str(bounds["ymax"]),
        ):
            assert numeric_fragment not in summary_text


def _write_raster(path: Path, array: np.ndarray, grid_spec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_georeferenced_raster(path, array.astype(np.float32, copy=False), grid_spec)
    write_raster_sidecar(
        path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape,
    )


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
