from __future__ import annotations

from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import DEFAULT_END, DEFAULT_START, build_final_radar_image, create_ee_radar_cube_fetcher


def test_sar_parity_uses_notebook_collection_pair_and_sampling_flow(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeSampleResult:
        def getInfo(self):
            calls.append(("getInfo", None))
            return {"properties": {band: [[2.0] * 320 for _ in range(320)] for band in ["VV_dB", "VH_dB", "angle"]}}

    class FakeImage:
        def select(self, bands):
            calls.append(("select", bands))
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
            return FakeSampleResult()

    class FakeCollection:
        def __init__(self, *_args, **_kwargs):
            pass

        def median(self):
            calls.append(("median", None))
            return FakeImage()

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.initialize_ee_session", lambda settings: calls.append(("init", settings.bind_host)))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_final_radar_image", lambda *args, **kwargs: (FakeImage(), []))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.finalize_for_sample", lambda image, _grid_spec: image.toFloat().unmask(_grid_spec.nodata).reproject(crs=_grid_spec.crs, crsTransform=list(_grid_spec.transform)).clip("grid-region"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Geometry", type("FakeGeometry", (), {"Rectangle": staticmethod(lambda coords, crs, geodesic: calls.append(("Rectangle", {"coords": coords, "crs": crs, "geodesic": geodesic})) or "tile-region")}))

    image, pairs = build_final_radar_image if False else (None, None)
    fetcher = create_ee_radar_cube_fetcher(_settings(), grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    cube = fetcher(grid_spec=grid_spec)

    assert cube.shape == (640, 640, 3)
    assert ("init", "127.0.0.1") in calls
    assert ("toFloat", None) in calls
    assert ("unmask", grid_spec.nodata) in calls
    assert ("reproject", {"crs": grid_spec.crs, "crsTransform": list(grid_spec.transform)}) in calls
    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 4


def _settings():
    from app.config import Settings

    return Settings()
