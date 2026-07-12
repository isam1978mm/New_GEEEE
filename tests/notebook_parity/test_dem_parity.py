from __future__ import annotations

from pyproj import Transformer

from app.pipeline.stages.dem import DEM_TILE_SIZE, build_ee_dem_image, create_ee_dem_tile_fetcher
from app.pipeline.stages.grid import build_run_grid


def test_dem_parity_uses_notebook_gee_ingest_flow(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeSampleResult:
        def getInfo(self):
            calls.append(("getInfo", None))
            return {"properties": {"DEM": [[7.0] * DEM_TILE_SIZE for _ in range(DEM_TILE_SIZE)]}}

    class FakeImage:
        def select(self, band):
            calls.append(("select", band))
            return self

        def clip(self, region):
            calls.append(("clip", region))
            return self

        def toFloat(self):
            calls.append(("toFloat", None))
            return self

        def reproject(self, *, crs, crsTransform):
            calls.append(("reproject", {"crs": crs, "crsTransform": crsTransform}))
            return self

        def unmask(self, nodata):
            calls.append(("unmask", nodata))
            return self

        def sampleRectangle(self, *, region, defaultValue):
            calls.append(("sampleRectangle", {"region": region, "defaultValue": defaultValue}))
            return FakeSampleResult()

    class FakeImageCollection:
        def __init__(self, dataset):
            calls.append(("ImageCollection", dataset))

        def mosaic(self):
            calls.append(("mosaic", None))
            return FakeImage()

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            calls.append(("Rectangle", {"coords": coords, "crs": crs, "geodesic": geodesic}))
            return {"coords": coords, "crs": crs, "geodesic": geodesic}

    monkeypatch.setattr("app.pipeline.stages.dem.ee.ImageCollection", FakeImageCollection)
    monkeypatch.setattr("app.pipeline.stages.dem.ee.Geometry", FakeGeometry)
    monkeypatch.setattr("app.pipeline.stages.dem.initialize_ee_session", lambda settings: calls.append(("init", settings.bind_host)))

    image = build_ee_dem_image(grid_spec)
    assert image is not None

    fetcher = create_ee_dem_tile_fetcher(_settings(), grid_spec)
    tile = fetcher(
        grid_spec=grid_spec,
        tile_row=0,
        tile_col=0,
        xmin=grid_spec.manifest.bounds_m["xmin"],
        ymin=(grid_spec.manifest.bounds_m["ymin"] + grid_spec.manifest.bounds_m["ymax"]) / 2.0,
        xmax=(grid_spec.manifest.bounds_m["xmin"] + grid_spec.manifest.bounds_m["xmax"]) / 2.0,
        ymax=grid_spec.manifest.bounds_m["ymax"],
        size=DEM_TILE_SIZE,
    )

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{grid_spec.manifest.epsg}", always_xy=True)
    center_x, center_y = transformer.transform(36.12694, 35.59499)
    expected_transform = [10.0, 0.0, center_x - 3200.0, 0.0, -10.0, center_y + 3200.0]

    assert tile.shape == (DEM_TILE_SIZE, DEM_TILE_SIZE)
    assert tile[0, 0] == 7.0
    assert ("ImageCollection", "COPERNICUS/DEM/GLO30_2024_1") in calls
    assert ("mosaic", None) in calls
    assert ("select", "DEM") in calls
    assert ("toFloat", None) in calls
    assert ("unmask", grid_spec.nodata) in calls
    assert (
        "reproject",
        {"crs": "EPSG:32637", "crsTransform": expected_transform},
    ) in calls
    sample_call = next(value for name, value in calls if name == "sampleRectangle")
    assert sample_call["defaultValue"] == grid_spec.nodata


def _settings():
    from app.config import Settings

    return Settings()
