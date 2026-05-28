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
from app.pipeline.stages.report_640 import (
    Report640Stage,
    compute_report_mass_report,
    compute_report_pottery_report,
    compute_report_zero_point_targets,
)
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_report_640_stage_emits_three_implemented_reports() -> None:
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
        result = asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        artifact_names = {a.name for a in result.artifacts}
        assert "REPORT_640_Pottery_Report" in artifact_names
        assert "REPORT_640_Mass_Report" in artifact_names
        assert "REPORT_640_FINAL_Zero_Point_Targets" in artifact_names
        assert "REPORT_640_manifest" in artifact_names

        metadata = result.metadata
        assert set(metadata["implemented_reports"]) == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }
        assert metadata["not_implemented_reports"] == []

        mass_detail = metadata["report_details"]["REPORT_640_Mass_Report"]
        assert mass_detail["status"] == "implemented"
        assert mass_detail["formula"] == "B12 * ST_B10 / 1000"


def test_report_640_manifest_documents_three_implemented_reports() -> None:
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
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        manifest_path = run_dir / "QA" / "REPORT_640_manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "notebook_report_640_manifest_v1"
        assert manifest["stage"] == "report_640"
        assert set(manifest["reports"]) == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }

        assert manifest["reports"]["REPORT_640_Pottery_Report.tif"]["status"] == "implemented"
        assert manifest["reports"]["REPORT_640_FINAL_Zero_Point_Targets.tif"]["status"] == "implemented"
        mass_report = manifest["reports"]["REPORT_640_Mass_Report.tif"]
        assert mass_report["status"] == "implemented"
        assert mass_report["formula"] == "B12 * ST_B10 / 1000"
        assert "s2_raw_cube.npy" in mass_report["source_equivalent"]
        assert "st_b10_raw.npy" in mass_report["source_equivalent"]


def test_implemented_report_rasters_match_grid_contract() -> None:
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
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        for report_name in (
            "REPORT_640_Pottery_Report",
            "REPORT_640_Mass_Report",
            "REPORT_640_FINAL_Zero_Point_Targets",
        ):
            tif_path = run_dir / f"{report_name}.tif"
            assert tif_path.is_file(), f"Missing {tif_path}"
            with rasterio.open(tif_path) as dataset:
                assert dataset.width == grid_spec.size
                assert dataset.height == grid_spec.size
                assert str(dataset.crs) == grid_spec.crs
                assert dataset.count == 1
                assert dataset.dtypes == ("float32",)
                assert float(dataset.nodata) == float(grid_spec.nodata)

            tags_text = json.dumps(dataset.tags())
            assert str(run_dir) not in tags_text
            assert "C:\\" not in tags_text


def test_mass_report_raster_is_emitted_with_grid_contract() -> None:
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
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        tif_path = run_dir / "REPORT_640_Mass_Report.tif"
        assert tif_path.is_file()
        with rasterio.open(tif_path) as dataset:
            assert dataset.width == grid_spec.size
            assert dataset.height == grid_spec.size
            assert str(dataset.crs) == grid_spec.crs
            assert dataset.count == 1
            assert dataset.dtypes == ("float32",)
            assert float(dataset.nodata) == float(grid_spec.nodata)


def test_mass_report_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    st_b10 = np.ones((size, size), dtype=np.float32) * 200.0
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), np.zeros((size, size)), b12, np.zeros((size, size))
    ], axis=-1)
    result = compute_report_mass_report(cube, st_b10, nodata=-9999.0)
    expected = np.float32((0.5 * 200.0) / 1000.0)
    assert np.allclose(result, expected)


def test_pottery_report_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b11 = np.ones((size, size), dtype=np.float32) * 0.25
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), b11, b12, np.zeros((size, size))
    ], axis=-1)
    result = compute_report_pottery_report(cube, nodata=-9999.0)
    expected = np.float32(0.5 / 0.25)
    assert np.allclose(result, expected)


def test_zero_point_targets_all_conditions_met() -> None:
    size = 64
    # Set up bands so all three conditions are met
    b12 = np.ones((size, size), dtype=np.float32) * 0.5   # B12/B11 = 0.5/0.3 = 1.67 > 1.45
    b11 = np.ones((size, size), dtype=np.float32) * 0.3
    b4 = np.ones((size, size), dtype=np.float32) * 0.4    # B4/B3 = 0.4/0.2 = 2.0 > 1.25
    b3 = np.ones((size, size), dtype=np.float32) * 0.2
    b8 = np.ones((size, size), dtype=np.float32) * 0.8    # NDVI = (0.8-0.4)/(0.8+0.4) = 0.33
    # S2_SOURCE_BANDS = (B2, B3, B4, B8, B11, B12, B1)
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=-9999.0)
    # NDVI = 0.33 which is NOT > 0.35, so all conditions are NOT met
    assert (result == 0.0).all() or (result == -9999.0).all()

    # Now make NDVI > 0.35
    b8 = np.ones((size, size), dtype=np.float32) * 0.9    # NDVI = (0.9-0.4)/(0.9+0.4) = 0.38 > 0.35
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=-9999.0)
    assert (result == 1.0).all()


def test_zero_point_targets_respects_nodata() -> None:
    size = 64
    nodata = -9999.0
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b11 = np.ones((size, size), dtype=np.float32) * 0.3
    b4 = np.ones((size, size), dtype=np.float32) * 0.4
    b3 = np.ones((size, size), dtype=np.float32) * 0.2
    b8 = np.ones((size, size), dtype=np.float32) * 0.9
    b3[0, 0] = nodata
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=nodata)
    assert result[0, 0] == nodata
    assert (result[1:, 1:] == 1.0).all()


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
