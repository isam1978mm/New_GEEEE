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
from app.pipeline.stages.s2_indices import (
    INDEX_NAMES,
    S2_DEM_MATCHED_MASK_MANIFEST_JSON,
    S2_INDEX_VALID_MASK_TIF,
    S2_MASK_OUTPUT_DIR,
    S2_RAW_VALID_MASK_TIF,
    S2_SOURCE_BANDS,
    S2IndicesStage,
    build_s2_composite,
    compute_s2_dem_matched_masks,
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


def test_compute_s2_indices_masks_only_formulas_that_require_nodata_band() -> None:
    nodata = -9999.0
    cube = np.zeros((1, 1, len(S2_SOURCE_BANDS)), dtype=np.float32)
    cube[:, :, 0] = 0.1  # B2
    cube[:, :, 1] = 0.2  # B3
    cube[:, :, 2] = 0.3  # B4
    cube[:, :, 3] = 0.6  # B8
    cube[:, :, 4] = 0.4  # B11
    cube[:, :, 5] = nodata  # B12

    outputs = compute_s2_indices(cube, nodata=nodata)

    assert outputs["NBR"][0, 0] == nodata
    assert outputs["IRON_SWIR"][0, 0] == nodata
    assert outputs["NDVI"][0, 0] == pytest.approx((0.6 - 0.3) / (0.6 + 0.3))
    assert outputs["NDMI"][0, 0] == pytest.approx((0.6 - 0.4) / (0.6 + 0.4))
    assert outputs["BSI"][0, 0] == pytest.approx(((0.4 + 0.3) - (0.6 + 0.1)) / ((0.4 + 0.3) + (0.6 + 0.1)))


def test_compute_s2_dem_matched_masks_tracks_raw_and_index_validity() -> None:
    nodata = -9999.0
    cube = np.ones((2, 2, len(S2_SOURCE_BANDS)), dtype=np.float32)
    cube[0, 1, 5] = nodata
    outputs = compute_s2_indices(cube, nodata=nodata)

    masks = compute_s2_dem_matched_masks(cube, outputs, nodata=nodata)

    assert masks["raw_valid_mask"].dtype == np.uint8
    assert masks["index_valid_mask"].dtype == np.uint8
    assert masks["raw_valid_mask"].tolist() == [[1, 0], [1, 1]]
    assert masks["index_valid_mask"].tolist() == [[1, 0], [1, 1]]


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
    assert ("select", ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]) in calls
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

        assert [artifact.name for artifact in result.artifacts] == [
            *INDEX_NAMES,
            "s2_raw_valid_mask_640",
            "s2_index_valid_mask_640",
            "s2_dem_matched_masks_manifest",
            "s2_indices_summary",
            "s2_raw_cube",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        for name in INDEX_NAMES:
            assert artifact_classes[name] == ArtifactClass.LOCAL_SENSITIVE
        for name in ("s2_raw_valid_mask_640", "s2_index_valid_mask_640", "s2_dem_matched_masks_manifest", "s2_indices_summary", "s2_raw_cube"):
            assert artifact_classes[name] == ArtifactClass.FILESYSTEM_ONLY
        assert all(artifact.http_servable is False for artifact in result.artifacts if artifact.name.startswith("s2_") and artifact.name not in INDEX_NAMES)
        assert result.metadata["band_names"] == list(INDEX_NAMES)
        assert result.metadata["mask_names"] == ["s2_raw_valid_mask_640", "s2_index_valid_mask_640"]

        for name in INDEX_NAMES:
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform
        for filename in (S2_RAW_VALID_MASK_TIF, S2_INDEX_VALID_MASK_TIF):
            sidecar = read_manifest(raster_sidecar_path(run_dir / S2_MASK_OUTPUT_DIR / filename))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform
            assert sidecar["dtype"] == "uint8"
            assert sidecar["nodata"] == 0.0

        summary = json.loads((run_dir / "QA" / "stacks" / "s2_indices_summary.json").read_text(encoding="utf-8"))
        assert summary["stage"] == "s2_indices"
        assert summary["index_bands"] == list(INDEX_NAMES)
        assert summary["source_bands"] == list(S2_SOURCE_BANDS)

        mask_manifest = json.loads((run_dir / S2_MASK_OUTPUT_DIR / S2_DEM_MATCHED_MASK_MANIFEST_JSON).read_text(encoding="utf-8"))
        assert mask_manifest["schema"] == "s2_dem_matched_masks_v1"
        assert mask_manifest["coordinate_space"] == "authoritative_grid"
        assert mask_manifest["grid_shape"] == [grid_spec.size, grid_spec.size]
        assert mask_manifest["privacy"] == {"artifact_class": "FILESYSTEM_ONLY", "http_servable": False}
        assert mask_manifest["date_rules"]["primary_start"] == "2022-01-01"
        assert mask_manifest["date_rules"]["primary_cloud_max"] == 3
        assert mask_manifest["date_rules"]["notebook_secret_cloud_max"] == 5
        assert mask_manifest["date_rules"]["notebook_report_cloud_max"] == 10
        assert mask_manifest["masks"]["raw_valid_mask"]["valid_fraction"] == 1.0
        assert mask_manifest["masks"]["index_valid_mask"]["valid_fraction"] == 1.0


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
