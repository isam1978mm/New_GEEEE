from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.errors import GridDriftError
from app.pipeline._base import ParityCategory, StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import read_manifest


def test_zero_shift_stage_accepts_grid_locked_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        result = asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))

        assert ZeroShiftStage(grid_spec=grid_spec).parity_category == ParityCategory.PARITY_REPRODUCES
        assert result.metadata["validated_tifs"] == 1
        assert result.metadata["validated_arrays"] == 1
        assert result.metadata["status"] == "grid_locked"


def test_zero_shift_stage_raises_grid_drift_error_for_half_pixel_shift() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        sidecar_path = raster_sidecar_path(run_dir / "dem.tif")
        metadata = read_manifest(sidecar_path)
        metadata["transform"][2] = metadata["transform"][2] + 5.0
        sidecar_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

        with pytest.raises(GridDriftError):
            asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
