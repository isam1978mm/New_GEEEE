from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import (
    NOTEBOOK_HYPERCUBE_NPY_NAME,
    NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
    NOTEBOOK_HYPERCUBE_TIF_NAME,
    NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY,
    NOTEBOOK_FINAL_TESLA_LAYER_ORDER,
    NOTEBOOK_PATCHED_14B_REASON,
    NOTEBOOK_STACK_OUTPUT_DIR,
    HypercubeStage,
    build_hypercube_products,
    write_notebook_final_tesla_outputs,
)
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.report_640 import Report640Stage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.services.storage import read_manifest


def test_build_hypercube_products_matches_notebook_masks_and_norm() -> None:
    layer_a = np.array([[1.0, 2.0], [3.0, -9999.0]], dtype=np.float32)
    layer_b = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)

    products = build_hypercube_products([("a", layer_a), ("b", layer_b)], nodata=-9999.0)

    cube_raw = products["cube_raw"]
    cube_clean = products["cube_clean"]
    cube_norm_plus_mask = products["cube_norm_plus_mask"]
    band_names = products["band_names"]
    assert isinstance(cube_raw, np.ndarray)
    assert isinstance(cube_clean, np.ndarray)
    assert isinstance(cube_norm_plus_mask, np.ndarray)
    assert cube_raw.shape == (2, 2, 3)
    assert cube_clean[1, 1, 0] == 0.0
    assert products["mask_any"][1, 1] == 1
    assert products["mask_all"][1, 1] == 0
    assert cube_norm_plus_mask.shape == (2, 2, 3)
    assert cube_norm_plus_mask[0, 0, -1] == 1.0
    assert band_names == ["a", "b", "valid_mask"]
    assert np.allclose(cube_raw, cube_norm_plus_mask)


def test_hypercube_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_source_raster(run_dir / "VV_dB.tif", np.full((grid_spec.size, grid_spec.size), -12.0, dtype=np.float32), grid_spec)
        _write_source_raster(run_dir / "NDVI.tif", np.full((grid_spec.size, grid_spec.size), 0.4, dtype=np.float32), grid_spec)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "hypercube_tif",
            "hypercube_npy",
            "hypercube_band_order",
            "hypercube_band_stats",
            "hypercube_norm_params",
            "hypercube_audit",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "hypercube_tif": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_npy": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_order": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_stats": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_norm_params": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_audit": ArtifactClass.FILESYSTEM_ONLY,
        }
        cube = np.load(run_dir / "hypercube.npy")
        assert cube.shape == (grid_spec.size, grid_spec.size, 3)
        assert np.all(cube[:, :, -1] == 1.0)
        with (run_dir / "hypercube_band_order.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 3
        assert rows[-1]["band_name"] == "valid_mask"
        assert rows[-1]["source_file"] == "generated"
        with (run_dir / "QA" / "parity" / "hypercube_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            audit_rows = list(csv.DictReader(handle))
        assert len(audit_rows) == 3
        assert audit_rows[-1]["band_name"] == "valid_mask"
        sidecar = read_manifest(raster_sidecar_path(run_dir / "hypercube.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform

        notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
        assert not (notebook_stack_dir / NOTEBOOK_HYPERCUBE_TIF_NAME).exists()
        assert not (notebook_stack_dir / NOTEBOOK_HYPERCUBE_NPY_NAME).exists()
        assert not (notebook_stack_dir / NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME).exists()
        statuses = result.metadata["notebook_output_statuses"]
        assert statuses[0]["filename"] == NOTEBOOK_HYPERCUBE_TIF_NAME
        assert statuses[0]["status"] == "not_implemented_no_source_equivalent"
        assert "missing required source rasters" in statuses[0]["reason"]
        assert statuses[1]["filename"] == NOTEBOOK_HYPERCUBE_NPY_NAME
        assert statuses[1]["status"] == "not_implemented_no_source_equivalent"
        assert "missing required source rasters" in statuses[1]["reason"]
        assert statuses[2] == {
            "filename": NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
            "status": "not_implemented_no_source_equivalent",
            "reason": NOTEBOOK_PATCHED_14B_REASON,
        }


def test_hypercube_stage_writes_notebook_final_tesla_outputs_when_sources_exist() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))
        result = asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))

        notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
        tif_path = notebook_stack_dir / NOTEBOOK_HYPERCUBE_TIF_NAME
        npy_path = notebook_stack_dir / NOTEBOOK_HYPERCUBE_NPY_NAME
        assert tif_path.is_file()
        assert npy_path.is_file()
        assert not (notebook_stack_dir / NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME).exists()

        tensor = np.load(npy_path)
        assert tensor.shape == (9, grid_spec.size, grid_spec.size)
        assert tensor.dtype == np.float32

        with rasterio.open(tif_path) as dataset:
            assert dataset.count == 9
            assert dataset.dtypes == ("float32",) * 9
            assert float(dataset.nodata) == float(grid_spec.nodata)
            assert str(dataset.crs) == grid_spec.crs
            assert dataset.descriptions == tuple(name for name, _relative_path in NOTEBOOK_FINAL_TESLA_LAYER_ORDER)

        sidecar = read_manifest(raster_sidecar_path(tif_path))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform

        artifact_names = [artifact.name for artifact in result.artifacts]
        assert "notebook_FINAL_TESLA_V7_2_HYPERCUBE_tif" in artifact_names
        assert "notebook_FINAL_TESLA_V7_2_HYPERCUBE_npy" in artifact_names

        statuses = result.metadata["notebook_output_statuses"]
        assert statuses == [
            {
                "filename": NOTEBOOK_HYPERCUBE_TIF_NAME,
                "status": "implemented",
                "source_family": NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY,
                "source_layer_order": [name for name, _relative_path in NOTEBOOK_FINAL_TESLA_LAYER_ORDER],
            },
            {
                "filename": NOTEBOOK_HYPERCUBE_NPY_NAME,
                "status": "implemented",
                "source_family": NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY,
                "source_layer_order": [name for name, _relative_path in NOTEBOOK_FINAL_TESLA_LAYER_ORDER],
                "layout": "CHW",
            },
            {
                "filename": NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
                "status": "not_implemented_no_source_equivalent",
                "reason": NOTEBOOK_PATCHED_14B_REASON,
            },
        ]


def test_write_notebook_final_tesla_outputs_uses_tiff_nodata_but_preserves_npy_nan() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        layer_a = np.array([[np.nan, 2.0], [3.0, 4.0]], dtype=np.float32)
        layer_b = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)

        outputs = write_notebook_final_tesla_outputs(
            run_dir,
            grid_spec,
            [("band_a", layer_a), ("band_b", layer_b)],
        )

        with rasterio.open(outputs["final_tesla_tif"]) as dataset:
            band_1 = dataset.read(1, masked=False)
            mask_1 = dataset.read_masks(1) == 0
            assert float(dataset.nodata) == float(grid_spec.nodata)
            assert band_1[0, 0] == np.float32(grid_spec.nodata)
            assert bool(mask_1[0, 0]) is True
            assert int(np.isnan(band_1).sum()) == 0
            assert dataset.descriptions == ("band_a", "band_b")

        tensor = np.load(outputs["final_tesla_npy"])
        assert tensor.shape == (2, 2, 2)
        assert np.isnan(tensor[0, 0, 0])
        assert tensor[0, 0, 1] == np.float32(2.0)


def _write_source_raster(path: Path, array: np.ndarray, grid_spec) -> None:
    from PIL import Image

    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")
    write_raster_sidecar(
        path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape,
    )


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
