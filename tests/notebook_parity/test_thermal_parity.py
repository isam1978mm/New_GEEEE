from __future__ import annotations

from app.pipeline._base import ParityCategory
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.thermal import (
    DEFAULT_END,
    DEFAULT_START,
    ThermalStage,
    build_landsat_lst_collection,
    create_ee_lst_fetcher,
    finalize_for_sample,
    prep_landsat_l2,
    to_grid_lst,
)


def test_thermal_parity_uses_notebook_landsat_lst_sequence(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeMask:
        def __init__(self, label):
            self.label = label

        def bitwiseAnd(self, value):
            calls.append(("bitwiseAnd", value))
            return FakeMask(f"{self.label}:{value}")

        def eq(self, value):
            calls.append(("eq", (self.label, value)))
            return self

        def And(self, other):
            calls.append(("And", (self.label, getattr(other, "label", other))))
            return self

    class FakeSampleResult:
        def __init__(self, band_name):
            self.band_name = band_name

        def getInfo(self):
            calls.append(("getInfo", None))
            return {"properties": {self.band_name: [[300.0] * 320 for _ in range(320)]}}

    class FakeImage:
        def __init__(self):
            self.band_name = "LST_DAY_K"

        def select(self, name):
            calls.append(("select", name))
            return self if name == "ST_B10" else FakeMask(name)

        def multiply(self, value):
            calls.append(("multiply", value))
            return self

        def add(self, value):
            calls.append(("add", value))
            return self

        def rename(self, value):
            calls.append(("rename", value))
            self.band_name = value
            return self

        def updateMask(self, mask):
            calls.append(("updateMask", getattr(mask, "label", mask)))
            return self

        def copyProperties(self, _img, props):
            calls.append(("copyProperties", props))
            return self

        def toFloat(self):
            calls.append(("toFloat", None))
            return self

        def reproject(self, *, crs, crsTransform):
            calls.append(("reproject", {"crs": crs, "crsTransform": crsTransform}))
            return self

        def clip(self, region):
            calls.append(("clip", region))
            return self

        def unmask(self, nodata):
            calls.append(("unmask", nodata))
            return self

        def sampleRectangle(self, *, region, defaultValue):
            calls.append(("sampleRectangle", {"region": region, "defaultValue": defaultValue}))
            return FakeSampleResult(self.band_name)

    class FakeCollection:
        def __init__(self, dataset):
            calls.append(("ImageCollection", dataset))

        def filterBounds(self, region):
            calls.append(("filterBounds", region))
            return self

        def filterDate(self, start, end):
            calls.append(("filterDate", (start, end)))
            return self

        def merge(self, other):
            calls.append(("merge", other))
            return self

        def map(self, func):
            calls.append(("map", func.__name__))
            return self

        def median(self):
            calls.append(("median", None))
            return FakeImage()

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            calls.append(("Rectangle", {"coords": coords, "crs": crs, "geodesic": geodesic}))
            return "grid-region"

    monkeypatch.setattr("app.pipeline.stages.thermal.initialize_ee_session", lambda settings: calls.append(("init", settings.bind_host)))
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.ImageCollection", FakeCollection)
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Image", lambda image: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Geometry", FakeGeometry)

    prep_landsat_l2(FakeImage())
    collection = build_landsat_lst_collection(grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    grid_image = to_grid_lst(collection.median().rename("LST_DAY_K"), grid_spec)
    sampled_image = finalize_for_sample(grid_image, grid_spec)
    fetcher = create_ee_lst_fetcher(_settings(), grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    outputs = fetcher(grid_spec=grid_spec)

    assert ThermalStage.parity_category is ParityCategory.PARITY_REPRODUCES
    assert outputs.lst.shape == (640, 640)
    assert outputs.st_b10_raw.shape == (640, 640)
    assert ("ImageCollection", "LANDSAT/LC08/C02/T1_L2") in calls
    assert ("ImageCollection", "LANDSAT/LC09/C02/T1_L2") in calls
    assert ("filterDate", (DEFAULT_START, DEFAULT_END)) in calls
    assert ("map", "prep_landsat_l2") in calls
    assert ("bitwiseAnd", 16) in calls
    assert ("bitwiseAnd", 8) in calls
    assert ("bitwiseAnd", 4) in calls
    assert ("multiply", 0.00341802) in calls
    assert ("add", 149.0) in calls
    assert ("rename", "LST_DAY_K") in calls
    assert ("median", None) in calls
    assert ("reproject", {"crs": grid_spec.crs, "crsTransform": list(grid_spec.transform)}) in calls
    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 12
    assert sampled_image is not None


def _settings():
    from app.config import Settings

    return Settings()
