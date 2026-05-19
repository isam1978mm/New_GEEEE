from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, StageContext
from app.pipeline.stages.dem import (
    DEM_TILE_SIZE,
    DemStage,
    build_dem_array,
    build_dem_tile_requests,
    create_ee_dem_tile_fetcher,
    deterministic_dem_tile,
    raster_sidecar_path,
)
from app.pipeline.stages.grid import build_run_grid
from app.services.storage import read_manifest


def test_build_dem_tile_requests_follow_notebook_grid_tiling() -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    requests = build_dem_tile_requests(grid_spec)

    assert [(request.tile_row, request.tile_col) for request in requests] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert requests[0].xmin == -3200.0
    assert requests[0].ymin == 0.0
    assert requests[0].xmax == 0.0
    assert requests[0].ymax == 3200.0
    assert requests[-1].xmin == 0.0
    assert requests[-1].ymin == -3200.0
    assert requests[-1].xmax == 3200.0
    assert requests[-1].ymax == 0.0
    assert all(request.size == DEM_TILE_SIZE for request in requests)


def test_build_dem_array_is_deterministic_and_tile_assembled() -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    first = build_dem_array(grid_spec, tile_fetcher=deterministic_dem_tile)
    second = build_dem_array(grid_spec, tile_fetcher=deterministic_dem_tile)

    assert np.array_equal(first, second)
    assert first.shape == (640, 640)
    assert first.dtype == np.float32
    assert float(first[0, 0]) == 1136.0
    assert float(first[319, 319]) == 1375.25
    assert float(first[320, 320]) == 1376.0
    assert float(first[-1, -1]) == 1615.25


def test_create_ee_dem_tile_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-dem-test"))
    initialize_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {"DEM": [[1.0] * DEM_TILE_SIZE for _ in range(DEM_TILE_SIZE)]}}

    class FakeImage:
        def sampleRectangle(self, *, region, defaultValue):
            assert region == "tile-region"
            assert defaultValue == grid_spec.nodata
            return FakeSampleResult()

    def fake_initialize_ee_session(_settings) -> None:
        initialize_calls.append("init")

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            rectangle_calls.append((coords, crs, geodesic))
            return "tile-region"

    monkeypatch.setattr("app.pipeline.stages.dem.initialize_ee_session", fake_initialize_ee_session)
    monkeypatch.setattr("app.pipeline.stages.dem.build_ee_dem_image", lambda _grid_spec: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.dem.ee.Geometry", FakeGeometry)

    fetcher = create_ee_dem_tile_fetcher(settings, grid_spec)
    tile = fetcher(
        grid_spec=grid_spec,
        tile_row=0,
        tile_col=0,
        xmin=-3200.0,
        ymin=0.0,
        xmax=0.0,
        ymax=3200.0,
        size=DEM_TILE_SIZE,
    )

    assert initialize_calls == ["init"]
    assert rectangle_calls == [([-3200.0, 0.0, 0.0, 3200.0], "EPSG:32637", False)]
    assert tile.shape == (DEM_TILE_SIZE, DEM_TILE_SIZE)
    assert tile.dtype == np.float32


def test_dem_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)
        stage = DemStage(grid_spec=build_run_grid(35.59499, 36.12694), tile_fetcher=deterministic_dem_tile)

        result = asyncio.run(stage.run(context))

        assert stage.parity_category == ParityCategory.PARITY_REPRODUCES
        assert [artifact.name for artifact in result.artifacts] == ["dem_tif", "dem_npy"]
        assert all(artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE for artifact in result.artifacts)
        assert result.metadata["tile_size"] == DEM_TILE_SIZE
        assert result.metadata["tile_count"] == 4

        tif_path = run_dir / "dem.tif"
        npy_path = run_dir / "dem.npy"
        assert tif_path.is_file()
        assert npy_path.is_file()

        array = np.load(npy_path)
        assert array.shape == (640, 640)

        sidecar = read_manifest(raster_sidecar_path(tif_path))
        assert sidecar["crs"] == "EPSG:32637"
        assert sidecar["width"] == 640
        assert sidecar["height"] == 640
        assert sidecar["transform"] == [10.0, 0.0, -3200.0, 0.0, -10.0, 3200.0]


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
