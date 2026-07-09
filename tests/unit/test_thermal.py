from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.thermal import (
    DEFAULT_END,
    DEFAULT_START,
    L9_RAW_ST_B10_NPY_NAME,
    NOTEBOOK_L9_ST_B10_COLLECTION,
    NOTEBOOK_THERMAL_END,
    NOTEBOOK_THERMAL_INERTIA_NAME,
    NOTEBOOK_THERMAL_START,
    RAW_ST_B10_NPY_NAME,
    ThermalOutputs,
    ThermalStage,
    build_landsat_lst_collection,
    build_landsat_st_b10_collection,
    build_notebook_l9_st_b10_image,
    build_notebook_thermal_inertia_image,
    create_ee_lst_fetcher,
    create_ee_notebook_thermal_inertia_fetcher,
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


def test_build_landsat_st_b10_collection_uses_notebook_filters(monkeypatch: pytest.MonkeyPatch) -> None:
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

    build_landsat_st_b10_collection(grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)

    assert ("ImageCollection", "LANDSAT/LC08/C02/T1_L2") in calls
    assert ("ImageCollection", "LANDSAT/LC09/C02/T1_L2") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (DEFAULT_START, DEFAULT_END)) in calls
    assert ("map", "prep_landsat_st_b10") in calls


def test_build_notebook_l9_st_b10_image_uses_notebook_source(monkeypatch: pytest.MonkeyPatch) -> None:
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

        def map(self, func):
            calls.append(("map", func.__name__))
            return self

        def median(self):
            calls.append(("median", None))
            return self

    monkeypatch.setattr("app.pipeline.stages.thermal.ee.ImageCollection", FakeCollection)
    monkeypatch.setattr("app.pipeline.stages.thermal.build_grid_region", lambda _grid_spec: "grid-region")

    build_notebook_l9_st_b10_image(grid_spec)

    assert ("ImageCollection", NOTEBOOK_L9_ST_B10_COLLECTION) in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (NOTEBOOK_THERMAL_START, NOTEBOOK_THERMAL_END)) in calls
    assert ("map", "prep_notebook_l9_st_b10") in calls
    assert ("median", None) in calls
    assert not any(call == ("ImageCollection", "LANDSAT/LC08/C02/T1_L2") for call in calls)


def test_build_notebook_thermal_inertia_image_uses_ee_focal_mean(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    operations: list[str] = []

    class FakeBand:
        def __init__(self, name):
            self.name = name

        def focal_mean(self, *, radius, units):
            operations.append(f"{self.name}.focal_mean({radius},{units})")
            return FakeBand(f"{self.name}.mean")

        def add(self, value):
            other = value.name if isinstance(value, FakeBand) else value
            operations.append(f"{self.name}.add({other})")
            return FakeBand(f"{self.name}+eps")

        def divide(self, other):
            operations.append(f"{self.name}.divide({other.name})")
            return FakeBand(f"{self.name}/{other.name}")

        def rename(self, name):
            operations.append(f"{self.name}.rename({name})")
            return FakeImage(name)

    class FakeImage:
        def __init__(self, name):
            self.name = name

        def toFloat(self):
            operations.append("toFloat")
            return self

        def reproject(self, *, crs, crsTransform):
            operations.append(f"reproject({crs})")
            assert crs == grid_spec.crs
            assert crsTransform == list(grid_spec.transform)
            return self

        def clip(self, region):
            operations.append(f"clip({region})")
            return self

    class FakeEeImage:
        @staticmethod
        def constant(value):
            operations.append(f"constant({value})")
            return FakeBand("eps")

    monkeypatch.setattr("app.pipeline.stages.thermal.build_notebook_l9_st_b10_image", lambda _grid_spec: FakeBand("ST_B10"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_grid_region", lambda _grid_spec: "grid-region")
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Image", FakeEeImage)

    build_notebook_thermal_inertia_image(grid_spec)

    assert "constant(1e-06)" in operations
    assert "ST_B10.focal_mean(500,meters)" in operations
    assert "ST_B10.divide(ST_B10.mean+eps)" in operations
    assert f"ST_B10/ST_B10.mean+eps.rename({NOTEBOOK_THERMAL_INERTIA_NAME})" in operations


def test_create_ee_lst_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-thermal-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def __init__(self, band_name):
            self.band_name = band_name

        def getInfo(self):
            return {"properties": {self.band_name: [[300.0] * 320 for _ in range(320)]}}

    class FakeMappedCollection:
        def __init__(self, band_name):
            self.band_name = band_name

        def median(self):
            return FakeImage(self.band_name)

    class FakeImage:
        def __init__(self, band_name="LST_DAY_K"):
            self.band_name = band_name

        def rename(self, name):
            self.band_name = name
            return self

        def sampleRectangle(self, *, region, defaultValue):
            assert region == "tile-region"
            assert defaultValue == grid_spec.nodata
            return FakeSampleResult(self.band_name)

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            rectangle_calls.append((coords, crs, geodesic))
            return "tile-region"

    monkeypatch.setattr("app.pipeline.stages.thermal.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_landsat_lst_collection", lambda *_args, **_kwargs: FakeMappedCollection("LST_DAY_K"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_landsat_st_b10_collection", lambda *_args, **_kwargs: FakeMappedCollection("ST_B10_RAW"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_notebook_l9_st_b10_image", lambda _grid_spec: FakeImage("ST_B10"))
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Image", lambda image: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.to_grid_lst", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.finalize_for_sample", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Geometry", FakeGeometry)

    fetcher = create_ee_lst_fetcher(settings, grid_spec)
    outputs = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert outputs.lst.shape == (640, 640)
    assert outputs.lst.dtype == np.float32
    assert outputs.st_b10_raw.shape == (640, 640)
    assert outputs.st_b10_raw.dtype == np.float32
    assert outputs.l9_st_b10_raw.shape == (640, 640)
    assert outputs.l9_st_b10_raw.dtype == np.float32
    assert len(rectangle_calls) == 4


def test_create_ee_notebook_thermal_inertia_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-notebook-thermal-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {NOTEBOOK_THERMAL_INERTIA_NAME: [[1.25] * 320 for _ in range(320)]}}

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

    monkeypatch.setattr("app.pipeline.stages.thermal.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.thermal.build_notebook_thermal_inertia_image", lambda _grid_spec: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.thermal.ee.Geometry", FakeGeometry)

    fetcher = create_ee_notebook_thermal_inertia_fetcher(settings, grid_spec)
    array = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert array.shape == (640, 640)
    assert array.dtype == np.float32
    assert array[0, 0] == np.float32(1.25)
    assert len(rectangle_calls) == 4


def test_thermal_stage_rejects_all_nodata_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        def all_nodata_fetcher(*, grid_spec):
            array = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
            return ThermalOutputs(lst=array, st_b10_raw=array, l9_st_b10_raw=array)

        with pytest.raises(StageError, match="insufficient valid data"):
            asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=all_nodata_fetcher).run(context))


def test_thermal_stage_writes_classified_grid_aligned_output() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))

        assert [artifact.name for artifact in result.artifacts] == ["lst", "thermal_summary", "st_b10_raw", "l9_st_b10_raw"]
        assert result.artifacts[0].artifact_class == ArtifactClass.LOCAL_SENSITIVE
        assert result.artifacts[1].artifact_class == ArtifactClass.FILESYSTEM_ONLY
        assert result.artifacts[2].artifact_class == ArtifactClass.FILESYSTEM_ONLY
        assert result.artifacts[3].artifact_class == ArtifactClass.FILESYSTEM_ONLY
        sidecar = read_manifest(raster_sidecar_path(run_dir / "lst.tif"))
        assert sidecar["transform"] == grid_spec.manifest.crs_transform
        assert np.load(run_dir / RAW_ST_B10_NPY_NAME).shape == (grid_spec.size, grid_spec.size)
        assert np.load(run_dir / L9_RAW_ST_B10_NPY_NAME).shape == (grid_spec.size, grid_spec.size)
        assert result.metadata["valid_fractions"] == {
            "lst": 1.0,
            "st_b10_raw": 1.0,
            "l9_st_b10_raw": 1.0,
        }
        summary = json.loads((run_dir / "QA" / "stacks" / "thermal_summary.json").read_text(encoding="utf-8"))
        assert summary["stage"] == "thermal"
        assert summary["start_date"] == DEFAULT_START
        assert summary["end_date"] == DEFAULT_END
        assert summary["valid_fractions"] == {
            "lst": 1.0,
            "st_b10_raw": 1.0,
            "l9_st_b10_raw": 1.0,
        }
        assert summary["l9_st_b10_source_collection"] == NOTEBOOK_L9_ST_B10_COLLECTION
        assert summary["l9_st_b10_unit"] == "raw_dn"


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
