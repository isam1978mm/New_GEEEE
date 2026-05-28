from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_notebook_stack_npy_aliases_match_local_sources_numerically() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_stack_run(run_dir)

        npy_alias_pairs = [("NPY_STACKS/RADAR_STACK_HWC_640_app.npy", "stacks/tensor_support/radar_db_support_stack.npy")]

        for alias_relative_path, source_relative_path in npy_alias_pairs:
            alias_path = run_dir / alias_relative_path
            source_path = run_dir / source_relative_path

            assert alias_path.is_file(), f"missing stack alias: {alias_relative_path}"
            assert source_path.is_file(), f"missing stack source: {source_relative_path}"

            alias_array = np.load(alias_path)
            source_array = np.load(source_path)

            assert alias_array.shape == source_array.shape, alias_relative_path
            assert alias_array.dtype == source_array.dtype, alias_relative_path
            np.testing.assert_array_equal(np.isnan(alias_array), np.isnan(source_array), err_msg=alias_relative_path)
            np.testing.assert_allclose(alias_array, source_array, rtol=0.0, atol=0.0, err_msg=alias_relative_path)


def _build_stack_run(run_dir: Path) -> None:
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
    asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
    asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
    asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
    asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))
    asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
