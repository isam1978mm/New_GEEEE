from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.secret_layers import compute_secret_thermal_inertia, SecretLayersStage
from app.pipeline.stages.thermal import (
    L9_RAW_ST_B10_NPY_NAME,
    NOTEBOOK_L9_ST_B10_COLLECTION,
    ThermalStage,
    deterministic_lst_fetcher,
)


def test_secret_thermal_inertia_uses_persisted_l9_raw_source() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))

        l9_raw = np.load(run_dir / L9_RAW_ST_B10_NPY_NAME)
        expected = compute_secret_thermal_inertia(
            l9_raw,
            nodata=grid_spec.nodata,
            scale_m=float(grid_spec.manifest.scale_m),
        )

        with rasterio.open(run_dir / "AI_READY_640" / "AI_READY_640_Secret_Thermal_Inertia.tif") as dataset:
            actual = dataset.read(1)

        assert np.allclose(actual, expected, rtol=1e-6, atol=1e-6)

        manifest = json.loads((run_dir / "QA" / "stacks" / "secret_layers_manifest.json").read_text(encoding="utf-8"))
        thermal_item = next(
            item for item in manifest["implemented"] if item["name"] == "AI_READY_640_Secret_Thermal_Inertia"
        )
        assert thermal_item["inputs"] == ["l9_st_b10_raw"]
        assert thermal_item["source_unit"] == "raw_dn"
        assert thermal_item["source_collection"] == NOTEBOOK_L9_ST_B10_COLLECTION


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
