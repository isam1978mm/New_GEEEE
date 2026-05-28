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
from app.pipeline.stages.secret_layers import (
    SECRET_LAYER_SPECS,
    SecretLayersStage,
    compute_secret_chemical_protector,
    compute_secret_gold_halo,
    compute_secret_hidden_doors,
    compute_secret_silver_oxide,
    compute_secret_thermal_inertia,
    compute_secret_tunnel_ceiling,
)
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_secret_layers_stage_emits_all_six_implemented() -> None:
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
        result = asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))

        artifact_names = {a.name for a in result.artifacts}
        assert "AI_READY_640_Secret_Gold_Halo" in artifact_names
        assert "AI_READY_640_Secret_Silver_Oxide" in artifact_names
        assert "AI_READY_640_Secret_Tunnel_Ceiling" in artifact_names
        assert "AI_READY_640_Secret_Thermal_Inertia" in artifact_names
        assert "AI_READY_640_Secret_Chemical_Protector" in artifact_names
        assert "AI_READY_640_Secret_Hidden_Doors" in artifact_names
        assert "secret_layers_manifest" in artifact_names

        metadata = result.metadata
        assert set(metadata["implemented_layers"]) == {
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        }
        assert metadata["not_implemented_layers"] == []

        for layer_name in metadata["implemented_layers"]:
            detail = metadata["layer_details"][layer_name]
            assert detail["status"] == "implemented"
            assert "formula" in detail


def test_secret_layers_manifest_documents_all_six_implemented() -> None:
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

        manifest_path = run_dir / "QA" / "stacks" / "secret_layers_manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "secret_layers_manifest_v1"
        assert manifest["stage"] == "secret_layers"
        assert manifest["layer_count"] == 6
        assert manifest["implemented_count"] == 6
        assert manifest["not_implemented_count"] == 0

        implemented_names = {item["name"] for item in manifest["implemented"]}
        assert implemented_names == {
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        }
        for item in manifest["implemented"]:
            assert item["status"] == "implemented"
            assert "formula" in item
            assert "source_type" in item
            assert "inputs" in item
            assert "output_path" in item
            assert item["output_path"].startswith("AI_READY_640/")

        assert manifest["not_implemented"] == []


def test_implemented_secret_layer_rasters_match_grid_contract() -> None:
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

        for layer_name in (
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        ):
            tif_path = run_dir / "AI_READY_640" / f"{layer_name}.tif"
            assert tif_path.is_file(), f"Missing {tif_path}"
            with rasterio.open(tif_path) as dataset:
                assert dataset.width == grid_spec.size
                assert dataset.height == grid_spec.size
                assert str(dataset.crs) == grid_spec.crs
                assert dataset.count == 1
                assert dataset.dtypes == ("float32",)
                assert float(dataset.nodata) == float(grid_spec.nodata)

            # Verify no absolute paths in tags
            tags_text = json.dumps(dataset.tags())
            assert str(run_dir) not in tags_text
            assert "C:\\" not in tags_text


def test_all_secret_layer_rasters_exist_after_stage() -> None:
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

        for layer_name in (
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        ):
            tif_path = run_dir / "AI_READY_640" / f"{layer_name}.tif"
            assert tif_path.is_file(), f"Missing secret layer raster: {tif_path}"


def test_gold_halo_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b8 = np.ones((size, size), dtype=np.float32) * 0.25
    cube = np.stack([np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)), b8, np.zeros((size, size)), b12], axis=-1)
    result = compute_secret_gold_halo(cube, nodata=-9999.0)
    expected = np.float32(0.5 / (0.25 + 1e-10))
    assert np.allclose(result, expected)


def test_tunnel_ceiling_formula_matches_notebook() -> None:
    size = 64
    b8 = np.ones((size, size), dtype=np.float32) * 0.8
    b4 = np.ones((size, size), dtype=np.float32) * 0.3
    cube = np.stack([np.zeros((size, size)), np.zeros((size, size)), b4, b8, np.zeros((size, size)), np.zeros((size, size))], axis=-1)
    result = compute_secret_tunnel_ceiling(cube, nodata=-9999.0)
    expected = np.float32(0.8 - 0.3)
    assert np.allclose(result, expected)


def test_thermal_inertia_formula_matches_notebook() -> None:
    size = 64
    lst = np.ones((size, size), dtype=np.float32) * 300.0
    result = compute_secret_thermal_inertia(lst, nodata=-9999.0, scale_m=10.0)
    # With uniform input, focal mean equals the input, so ratio is 1.0
    assert np.allclose(result, 1.0)


def test_silver_oxide_formula_matches_notebook() -> None:
    size = 64
    b2 = np.ones((size, size), dtype=np.float32) * 0.4
    b1 = np.ones((size, size), dtype=np.float32) * 0.2
    cube = np.stack([
        b2, np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)), b1
    ], axis=-1)
    result = compute_secret_silver_oxide(cube, nodata=-9999.0)
    expected = np.float32(0.4 / (0.2 + 1e-10))
    assert np.allclose(result, expected)


def test_chemical_protector_formula_matches_notebook() -> None:
    size = 64
    b1 = np.ones((size, size), dtype=np.float32) * 0.2
    b11 = np.ones((size, size), dtype=np.float32) * 0.4
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), b11, np.zeros((size, size)), b1
    ], axis=-1)
    result = compute_secret_chemical_protector(cube, nodata=-9999.0)
    expected = np.float32(0.2 / (0.4 + 1e-10))
    assert np.allclose(result, expected)


def test_hidden_doors_produces_finite_output() -> None:
    size = 64
    dem = np.linspace(0, 100, size * size, dtype=np.float32).reshape((size, size))
    result = compute_secret_hidden_doors(dem, nodata=-9999.0, scale_m=10.0)
    assert result.shape == (size, size)
    assert np.isfinite(result).all()
    assert (result != -9999.0).all()


def test_secret_layer_specs_cover_all_six_layers() -> None:
    names = {spec["name"] for spec in SECRET_LAYER_SPECS}
    assert names == {
        "AI_READY_640_Secret_Gold_Halo",
        "AI_READY_640_Secret_Silver_Oxide",
        "AI_READY_640_Secret_Tunnel_Ceiling",
        "AI_READY_640_Secret_Thermal_Inertia",
        "AI_READY_640_Secret_Chemical_Protector",
        "AI_READY_640_Secret_Hidden_Doors",
    }


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
