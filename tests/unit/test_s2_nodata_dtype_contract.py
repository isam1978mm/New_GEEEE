from __future__ import annotations

import json

import numpy as np
import rasterio

from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.s2_indices import write_mask_raster, write_s2_outputs
from app.services.grid import GridManifest


def _grid_spec() -> GridSpec:
    return GridSpec(
        manifest=GridManifest(
            epsg=32637,
            utm_zone=37,
            hemisphere="north",
            scale_m=10,
            size_px=2,
            crs_transform=[10.0, 0.0, 500000.0, 0.0, -10.0, 4000020.0],
            bounds_m={"xmin": 500000.0, "ymin": 4000000.0, "xmax": 500020.0, "ymax": 4000020.0},
        ),
        nodata=-9999.0,
    )


def test_s2_index_sidecars_use_grid_nodata_not_real_zero(tmp_path):
    grid_spec = _grid_spec()
    outputs = {
        "NDVI": np.array([[0.0, 0.25], [-0.5, grid_spec.nodata]], dtype=np.float32),
    }

    written = write_s2_outputs(tmp_path, grid_spec, outputs)

    assert len(written) == 1
    with rasterio.open(written[0]) as dataset:
        assert dataset.nodata == grid_spec.nodata
        assert float(dataset.read(1)[0, 0]) == 0.0

    sidecar = json.loads(raster_sidecar_path(written[0]).read_text(encoding="utf-8"))
    assert sidecar["nodata"] == grid_spec.nodata


def test_s2_mask_raster_actual_dtype_matches_uint8_sidecar_contract(tmp_path):
    grid_spec = _grid_spec()
    path = tmp_path / "mask.tif"

    write_mask_raster(path, np.array([[1, 0], [1, 1]], dtype=np.uint8), grid_spec)

    with rasterio.open(path) as dataset:
        assert dataset.dtypes == ("uint8",)
        assert dataset.nodata == 0
        assert dataset.read(1).dtype == np.uint8
