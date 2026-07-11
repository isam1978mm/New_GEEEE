from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from app.errors import GridDriftError
from app.pipeline.stages.alignment_qa import build_alignment_reports
from app.pipeline.stages.dem import raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.services.storage import read_manifest


def test_alignment_qa_checks_tif_without_sidecar() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        raster_path = run_dir / "no_sidecar.tif"
        write_georeferenced_raster(raster_path, np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)

        audit_rows, summary, _ = build_alignment_reports(run_dir, grid_spec)

        assert summary["pass"] is True
        assert summary["checked_raster_count"] == 1
        assert summary["metadata_source"] == "real_geotiff"
        assert audit_rows[0]["artifact_name"] == "no_sidecar.tif"
        assert audit_rows[0]["metadata_source"] == "real_geotiff"
        assert audit_rows[0]["sidecar_present"] == "false"
        assert audit_rows[0]["passes_alignment"] == "true"


def test_alignment_qa_ignores_sidecar_transform_when_real_tif_is_grid_locked() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        raster_path = run_dir / "sidecar_lies.tif"
        array = np.ones((grid_spec.size, grid_spec.size), dtype=np.float32)
        write_georeferenced_raster(raster_path, array, grid_spec)
        sidecar_path = write_raster_sidecar(
            raster_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        metadata = read_manifest(sidecar_path)
        metadata["transform"][2] = metadata["transform"][2] + 5.0
        sidecar_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

        audit_rows, summary, _ = build_alignment_reports(run_dir, grid_spec)

        assert summary["pass"] is True
        assert summary["failing_artifacts"] == []
        assert audit_rows[0]["sidecar_present"] == "true"
        assert audit_rows[0]["metadata_source"] == "real_geotiff"
        assert audit_rows[0]["passes_alignment"] == "true"


def test_alignment_qa_fails_when_real_tif_is_shifted_even_if_sidecar_is_grid_locked() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        raster_path = run_dir / "real_tif_shifted.tif"
        array = np.ones((grid_spec.size, grid_spec.size), dtype=np.float32)
        write_georeferenced_raster(raster_path, array, grid_spec)
        write_raster_sidecar(
            raster_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        _shift_tif_transform(raster_path, dx=5.0, dy=0.0)

        audit_rows, summary, _ = build_alignment_reports(run_dir, grid_spec)

        assert summary["pass"] is False
        assert summary["failing_artifacts"] == ["real_tif_shifted.tif"]
        assert audit_rows[0]["metadata_source"] == "real_geotiff"
        assert audit_rows[0]["passes_alignment"] == "false"


def _shift_tif_transform(path: Path, *, dx: float, dy: float) -> None:
    with rasterio.open(path) as dataset:
        data = dataset.read()
        profile = dataset.profile.copy()
        transform = dataset.transform
    profile["transform"] = Affine(
        transform.a,
        transform.b,
        transform.c + dx,
        transform.d,
        transform.e,
        transform.f + dy,
    )
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(data)
