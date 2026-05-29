from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.report_640 import (
    NOTEBOOK_REPORT_S2_CLOUD_MAX,
    NOTEBOOK_REPORT_S2_END,
    NOTEBOOK_REPORT_S2_SOURCE_BANDS,
    NOTEBOOK_REPORT_S2_START,
    Report640Stage,
    build_notebook_report_pottery_image,
    build_notebook_report_s2_composite,
    compute_report_mass_report,
    compute_report_pottery_report,
    compute_report_zero_point_targets,
    create_ee_notebook_report_pottery_fetcher,
)
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_report_640_stage_emits_three_implemented_reports() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        result = asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        artifact_names = {a.name for a in result.artifacts}
        assert "REPORT_640_Pottery_Report" in artifact_names
        assert "REPORT_640_Mass_Report" in artifact_names
        assert "REPORT_640_FINAL_Zero_Point_Targets" in artifact_names
        assert "REPORT_640_manifest" in artifact_names

        metadata = result.metadata
        assert set(metadata["implemented_reports"]) == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }
        assert metadata["not_implemented_reports"] == []

        mass_detail = metadata["report_details"]["REPORT_640_Mass_Report"]
        assert mass_detail["status"] == "implemented"
        assert mass_detail["formula"] == "B12 * ST_B10 / 1000"


def test_report_640_manifest_documents_three_implemented_reports() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        manifest_path = run_dir / "QA" / "REPORT_640_manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "notebook_report_640_manifest_v1"
        assert manifest["stage"] == "report_640"
        assert set(manifest["reports"]) == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }

        assert manifest["reports"]["REPORT_640_Pottery_Report.tif"]["status"] == "implemented"
        assert manifest["reports"]["REPORT_640_FINAL_Zero_Point_Targets.tif"]["status"] == "implemented"
        mass_report = manifest["reports"]["REPORT_640_Mass_Report.tif"]
        assert mass_report["status"] == "implemented"
        assert mass_report["formula"] == "B12 * ST_B10 / 1000"
        assert "s2_raw_cube.npy" in mass_report["source_equivalent"]
        assert "st_b10_raw.npy" in mass_report["source_equivalent"]


def test_notebook_report_s2_composite_uses_report_provenance(monkeypatch) -> None:
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

    monkeypatch.setattr("app.pipeline.stages.report_640.ee.Filter", FakeFilter)
    monkeypatch.setattr(
        "app.pipeline.stages.report_640.ee.ImageCollection",
        lambda dataset: calls.append(("ImageCollection", dataset)) or FakeCollection(),
    )
    monkeypatch.setattr("app.pipeline.stages.report_640.build_grid_region", lambda _grid_spec: "grid-region")

    build_notebook_report_s2_composite(grid_spec)

    assert ("ImageCollection", "COPERNICUS/S2_SR_HARMONIZED") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (NOTEBOOK_REPORT_S2_START, NOTEBOOK_REPORT_S2_END)) in calls
    assert ("filter", ("lt", "CLOUDY_PIXEL_PERCENTAGE", NOTEBOOK_REPORT_S2_CLOUD_MAX)) in calls
    assert ("select", list(NOTEBOOK_REPORT_S2_SOURCE_BANDS)) in calls
    assert ("median", None) in calls


def test_notebook_report_pottery_image_builds_ee_formula(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    operations: list[str] = []

    class FakeBand:
        def __init__(self, name):
            self.name = name

        def divide(self, other):
            operations.append(f"{self.name}.divide({other.name})")
            return FakeBand(f"{self.name}/{other.name}")

        def rename(self, name):
            operations.append(f"{self.name}.rename({name})")
            return FakeImage(name)

    class FakeS2:
        def select(self, name):
            operations.append(f"select({name})")
            return FakeBand(name)

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

    monkeypatch.setattr("app.pipeline.stages.report_640.build_notebook_report_s2_composite", lambda _grid_spec: FakeS2())
    monkeypatch.setattr("app.pipeline.stages.report_640.build_grid_region", lambda _grid_spec: "grid-region")

    build_notebook_report_pottery_image(grid_spec)

    assert "B12.divide(B11)" in operations
    assert "B12/B11.rename(REPORT_640_Pottery_Report)" in operations
    assert "toFloat" in operations


def test_create_ee_notebook_report_pottery_fetcher_uses_sample_rectangle(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-report-pottery-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {"REPORT_640_Pottery_Report": [[7.0] * 320 for _ in range(320)]}}

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

    monkeypatch.setattr("app.pipeline.stages.report_640.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.report_640.build_notebook_report_pottery_image", lambda _grid_spec: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.report_640.ee.Geometry", FakeGeometry)

    fetcher = create_ee_notebook_report_pottery_fetcher(settings, grid_spec)
    array = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert array.shape == (640, 640)
    assert array.dtype == np.float32
    assert array[0, 0] == np.float32(7.0)
    assert len(rectangle_calls) == 4


def test_report_640_stage_uses_pottery_fetcher_only_for_pottery_report() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)
        calls: list[str] = []
        pottery = np.full((grid_spec.size, grid_spec.size), 7.0, dtype=np.float32)

        def pottery_fetcher(*, grid_spec):
            calls.append(grid_spec.crs)
            return pottery

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(Report640Stage(grid_spec=grid_spec, pottery_fetcher=pottery_fetcher).run(context))

        with rasterio.open(run_dir / "REPORT_640_Pottery_Report.tif") as dataset:
            assert dataset.read(1)[0, 0] == np.float32(7.0)

        with rasterio.open(run_dir / "REPORT_640_Mass_Report.tif") as dataset:
            assert dataset.read(1)[0, 0] != np.float32(7.0)

        with rasterio.open(run_dir / "REPORT_640_FINAL_Zero_Point_Targets.tif") as dataset:
            assert dataset.read(1)[0, 0] in {np.float32(0.0), np.float32(1.0)}

        manifest = json.loads((run_dir / "QA" / "REPORT_640_manifest.json").read_text(encoding="utf-8"))
        pottery_report = manifest["reports"]["REPORT_640_Pottery_Report.tif"]
        mass_report = manifest["reports"]["REPORT_640_Mass_Report.tif"]
        zero_report = manifest["reports"]["REPORT_640_FINAL_Zero_Point_Targets.tif"]
        assert pottery_report["source_provenance"] == "notebook_report_s2"
        assert mass_report["source_equivalent"] != "notebook_report_s2"
        assert zero_report["source_equivalent"] != "notebook_report_s2"
        assert calls == [grid_spec.crs]


def test_implemented_report_rasters_match_grid_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        for report_name in (
            "REPORT_640_Pottery_Report",
            "REPORT_640_Mass_Report",
            "REPORT_640_FINAL_Zero_Point_Targets",
        ):
            tif_path = run_dir / f"{report_name}.tif"
            assert tif_path.is_file(), f"Missing {tif_path}"
            with rasterio.open(tif_path) as dataset:
                assert dataset.width == grid_spec.size
                assert dataset.height == grid_spec.size
                assert str(dataset.crs) == grid_spec.crs
                assert dataset.count == 1
                assert dataset.dtypes == ("float32",)
                assert float(dataset.nodata) == float(grid_spec.nodata)

            tags_text = json.dumps(dataset.tags())
            assert str(run_dir) not in tags_text
            assert "C:\\" not in tags_text


def test_mass_report_raster_is_emitted_with_grid_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))

        tif_path = run_dir / "REPORT_640_Mass_Report.tif"
        assert tif_path.is_file()
        with rasterio.open(tif_path) as dataset:
            assert dataset.width == grid_spec.size
            assert dataset.height == grid_spec.size
            assert str(dataset.crs) == grid_spec.crs
            assert dataset.count == 1
            assert dataset.dtypes == ("float32",)
            assert float(dataset.nodata) == float(grid_spec.nodata)


def test_mass_report_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    st_b10 = np.ones((size, size), dtype=np.float32) * 200.0
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), np.zeros((size, size)), b12, np.zeros((size, size))
    ], axis=-1)
    result = compute_report_mass_report(cube, st_b10, nodata=-9999.0)
    expected = np.float32((0.5 * 200.0) / 1000.0)
    assert np.allclose(result, expected)


def test_pottery_report_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b11 = np.ones((size, size), dtype=np.float32) * 0.25
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), b11, b12, np.zeros((size, size))
    ], axis=-1)
    result = compute_report_pottery_report(cube, nodata=-9999.0)
    expected = np.float32(0.5 / 0.25)
    assert np.allclose(result, expected)


def test_zero_point_targets_all_conditions_met() -> None:
    size = 64
    # Set up bands so all three conditions are met
    b12 = np.ones((size, size), dtype=np.float32) * 0.5   # B12/B11 = 0.5/0.3 = 1.67 > 1.45
    b11 = np.ones((size, size), dtype=np.float32) * 0.3
    b4 = np.ones((size, size), dtype=np.float32) * 0.4    # B4/B3 = 0.4/0.2 = 2.0 > 1.25
    b3 = np.ones((size, size), dtype=np.float32) * 0.2
    b8 = np.ones((size, size), dtype=np.float32) * 0.8    # NDVI = (0.8-0.4)/(0.8+0.4) = 0.33
    # S2_SOURCE_BANDS = (B2, B3, B4, B8, B11, B12, B1)
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=-9999.0)
    # NDVI = 0.33 which is NOT > 0.35, so all conditions are NOT met
    assert (result == 0.0).all() or (result == -9999.0).all()

    # Now make NDVI > 0.35
    b8 = np.ones((size, size), dtype=np.float32) * 0.9    # NDVI = (0.9-0.4)/(0.9+0.4) = 0.38 > 0.35
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=-9999.0)
    assert (result == 1.0).all()


def test_zero_point_targets_respects_nodata() -> None:
    size = 64
    nodata = -9999.0
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b11 = np.ones((size, size), dtype=np.float32) * 0.3
    b4 = np.ones((size, size), dtype=np.float32) * 0.4
    b3 = np.ones((size, size), dtype=np.float32) * 0.2
    b8 = np.ones((size, size), dtype=np.float32) * 0.9
    b3[0, 0] = nodata
    cube = np.stack([
        np.zeros((size, size)),  # B2
        b3,                       # B3
        b4,                       # B4
        b8,                       # B8
        b11,                      # B11
        b12,                      # B12
        np.zeros((size, size)),   # B1
    ], axis=-1)
    result = compute_report_zero_point_targets(cube, nodata=nodata)
    assert result[0, 0] == nodata
    assert (result[1:, 1:] == 1.0).all()


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
