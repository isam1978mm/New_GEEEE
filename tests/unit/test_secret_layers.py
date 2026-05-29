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
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.secret_layers import (
    NOTEBOOK_SECRET_S2_CLOUD_MAX,
    NOTEBOOK_SECRET_S2_END,
    NOTEBOOK_SECRET_S2_SOURCE_BANDS,
    NOTEBOOK_SECRET_S2_START,
    SECRET_LAYER_SPECS,
    SecretLayersStage,
    build_notebook_secret_s2_composite,
    build_notebook_secret_s2_layers_image,
    create_ee_notebook_secret_s2_cube_fetcher,
    create_ee_notebook_secret_s2_layer_fetcher,
    compute_hillshade_parameterized,
    compute_secret_chemical_protector,
    compute_secret_gold_halo,
    compute_secret_hidden_doors,
    compute_secret_silver_oxide,
    compute_secret_thermal_inertia,
    compute_secret_tunnel_ceiling,
)
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_secret_layers_stage_emits_all_six_implemented() -> None:
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
        result = asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))

        artifact_names = {a.name for a in result.artifacts}
        assert "AI_READY_640_Secret_Gold_Halo" in artifact_names
        assert "AI_READY_640_Secret_Silver_Oxide" in artifact_names
        assert "AI_READY_640_Secret_Tunnel_Ceiling" in artifact_names
        assert "AI_READY_640_Secret_Thermal_Inertia" in artifact_names
        assert "AI_READY_640_Secret_Chemical_Protector" in artifact_names
        assert "AI_READY_640_Secret_Hidden_Doors" in artifact_names
        assert "secret_layers_manifest" in artifact_names

        metadata = result.metadata
        assert set(metadata["implemented_layers"]) == {
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        }
        assert metadata["not_implemented_layers"] == []

        for layer_name in metadata["implemented_layers"]:
            detail = metadata["layer_details"][layer_name]
            assert detail["status"] == "implemented"
            assert "formula" in detail


def test_secret_layers_manifest_documents_all_six_implemented() -> None:
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

        manifest_path = run_dir / "QA" / "stacks" / "secret_layers_manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "secret_layers_manifest_v1"
        assert manifest["stage"] == "secret_layers"
        assert manifest["layer_count"] == 6
        assert manifest["implemented_count"] == 6
        assert manifest["not_implemented_count"] == 0

        implemented_names = {item["name"] for item in manifest["implemented"]}
        assert implemented_names == {
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        }
        for item in manifest["implemented"]:
            assert item["status"] == "implemented"
            assert "formula" in item
            assert "source_type" in item
            assert "inputs" in item
            assert "output_path" in item
            assert item["output_path"].startswith("AI_READY_640/")

        assert manifest["not_implemented"] == []


def test_implemented_secret_layer_rasters_match_grid_contract() -> None:
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

        for layer_name in (
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        ):
            tif_path = run_dir / "AI_READY_640" / f"{layer_name}.tif"
            assert tif_path.is_file(), f"Missing {tif_path}"
            with rasterio.open(tif_path) as dataset:
                assert dataset.width == grid_spec.size
                assert dataset.height == grid_spec.size
                assert str(dataset.crs) == grid_spec.crs
                assert dataset.count == 1
                assert dataset.dtypes == ("float32",)
                assert float(dataset.nodata) == float(grid_spec.nodata)

            # Verify no absolute paths in tags
            tags_text = json.dumps(dataset.tags())
            assert str(run_dir) not in tags_text
            assert "C:\\" not in tags_text


def test_all_secret_layer_rasters_exist_after_stage() -> None:
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

        for layer_name in (
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
        ):
            tif_path = run_dir / "AI_READY_640" / f"{layer_name}.tif"
            assert tif_path.is_file(), f"Missing secret layer raster: {tif_path}"


def test_hidden_doors_can_use_external_ee_derived_fetcher() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)
        hidden_doors = np.full((grid_spec.size, grid_spec.size), 42.0, dtype=np.float32)
        calls: list[str] = []

        def hidden_doors_fetcher(*, grid_spec):
            calls.append(grid_spec.crs)
            return hidden_doors

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec, hidden_doors_fetcher=hidden_doors_fetcher).run(context))

        with rasterio.open(run_dir / "AI_READY_640" / "AI_READY_640_Secret_Hidden_Doors.tif") as dataset:
            array = dataset.read(1)
            assert np.array_equal(array, hidden_doors)
            assert float(dataset.nodata) == float(grid_spec.nodata)
            assert dataset.width == grid_spec.size
            assert dataset.height == grid_spec.size

        assert calls == [grid_spec.crs]


def test_notebook_secret_s2_composite_uses_notebook_provenance(monkeypatch) -> None:
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

    monkeypatch.setattr("app.pipeline.stages.secret_layers.ee.Filter", FakeFilter)
    monkeypatch.setattr(
        "app.pipeline.stages.secret_layers.ee.ImageCollection",
        lambda dataset: calls.append(("ImageCollection", dataset)) or FakeCollection(),
    )
    monkeypatch.setattr("app.pipeline.stages.secret_layers.build_grid_region", lambda _grid_spec: "grid-region")

    build_notebook_secret_s2_composite(grid_spec)

    assert ("ImageCollection", "COPERNICUS/S2_SR_HARMONIZED") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (NOTEBOOK_SECRET_S2_START, NOTEBOOK_SECRET_S2_END)) in calls
    assert ("filter", ("lt", "CLOUDY_PIXEL_PERCENTAGE", NOTEBOOK_SECRET_S2_CLOUD_MAX)) in calls
    assert ("select", list(NOTEBOOK_SECRET_S2_SOURCE_BANDS)) in calls
    assert ("median", None) in calls


def test_create_ee_notebook_secret_s2_cube_fetcher_uses_sample_rectangle(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-secret-s2-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {band: [[float(index)] * 320 for _ in range(320)] for index, band in enumerate(NOTEBOOK_SECRET_S2_SOURCE_BANDS)}}

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

    monkeypatch.setattr("app.pipeline.stages.secret_layers.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.secret_layers.build_notebook_secret_s2_image", lambda _grid_spec: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.secret_layers.ee.Geometry", FakeGeometry)

    fetcher = create_ee_notebook_secret_s2_cube_fetcher(settings, grid_spec)
    cube = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert cube.shape == (640, 640, len(NOTEBOOK_SECRET_S2_SOURCE_BANDS))
    assert cube.dtype == np.float32
    assert len(rectangle_calls) == 4
    assert np.array_equal(cube[0, 0, :], np.arange(len(NOTEBOOK_SECRET_S2_SOURCE_BANDS), dtype=np.float32))


def test_create_ee_notebook_secret_s2_layer_fetcher_uses_sample_rectangle(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-secret-s2-layer-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    layer_names = (
        "AI_READY_640_Secret_Gold_Halo",
        "AI_READY_640_Secret_Silver_Oxide",
        "AI_READY_640_Secret_Tunnel_Ceiling",
        "AI_READY_640_Secret_Chemical_Protector",
    )

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {name: [[float(index)] * 320 for _ in range(320)] for index, name in enumerate(layer_names)}}

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

    monkeypatch.setattr("app.pipeline.stages.secret_layers.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.secret_layers.build_notebook_secret_s2_layers_image", lambda _grid_spec: FakeImage())
    monkeypatch.setattr("app.pipeline.stages.secret_layers.ee.Geometry", FakeGeometry)

    fetcher = create_ee_notebook_secret_s2_layer_fetcher(settings, grid_spec)
    arrays = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert set(arrays) == set(layer_names)
    assert len(rectangle_calls) == 4
    for index, name in enumerate(layer_names):
        assert arrays[name].shape == (640, 640)
        assert arrays[name].dtype == np.float32
        assert arrays[name][0, 0] == np.float32(index)


def test_notebook_secret_s2_layers_image_builds_ee_formula_stack(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    operations: list[str] = []

    class FakeBand:
        def __init__(self, name):
            self.name = name

        def add(self, value):
            other = value.name if isinstance(value, FakeBand) else value
            operations.append(f"{self.name}.add({other})")
            return FakeBand(f"{self.name}+eps")

        def divide(self, other):
            operations.append(f"{self.name}.divide({other.name})")
            return FakeBand(f"{self.name}/{other.name}")

        def subtract(self, other):
            operations.append(f"{self.name}.subtract({other.name})")
            return FakeBand(f"{self.name}-{other.name}")

        def rename(self, name):
            operations.append(f"{self.name}.rename({name})")
            return FakeBand(name)

    class FakeS2:
        def select(self, name):
            operations.append(f"select({name})")
            return FakeBand(name)

    class FakeLayerImage:
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

    class FakeImage:
        @staticmethod
        def cat(layers):
            operations.append(f"cat({len(layers)})")
            return FakeLayerImage()

        @staticmethod
        def constant(value):
            operations.append(f"constant({value})")
            return FakeBand("eps")

    monkeypatch.setattr("app.pipeline.stages.secret_layers.build_notebook_secret_s2_composite", lambda _grid_spec: FakeS2())
    monkeypatch.setattr("app.pipeline.stages.secret_layers.build_grid_region", lambda _grid_spec: "grid-region")
    monkeypatch.setattr("app.pipeline.stages.secret_layers.ee.Image", FakeImage)

    build_notebook_secret_s2_layers_image(grid_spec)

    assert "constant(1e-06)" in operations
    assert "B12.divide(B8+eps)" in operations
    assert "B2.divide(B1+eps)" in operations
    assert "B8.subtract(B4)" in operations
    assert "B1.divide(B11+eps)" in operations
    assert "cat(4)" in operations
    assert "toFloat" in operations


def test_secret_layers_stage_uses_notebook_s2_fetcher_only_for_s2_layers() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)
        calls: list[str] = []

        notebook_secret_layers = {
            "AI_READY_640_Secret_Gold_Halo": np.full((grid_spec.size, grid_spec.size), 101.0, dtype=np.float32),
            "AI_READY_640_Secret_Silver_Oxide": np.full((grid_spec.size, grid_spec.size), 102.0, dtype=np.float32),
            "AI_READY_640_Secret_Tunnel_Ceiling": np.full((grid_spec.size, grid_spec.size), 103.0, dtype=np.float32),
            "AI_READY_640_Secret_Chemical_Protector": np.full((grid_spec.size, grid_spec.size), 104.0, dtype=np.float32),
        }
        hidden_doors = np.full((grid_spec.size, grid_spec.size), 42.0, dtype=np.float32)

        def secret_s2_layer_fetcher(*, grid_spec):
            calls.append(f"s2:{grid_spec.crs}")
            return notebook_secret_layers

        def hidden_doors_fetcher(*, grid_spec):
            calls.append(f"hidden:{grid_spec.crs}")
            return hidden_doors

        asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(
            SecretLayersStage(
                grid_spec=grid_spec,
                hidden_doors_fetcher=hidden_doors_fetcher,
                secret_s2_layer_fetcher=secret_s2_layer_fetcher,
            ).run(context)
        )

        expected_values = {
            "AI_READY_640_Secret_Gold_Halo": np.float32(101.0),
            "AI_READY_640_Secret_Silver_Oxide": np.float32(102.0),
            "AI_READY_640_Secret_Tunnel_Ceiling": np.float32(103.0),
            "AI_READY_640_Secret_Chemical_Protector": np.float32(104.0),
            "AI_READY_640_Secret_Hidden_Doors": np.float32(42.0),
        }
        for layer_name, expected in expected_values.items():
            with rasterio.open(run_dir / "AI_READY_640" / f"{layer_name}.tif") as dataset:
                assert dataset.read(1)[0, 0] == expected

        manifest = json.loads((run_dir / "QA" / "stacks" / "secret_layers_manifest.json").read_text(encoding="utf-8"))
        provenance = {item["name"]: item["source_provenance"] for item in manifest["implemented"]}
        assert provenance["AI_READY_640_Secret_Gold_Halo"] == "notebook_secret_s2"
        assert provenance["AI_READY_640_Secret_Silver_Oxide"] == "notebook_secret_s2"
        assert provenance["AI_READY_640_Secret_Tunnel_Ceiling"] == "notebook_secret_s2"
        assert provenance["AI_READY_640_Secret_Chemical_Protector"] == "notebook_secret_s2"
        assert provenance["AI_READY_640_Secret_Thermal_Inertia"] == "thermal"
        assert provenance["AI_READY_640_Secret_Hidden_Doors"] == "dem"
        assert calls == [f"s2:{grid_spec.crs}", f"hidden:{grid_spec.crs}"]


def test_gold_halo_formula_matches_notebook() -> None:
    size = 64
    b12 = np.ones((size, size), dtype=np.float32) * 0.5
    b8 = np.ones((size, size), dtype=np.float32) * 0.25
    cube = np.stack([np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)), b8, np.zeros((size, size)), b12], axis=-1)
    result = compute_secret_gold_halo(cube, nodata=-9999.0)
    expected = np.float32(0.5 / (0.25 + 1e-10))
    assert np.allclose(result, expected)


def test_tunnel_ceiling_formula_matches_notebook() -> None:
    size = 64
    b8 = np.ones((size, size), dtype=np.float32) * 0.8
    b4 = np.ones((size, size), dtype=np.float32) * 0.3
    cube = np.stack([np.zeros((size, size)), np.zeros((size, size)), b4, b8, np.zeros((size, size)), np.zeros((size, size))], axis=-1)
    result = compute_secret_tunnel_ceiling(cube, nodata=-9999.0)
    expected = np.float32(0.8 - 0.3)
    assert np.allclose(result, expected)


def test_thermal_inertia_formula_matches_notebook() -> None:
    size = 64
    lst = np.ones((size, size), dtype=np.float32) * 300.0
    result = compute_secret_thermal_inertia(lst, nodata=-9999.0, scale_m=10.0)
    # With uniform input, focal mean equals the input, so ratio is 1.0
    assert np.allclose(result, 1.0)


def test_silver_oxide_formula_matches_notebook() -> None:
    size = 64
    b2 = np.ones((size, size), dtype=np.float32) * 0.4
    b1 = np.ones((size, size), dtype=np.float32) * 0.2
    cube = np.stack([
        b2, np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)), b1
    ], axis=-1)
    result = compute_secret_silver_oxide(cube, nodata=-9999.0)
    expected = np.float32(0.4 / (0.2 + 1e-10))
    assert np.allclose(result, expected)


def test_chemical_protector_formula_matches_notebook() -> None:
    size = 64
    b1 = np.ones((size, size), dtype=np.float32) * 0.2
    b11 = np.ones((size, size), dtype=np.float32) * 0.4
    cube = np.stack([
        np.zeros((size, size)), np.zeros((size, size)), np.zeros((size, size)),
        np.zeros((size, size)), b11, np.zeros((size, size)), b1
    ], axis=-1)
    result = compute_secret_chemical_protector(cube, nodata=-9999.0)
    expected = np.float32(0.2 / (0.4 + 1e-10))
    assert np.allclose(result, expected)


def test_hidden_doors_produces_finite_output() -> None:
    size = 64
    dem = np.linspace(0, 100, size * size, dtype=np.float32).reshape((size, size))
    result = compute_secret_hidden_doors(dem, nodata=-9999.0, scale_m=10.0)
    assert result.shape == (size, size)
    assert np.isfinite(result).all()
    assert (result != -9999.0).all()
    assert float(result.min()) >= -255.0
    assert float(result.max()) <= 255.0


def test_parameterized_hillshade_uses_ee_style_255_scale() -> None:
    size = 32
    dem = np.zeros((size, size), dtype=np.float32)
    result = compute_hillshade_parameterized(
        dem,
        nodata=-9999.0,
        scale_m=10.0,
        azimuth_deg=315.0,
        altitude_deg=35.0,
    )
    expected = np.float32(np.sin(np.deg2rad(35.0)) * 255.0)
    assert np.allclose(result, expected)


def test_secret_layer_specs_cover_all_six_layers() -> None:
    names = {spec["name"] for spec in SECRET_LAYER_SPECS}
    assert names == {
        "AI_READY_640_Secret_Gold_Halo",
        "AI_READY_640_Secret_Silver_Oxide",
        "AI_READY_640_Secret_Tunnel_Ceiling",
        "AI_READY_640_Secret_Thermal_Inertia",
        "AI_READY_640_Secret_Chemical_Protector",
        "AI_READY_640_Secret_Hidden_Doors",
    }


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
