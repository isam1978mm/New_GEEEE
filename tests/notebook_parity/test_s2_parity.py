from __future__ import annotations

from app.pipeline._base import ParityCategory
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import (
    DEFAULT_END,
    DEFAULT_START,
    S2_SOURCE_BANDS,
    S2IndicesStage,
    build_s2_composite,
    create_ee_s2_cube_fetcher,
    finalize_for_sample,
    to_grid_s2,
)


def test_s2_parity_uses_notebook_collection_and_sampling_flow(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeFilter:
        @staticmethod
        def lt(name, value):
            calls.append(("lt", (name, value)))
            return ("lt", name, value)

    class FakeSampleResult:
        def getInfo(self):
            calls.append(("getInfo", None))
            return {"properties": {band: [[2.0] * 320 for _ in range(320)] for band in S2_SOURCE_BANDS}}

    class FakeImage:
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
            return FakeSampleResult()

    class FakeCollection:
        def __init__(self, dataset):
            calls.append(("ImageCollection", dataset))

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

        def median(self):
            calls.append(("median", None))
            return FakeImage()

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            calls.append(("Rectangle", {"coords": coords, "crs": crs, "geodesic": geodesic}))
            return "grid-region"

    monkeypatch.setattr("app.pipeline.stages.s2_indices.initialize_ee_session", lambda settings: calls.append(("init", settings.bind_host)))
    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.Filter", FakeFilter)
    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.ImageCollection", FakeCollection)
    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.Image", lambda image: image)
    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.Geometry", FakeGeometry)

    composite = build_s2_composite(grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    grid_image = to_grid_s2(composite, grid_spec)
    sampled_image = finalize_for_sample(grid_image, grid_spec)

    fetcher = create_ee_s2_cube_fetcher(_settings(), grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    cube = fetcher(grid_spec=grid_spec)

    assert cube.shape == (640, 640, len(S2_SOURCE_BANDS))
    assert ("ImageCollection", "COPERNICUS/S2_SR_HARMONIZED") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (DEFAULT_START, DEFAULT_END)) in calls
    assert ("lt", ("CLOUDY_PIXEL_PERCENTAGE", 3)) in calls
    assert ("select", ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]) in calls
    assert ("median", None) in calls
    assert ("reproject", {"crs": grid_spec.crs, "crsTransform": list(grid_spec.transform)}) in calls
    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 4
    assert sampled_image is not None


def test_s2_parity_iron_swir_correction_reference() -> None:
    b11 = 0.4
    b12 = 0.25
    corrected = (b11 - b12) / (b11 + b12)
    buggy = (b11 - b12) / (b11 - b12)

    assert S2IndicesStage.parity_category is ParityCategory.PARITY_CORRECTS
    assert "notebook bug" in S2IndicesStage.parity_reason
    assert "B11+B12" in S2IndicesStage.parity_reason
    assert corrected != buggy
    assert corrected == (0.4 - 0.25) / (0.4 + 0.25)


def _settings():
    from app.config import Settings

    return Settings()
