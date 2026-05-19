from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import (
    INDEX_NAMES,
    S2_SOURCE_BANDS,
    S2IndicesStage,
    build_s2_composite,
    compute_s2_indices,
    create_ee_s2_cube_fetcher,
    deterministic_s2_cube_fetcher,
)
from app.services.storage import read_manifest


def test_compute_s2_indices_uses_correct_iron_swir_formula() -> None:
    cube = np.zeros((2, 2, len(S2_SOURCE_BANDS)), dtype=np.float32)
    cube[:, :, 0] = 0.1  # B2
    cube[:, :, 1] = 0.2  # B3
    cube[:, :, 2] = 0.3  # B4
    cube[:, :, 3] = 0.6  # B8
    cube[:, :, 4] = 0.4  # B11
    cube[:, :, 5] = 0.25  # B12

    outputs = compute_s2_indices(cube, nodata=-9999.0)

    expected = (0.4 - 0.25) / (0.4 + 0.25)
    assert outputs["IRON_SWIR"][0, 0] == pytest.approx(expected)
    assert outputs["IRON_SWIR"][0, 0] != pytest.approx(1.0)


def test_build_s2_composite_uses_notebook_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeFilter:
        @staticmethod
        def lt(name, value):
            return ("lt", name, value)

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

        def median(self):
            calls.append(("median", None))
            return self

    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.Filter", FakeFilter)
    monkeypatch.setattr(
        "app.pipeline.stages.s2_indices.ee.ImageCollection",
        lambda dataset: calls.append(("ImageCollection", dataset)) or FakeCollection(),
    )
    monkeypatch.setattr("app.pipeline.stages.s2_indices.build_grid_region", lambda _grid_spec: "grid-region")

    build_s2_composite(grid_spec)

    assert ("ImageCollection", "COPERNICUS/S2_SR_HARMONIZED") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", ("2022-01-01", "2026-02-28")) in calls
    assert ("filter", ("lt", "CLOUDY_PIXEL_PERCENTAGE", 3)) in calls
    assert ("select", ["B2", "B3", "B4", "B8", "B11", "B12"]) in calls
    assert ("median", None) in calls


def test_create_ee_s2_cube_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-s2-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {band: [[1.0] * 320 for _ in range(320)] for band in S2_SOURCE_BANDS}}

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

    monkeypatch.setattr("app.pipeline.stages.s2_indices.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.s2_indices.build_s2_composite", lambda *_args, **_kwargs: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.s2_indices.to_grid_s2", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.s2_indices.finalize_for_sample", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.s2_indices.ee.Geometry", FakeGeometry)

    fetcher = create_ee_s2_cube_fetcher(settings, grid_spec)
    cube = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert cube.shape == (640, 640, len(S2_SOURCE_BANDS))
    assert cube.dtype == np.float32
    assert len(rectangle_calls) == 4


def test_s2_indices_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))

        assert [artifact.name for artifact in result.artifacts] == list(INDEX_NAMES)
        assert all(artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE for artifact in result.artifacts)
        assert result.metadata["band_names"] == list(INDEX_NAMES)

        for name in INDEX_NAMES:
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
