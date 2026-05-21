from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage, build_hypercube_products
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
        with (run_dir / "qa" / "parity" / "hypercube_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            audit_rows = list(csv.DictReader(handle))
        assert len(audit_rows) == 3
        assert audit_rows[-1]["band_name"] == "valid_mask"
        sidecar = read_manifest(raster_sidecar_path(run_dir / "hypercube.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform


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
