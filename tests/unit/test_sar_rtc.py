from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import (
    RADAR_BANDS,
    SarRtcStage,
    apply_local_dem_rtc,
    build_s1_base_collection,
    create_ee_radar_cube_fetcher,
    deterministic_radar_cube_fetcher,
)
from app.services.storage import read_manifest


def test_apply_local_dem_rtc_builds_expected_bands_and_formula() -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    dem = np.full((grid_spec.size, grid_spec.size), 100.0, dtype=np.float32)
    cube = deterministic_radar_cube_fetcher(grid_spec=grid_spec)

    outputs = apply_local_dem_rtc(
        cube,
        dem,
        nodata=grid_spec.nodata,
        scale_m=float(grid_spec.manifest.scale_m),
    )

    assert set(outputs) == {"VV_dB", "VH_dB", "logRatio_dB", "incidence"}
    assert outputs["VV_dB"].shape == (640, 640)
    assert outputs["incidence"][0, 0] == np.float32(38.5)
    valid = outputs["logRatio_dB"] != grid_spec.nodata
    np.testing.assert_allclose(outputs["logRatio_dB"][valid], outputs["VV_dB"][valid] - outputs["VH_dB"][valid])

    # Flat DEM => corr = 1.0, so notebook local RTC reduces to dividing linear sigma0 by cos(incidence).
    vv_in = float(cube[0, 0, 0])
    cos_inc = float(np.cos(np.deg2rad(cube[0, 0, 2])))
    expected_vv = float(10.0 * np.log10((10.0 ** (vv_in / 10.0)) / cos_inc))
    assert outputs["VV_dB"][0, 0] == pytest.approx(expected_vv, abs=1e-5)


def test_apply_local_dem_rtc_uses_passed_scale_m() -> None:
    dem = np.arange(16, dtype=np.float32).reshape(4, 4)
    cube = np.stack(
        [
            np.full((4, 4), -10.0, dtype=np.float32),
            np.full((4, 4), -16.0, dtype=np.float32),
            np.full((4, 4), 38.5, dtype=np.float32),
        ],
        axis=-1,
    )

    outputs_scale_10 = apply_local_dem_rtc(cube, dem, nodata=-9999.0, scale_m=10.0)
    outputs_scale_20 = apply_local_dem_rtc(cube, dem, nodata=-9999.0, scale_m=20.0)

    assert not np.allclose(outputs_scale_10["VV_dB"], outputs_scale_20["VV_dB"])


def test_build_s1_base_collection_uses_notebook_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            return ("eq", name, value)

        @staticmethod
        def listContains(name, value):
            return ("listContains", name, value)

    class FakeCollection:
        def filterBounds(self, region):
            calls.append(("filterBounds", region))
            return self

        def filterDate(self, start, end):
            calls.append(("filterDate", (start, end)))
            return self

        def filter(self, predicate):
            calls.append(("filter", predicate))
            return self

        def select(self, bands):
            calls.append(("select", bands))
            return self

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc.ee.ImageCollection",
        lambda dataset: calls.append(("ImageCollection", dataset)) or FakeCollection(),
    )
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_grid_region", lambda _grid_spec: "grid-region")

    build_s1_base_collection(grid_spec, start_date="2026-01-01", end_date="2026-03-01")

    assert ("ImageCollection", "COPERNICUS/S1_GRD") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", ("2026-01-01", "2026-03-01")) in calls
    assert ("select", ["VV", "VH", "angle"]) in calls


def test_create_ee_radar_cube_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-sar-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {band: [[1.0] * 320 for _ in range(320)] for band in RADAR_BANDS}}

    class FakeImage:
        def sampleRectangle(self, *, region, defaultValue):
            assert region == "tile-region"
            assert defaultValue == grid_spec.nodata
            return FakeSampleResult()

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            rectangle_calls.append((coords, crs, geodesic))
            return "tile-region"

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_final_radar_image", lambda *_args, **_kwargs: (FakeImage(), []))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.finalize_for_sample", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Geometry", FakeGeometry)

    fetcher = create_ee_radar_cube_fetcher(settings, grid_spec, start_date="2026-01-01", end_date="2026-03-01")
    cube = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert cube.shape == (640, 640, 3)
    assert cube.dtype == np.float32
    assert len(rectangle_calls) == 4


def test_sar_rtc_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))

        result = asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))

        assert [artifact.name for artifact in result.artifacts] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]
        assert all(artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE for artifact in result.artifacts)
        assert result.metadata["band_names"] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]

        for name in ("VV_dB", "VH_dB", "logRatio_dB", "incidence"):
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
