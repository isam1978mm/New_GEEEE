from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import json
import numpy as np

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher


def test_notebook_sar_npy_aliases_match_local_sources_numerically() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_sar_run(run_dir)

        alias_pairs = [
            ("NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy", "npy_radar_bands/VV_dB.npy"),
            ("NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy", "npy_radar_bands/VH_dB.npy"),
            ("NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy", "npy_radar_bands/logRatio_dB.npy"),
            ("NPY_RADAR_BANDS/RADAR_angle_640_app.npy", "npy_radar_bands/incidence.npy"),
        ]

        for alias_relative_path, source_relative_path in alias_pairs:
            _assert_npy_alias_exact(run_dir, alias_relative_path, source_relative_path)


def test_notebook_sar_post_rtc_intermediates_match_local_sources_numerically() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_sar_run(run_dir)

        manifest_path = run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        post_rtc = manifest["stages"]["post_rtc"]
        assert post_rtc["status"] == "implemented"
        assert isinstance(post_rtc["source_description"], str) and post_rtc["source_description"]
        assert post_rtc["bands"] == {
            "VV_dB": "post_rtc/final_VV_dB.npy",
            "VH_dB": "post_rtc/final_VH_dB.npy",
            "logRatio_dB": "post_rtc/final_logRatio_dB.npy",
            "angle": "post_rtc/final_angle.npy",
        }
        assert post_rtc["source_mapping"] == {
            "post_rtc/final_VV_dB.npy": "npy_radar_bands/VV_dB.npy",
            "post_rtc/final_VH_dB.npy": "npy_radar_bands/VH_dB.npy",
            "post_rtc/final_logRatio_dB.npy": "npy_radar_bands/logRatio_dB.npy",
            "post_rtc/final_angle.npy": "npy_radar_bands/incidence.npy",
        }

        alias_pairs = [
            ("QA/sar/intermediates/post_rtc/final_VV_dB.npy", "npy_radar_bands/VV_dB.npy"),
            ("QA/sar/intermediates/post_rtc/final_VH_dB.npy", "npy_radar_bands/VH_dB.npy"),
            ("QA/sar/intermediates/post_rtc/final_logRatio_dB.npy", "npy_radar_bands/logRatio_dB.npy"),
            ("QA/sar/intermediates/post_rtc/final_angle.npy", "npy_radar_bands/incidence.npy"),
        ]
        for alias_relative_path, source_relative_path in alias_pairs:
            _assert_npy_alias_exact(run_dir, alias_relative_path, source_relative_path)


def _assert_npy_alias_exact(run_dir: Path, alias_relative_path: str, source_relative_path: str) -> None:
    alias_path = run_dir / alias_relative_path
    source_path = run_dir / source_relative_path

    assert alias_path.is_file(), f"missing SAR NPY alias: {alias_relative_path}"
    assert source_path.is_file(), f"missing SAR NPY source: {source_relative_path}"

    alias_array = np.load(alias_path)
    source_array = np.load(source_path)

    assert alias_array.shape == source_array.shape, alias_relative_path
    assert alias_array.dtype == source_array.dtype, alias_relative_path
    np.testing.assert_array_equal(np.isnan(alias_array), np.isnan(source_array), err_msg=alias_relative_path)
    np.testing.assert_allclose(alias_array, source_array, rtol=0.0, atol=0.0, err_msg=alias_relative_path)


def _build_sar_run(run_dir: Path) -> None:
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
