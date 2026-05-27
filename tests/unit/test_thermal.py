from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.thermal import (
    DEFAULT_END,
    DEFAULT_START,
    ThermalStage,
    build_landsat_lst_collection,
    create_ee_lst_fetcher,
    deterministic_lst_fetcher,
)
from app.services.storage import read_manifest


def test_build_landsat_lst_collection_uses_notebook_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

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

    monkeypatch.setattr("app.pipeline.stages.thermal.ee.ImageCollection", FakeCollection)
    monkeypatch.setattr("app.pipeline.stages.thermal.build_grid_region", lambda _grid_spec: "grid-region")

    build_landsat_lst_collection(grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)

    assert ("ImageCollection", "LANDSAT/LC08/C02/T1_L2") in calls
    assert ("ImageCollection", "LANDSAT/LC09/C02/T1_L2") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (DEFAULT_START, DEFAULT_END)) in calls
    assert ("map", "prep_landsat_l2") in calls


def test_create_ee_lst_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-thermal-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {"LST_DAY_K": [[300.0] * 320 for _ in range(320)]}}

    class FakeMappedCollection:
        def median(self):
            return FakeImage()

    class FakeImage:
        def rename(self, _name):
            return self

        def sampleRectangle(self, *, region, defaultValue):
            assert region == "tile-region"
            assert defaultValue == grid_spec.nodata
            return FakeSampleResult()

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            rectangle_calls.append((coords, crs, geodesic))
            return "tile-region"

    monkeypatch.setattr("app.pipeline.stages.thermal.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_landsat_lst_collection", lambda *_args, **_kwargs: FakeMappedCollection())
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Image", lambda image: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.to_grid_lst", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.finalize_for_sample", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Geometry", FakeGeometry)

    fetcher = create_ee_lst_fetcher(settings, grid_spec)
    lst = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert lst.shape == (640, 640)
    assert lst.dtype == np.float32
    assert len(rectangle_calls) == 4


def test_thermal_stage_writes_classified_grid_aligned_output() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))

        assert [artifact.name for artifact in result.artifacts] == ["lst", "thermal_summary"]
        assert result.artifacts[0].artifact_class == ArtifactClass.LOCAL_SENSITIVE
        assert result.artifacts[1].artifact_class == ArtifactClass.FILESYSTEM_ONLY
        sidecar = read_manifest(raster_sidecar_path(run_dir / "lst.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform
        summary = json.loads((run_dir / "QA" / "stacks" / "thermal_summary.json").read_text(encoding="utf-8"))
        assert summary["stage"] == "thermal"
        assert summary["start_date"] == DEFAULT_START
        assert summary["end_date"] == DEFAULT_END


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
