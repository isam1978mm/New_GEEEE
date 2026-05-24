from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.services.storage import read_manifest


def test_focus_mask_stage_writes_filesystem_only_local_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))

        result = asyncio.run(FocusMaskStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "focus_zone_17m_tif",
            "focus_zone_17m_npy",
            "focus_zone_ai_ready_window",
            "focus_zone_summary",
            "focus_band_summary",
        ]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        mask = np.load(run_dir / "full_job" / "focus" / "focus_zone_17m.npy")
        assert mask.shape == (grid_spec.size, grid_spec.size)
        assert int(mask.sum()) == 9
        mask_sidecar = read_manifest(raster_sidecar_path(run_dir / "full_job" / "focus" / "focus_zone_17m.tif"))
        assert mask_sidecar["transform"] == grid_spec.manifest.crs_transform
        assert mask_sidecar["dtype"] == "uint8"
        assert mask_sidecar["nodata"] == 0.0

        focus_window = np.load(run_dir / "full_job" / "focus" / "focus_zone_ai_ready_window.npy")
        assert focus_window.ndim == 3
        assert focus_window.shape[:2] == (3, 3)
        assert focus_window.shape[-1] > 1

        summary = json.loads((run_dir / "full_job" / "focus" / "focus_zone_summary.json").read_text(encoding="utf-8"))
        assert summary["focus_size_m"] == 17.0
        assert summary["mask_pixel_count"] == int(mask.sum())
        assert "coordinates" not in json.dumps(summary).casefold()
        assert "geometry" not in json.dumps(summary).casefold()

        with (run_dir / "full_job" / "focus" / "focus_zone_band_summary.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert rows[0]["band_name"] == "VV_dB"


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
