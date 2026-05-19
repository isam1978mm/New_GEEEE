from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.dem_derivatives import OUTPUT_NAMES, DemDerivativesStage, compute_dem_derivatives
from app.pipeline.stages.grid import build_run_grid
from app.services.storage import read_manifest


def test_compute_dem_derivatives_matches_notebook_slope_and_aspect() -> None:
    dem = np.array(
        [
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float32,
    )

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    expected_slope = np.degrees(np.arctan(1.0))
    assert outputs["slope"][1, 1] == expected_slope
    assert outputs["aspect"][1, 1] == 270.0
    assert outputs["curvature"][1, 1] == 0.0


def test_compute_dem_derivatives_propagates_nodata() -> None:
    dem = np.full((5, 5), 100.0, dtype=np.float32)
    dem[2, 2] = -9999.0

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    for name in OUTPUT_NAMES:
        assert outputs[name][2, 2] == -9999.0


def test_dem_derivatives_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        dem = np.linspace(100.0, 200.0, grid_spec.size * grid_spec.size, dtype=np.float32).reshape(grid_spec.size, grid_spec.size)
        np.save(run_dir / "dem.npy", dem)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == list(OUTPUT_NAMES)
        assert all(artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE for artifact in result.artifacts)
        for name in OUTPUT_NAMES:
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
