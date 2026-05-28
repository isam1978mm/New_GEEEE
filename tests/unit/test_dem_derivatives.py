from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.dem_derivatives import OUTPUT_NAMES, DemDerivativesStage, compute_dem_derivatives, compute_hillshade
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


def test_compute_hillshade_matches_notebook_azimuth_convention() -> None:
    dem = np.array(
        [
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float32,
    )

    hillshade = compute_hillshade(dem, nodata=-9999.0, scale_m=10.0)

    expected_center = (
        np.sin(np.deg2rad(45.0)) * np.cos(np.arctan(1.0))
        + np.cos(np.deg2rad(45.0)) * np.sin(np.arctan(1.0)) * np.cos(np.deg2rad(45.0) - np.deg2rad(270.0))
    )
    assert np.isclose(hillshade[1, 1], expected_center, atol=1e-6)


def test_dem_derivatives_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        dem = np.linspace(100.0, 200.0, grid_spec.size * grid_spec.size, dtype=np.float32).reshape(grid_spec.size, grid_spec.size)
        np.save(run_dir / "dem.npy", dem)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            *OUTPUT_NAMES,
            "notebook_DEM_640",
            "notebook_slope_deg_640",
            "notebook_aspect_deg_640",
            "notebook_roughness_100m_640",
            "notebook_tpi_100m_640",
            "notebook_hillshade_0to1_640",
            "dem_derivatives_summary",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        for name in OUTPUT_NAMES:
            assert artifact_classes[name] == ArtifactClass.LOCAL_SENSITIVE
        for name in (
            "notebook_DEM_640",
            "notebook_slope_deg_640",
            "notebook_aspect_deg_640",
            "notebook_roughness_100m_640",
            "notebook_tpi_100m_640",
            "notebook_hillshade_0to1_640",
        ):
            assert artifact_classes[name] == ArtifactClass.LOCAL_SENSITIVE
        assert artifact_classes["dem_derivatives_summary"] == ArtifactClass.FILESYSTEM_ONLY
        for name in OUTPUT_NAMES:
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform
        notebook_dem_dir = run_dir / "DEM_GEO8_TIFS"
        expected_notebook_outputs = {
            "slope_deg_640.tif",
            "aspect_deg_640.tif",
            "roughness_100m_640.tif",
            "tpi_100m_640.tif",
            "hillshade_0to1_640.tif",
        }
        assert notebook_dem_dir.is_dir()
        assert expected_notebook_outputs <= {path.name for path in notebook_dem_dir.iterdir() if path.is_file()}
        for name in expected_notebook_outputs:
            notebook_sidecar = read_manifest(raster_sidecar_path(notebook_dem_dir / name))
            assert notebook_sidecar["transform"] == grid_spec.manifest.crs_transform
        summary = json.loads((run_dir / "QA" / "stacks" / "dem_derivatives_summary.json").read_text(encoding="utf-8"))
        assert summary["stage"] == "dem_derivatives"
        assert summary["band_count"] == len(OUTPUT_NAMES)


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
