from __future__ import annotations

import asyncio
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from app.errors import StageError
from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import (
    RADAR_BANDS,
    SAR_NPY_ARTIFACT_NAMES,
    SAR_NPY_OUTPUT_DIR,
    NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR,
    NOTEBOOK_SAR_NPY_OUTPUT_DIR,
    NOTEBOOK_SAR_INTERMEDIATE_DIR,
    MAX_ORBIT_DT_DAYS,
    MAX_PAIR_DT_HOURS,
    MAX_PAIRS,
    MIN_PAIRS,
    S1_COLLECTION_ID,
    SAR_SELECTION_PROFILE,
    SarFetchDiagnostics,
    SarPair,
    SarRtcStage,
    SAR_LEE_KERNEL_M,
    SAR_SIGMA_LEE_KERNEL_M,
    SAR_SIGMA_LEE_SIGMA,
    apply_local_dem_rtc,
    build_pair_diagnostics_payload,
    build_final_radar_image,
    build_s1_base_collection,
    create_ee_radar_cube_fetcher,
    deterministic_radar_cube_fetcher,
    per_image_products_db,
    select_pairs,
)
from app.services.storage import read_manifest


def test_apply_local_dem_rtc_builds_expected_bands_and_formula() -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    dem = np.full((grid_spec.size, grid_spec.size), 100.0, dtype=np.float32)
    cube = deterministic_radar_cube_fetcher(grid_spec=grid_spec)

    outputs = apply_local_dem_rtc(
        cube,
        dem,
        nodata=grid_spec.nodata,
        scale_m=float(grid_spec.manifest.scale_m),
    )

    assert set(outputs) == {"VV_dB", "VH_dB", "logRatio_dB", "incidence"}
    assert outputs["VV_dB"].shape == (640, 640)
    assert outputs["incidence"][0, 0] == np.float32(38.5)
    valid = outputs["logRatio_dB"] != grid_spec.nodata
    np.testing.assert_allclose(outputs["logRatio_dB"][valid], outputs["VV_dB"][valid] - outputs["VH_dB"][valid])

    # Flat DEM => corr = 1.0, so notebook local RTC reduces to dividing linear sigma0 by cos(incidence).
    vv_in = float(cube[0, 0, 0])
    cos_inc = float(np.cos(np.deg2rad(cube[0, 0, 2])))
    expected_vv = float(10.0 * np.log10((10.0 ** (vv_in / 10.0)) / cos_inc))
    assert outputs["VV_dB"][0, 0] == pytest.approx(expected_vv, abs=1e-5)


def test_apply_local_dem_rtc_uses_passed_scale_m() -> None:
    dem = np.arange(16, dtype=np.float32).reshape(4, 4)
    cube = np.stack(
        [
            np.full((4, 4), -10.0, dtype=np.float32),
            np.full((4, 4), -16.0, dtype=np.float32),
            np.full((4, 4), 38.5, dtype=np.float32),
        ],
        axis=-1,
    )

    outputs_scale_10 = apply_local_dem_rtc(cube, dem, nodata=-9999.0, scale_m=10.0)
    outputs_scale_20 = apply_local_dem_rtc(cube, dem, nodata=-9999.0, scale_m=20.0)

    assert not np.allclose(outputs_scale_10["VV_dB"], outputs_scale_20["VV_dB"])


def test_apply_local_dem_rtc_valid_mask_matches_cell25_when_angle_is_nodata() -> None:
    nodata = -9999.0
    dem = np.full((4, 4), 100.0, dtype=np.float32)
    cube = np.stack(
        [
            np.full((4, 4), -10.0, dtype=np.float32),
            np.full((4, 4), -16.0, dtype=np.float32),
            np.full((4, 4), 38.5, dtype=np.float32),
        ],
        axis=-1,
    )
    cube[1, 2, 2] = nodata

    outputs = apply_local_dem_rtc(cube, dem, nodata=nodata, scale_m=10.0)

    assert outputs["VV_dB"][1, 2] != nodata
    assert outputs["VH_dB"][1, 2] != nodata
    assert outputs["logRatio_dB"][1, 2] != nodata
    assert outputs["incidence"][1, 2] == nodata


def test_per_image_products_db_applies_notebook_no_cop_dem_filter_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakeBand:
        def __init__(self, label: str):
            self.label = label

        def rename(self, name: str):
            calls.append(("rename", (self.label, name)))
            return FakeBand(f"{self.label}->{name}")

    class FakeImage:
        def __init__(self, label: str):
            self.label = label

        def select(self, bands):
            calls.append(("select", (self.label, bands)))
            if isinstance(bands, str):
                return FakeBand(f"{self.label}.{bands}")
            return FakeImage(f"{self.label}.select")

    class FakeImageFactory:
        def __call__(self, image):
            return FakeImage(f"wrapped:{image}")

        @staticmethod
        def cat(items):
            labels = [item.label for item in items]
            calls.append(("cat", labels))
            return {"labels": labels}

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Image", FakeImageFactory())
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc._border_noise_mask_db",
        lambda image_db: calls.append(("border_mask", image_db.label)) or FakeImage("masked"),
    )
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc._to_linear_from_db",
        lambda band: calls.append(("to_linear", band.label)) or FakeBand(f"lin:{band.label}"),
    )
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc._sigma_lee_filter",
        lambda band, kernel_m, sigma: calls.append(("sigma_lee", (band.label, kernel_m, sigma))) or FakeBand(f"sigma:{band.label}"),
    )
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc._lee_filter",
        lambda band, kernel_m: calls.append(("lee", (band.label, kernel_m))) or FakeBand(f"lee:{band.label}"),
    )
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc._to_db_from_linear",
        lambda band: calls.append(("to_db", band.label)) or FakeBand(f"db:{band.label}"),
    )

    result = per_image_products_db("raw-image")

    assert result["labels"] == [
        "db:lee:sigma:lin:masked.VV->VV_dB",
        "db:lee:sigma:lin:masked.VH->VH_dB",
        "masked.angle->angle",
    ]
    assert ("border_mask", "wrapped:raw-image.select") in calls
    assert ("sigma_lee", ("lin:masked.VV", SAR_SIGMA_LEE_KERNEL_M, SAR_SIGMA_LEE_SIGMA)) in calls
    assert ("sigma_lee", ("lin:masked.VH", SAR_SIGMA_LEE_KERNEL_M, SAR_SIGMA_LEE_SIGMA)) in calls
    assert ("lee", ("sigma:lin:masked.VV", SAR_LEE_KERNEL_M)) in calls
    assert ("lee", ("sigma:lin:masked.VH", SAR_LEE_KERNEL_M)) in calls


def test_build_s1_base_collection_uses_notebook_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            return ("eq", name, value)

        @staticmethod
        def listContains(name, value):
            return ("listContains", name, value)

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

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc.ee.ImageCollection",
        lambda dataset: calls.append(("ImageCollection", dataset)) or FakeCollection(),
    )
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_grid_region", lambda _grid_spec: "grid-region")

    build_s1_base_collection(grid_spec, start_date="2026-01-01", end_date="2026-03-01")

    assert ("ImageCollection", "COPERNICUS/S1_GRD") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", ("2026-01-01", "2026-03-01")) in calls
    assert ("select", ["VV", "VH", "angle"]) in calls


def test_create_ee_radar_cube_fetcher_uses_sample_rectangle(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    settings = _settings(Path("C:/tmp/gee-sar-test"))
    init_calls: list[str] = []
    rectangle_calls: list[tuple[list[float], str, bool]] = []

    class FakeSampleResult:
        def getInfo(self):
            return {"properties": {band: [[1.0] * 320 for _ in range(320)] for band in RADAR_BANDS}}

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

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.initialize_ee_session", lambda _settings: init_calls.append("init"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_final_radar_image", lambda *_args, **_kwargs: (FakeImage(), []))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.finalize_for_sample", lambda image, _grid_spec: image)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Geometry", FakeGeometry)

    fetcher = create_ee_radar_cube_fetcher(settings, grid_spec, start_date="2026-01-01", end_date="2026-03-01")
    cube = fetcher(grid_spec=grid_spec)

    assert init_calls == ["init"]
    assert cube.shape == (640, 640, 3)
    assert cube.dtype == np.float32
    assert len(rectangle_calls) == 4
    assert fetcher.diagnostics.tile_request_count == 4
    assert fetcher.diagnostics.pairs == []


def test_build_final_radar_image_fails_cleanly_for_empty_ascending_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    class FakeNumber:
        def __init__(self, value: int):
            self.value = value

        def getInfo(self) -> int:
            return self.value

    class FakeCollection:
        def __init__(self, direction: str):
            self.direction = direction

        def filter(self, predicate):
            if predicate == ("eq", "orbitProperties_pass", "ASCENDING"):
                return FakeCollection("ASCENDING")
            if predicate == ("eq", "orbitProperties_pass", "DESCENDING"):
                return FakeCollection("DESCENDING")
            return self

        def size(self):
            return FakeNumber(0 if self.direction == "ASCENDING" else 2)

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            return ("eq", name, value)

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_s1_base_collection", lambda *_args, **_kwargs: FakeCollection("BASE"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)

    with pytest.raises(StageError, match="non-empty Sentinel-1 ASCENDING collections"):
        build_final_radar_image(grid_spec, start_date="2026-01-01", end_date="2026-03-01")


def test_build_final_radar_image_fails_cleanly_for_empty_descending_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    class FakeNumber:
        def __init__(self, value: int):
            self.value = value

        def getInfo(self) -> int:
            return self.value

    class FakeFeature:
        def __init__(self, _geometry, properties):
            self.properties = properties

        def get(self, key):
            return self.properties[key]

    class FakeList:
        def __init__(self, values):
            self.values = list(values)

        def distinct(self):
            return self

        def map(self, fn):
            return [fn(value) for value in self.values]

    class FakeCollection:
        def __init__(self, direction: str):
            self.direction = direction

        def filter(self, predicate):
            if predicate == ("eq", "orbitProperties_pass", "ASCENDING"):
                return FakeCollection("ASCENDING")
            if predicate == ("eq", "orbitProperties_pass", "DESCENDING"):
                return FakeCollection("DESCENDING")
            return self

        def size(self):
            return FakeNumber(2 if self.direction == "ASCENDING" else 0)

        def aggregate_array(self, _name):
            return [7]

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            return ("eq", name, value)

    class FakeFeatureCollection:
        def __init__(self, features):
            self.features = list(features)

        def sort(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.features[0]

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_s1_base_collection", lambda *_args, **_kwargs: FakeCollection("BASE"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.List", lambda values: FakeList(values))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Number", lambda value: value if isinstance(value, FakeNumber) else FakeNumber(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Feature", FakeFeature)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.FeatureCollection", FakeFeatureCollection)

    with pytest.raises(StageError, match="non-empty Sentinel-1 DESCENDING collections"):
        build_final_radar_image(grid_spec, start_date="2026-01-01", end_date="2026-03-01")


def test_build_final_radar_image_keeps_stage_error_for_insufficient_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    class FakeNumber:
        def __init__(self, value):
            self.value = value

        def getInfo(self):
            return self.value

    class FakeFeature:
        def __init__(self, _geometry, properties):
            self.properties = properties

        def get(self, key):
            return self.properties[key]

    class FakeList:
        def __init__(self, values):
            self.values = list(values)

        def distinct(self):
            return self

        def map(self, fn):
            return [fn(value) for value in self.values]

    class FakeFeatureCollection:
        def __init__(self, features):
            self.features = list(features)

        def sort(self, _key, _descending=False):
            return self

        def first(self):
            return self.features[0]

    class FakeCollection:
        def __init__(self, direction: str):
            self.direction = direction

        def filter(self, predicate):
            if predicate == ("eq", "orbitProperties_pass", "ASCENDING"):
                return FakeCollection("ASCENDING")
            if predicate == ("eq", "orbitProperties_pass", "DESCENDING"):
                return FakeCollection("DESCENDING")
            return self

        def size(self):
            return FakeNumber(2)

        def aggregate_array(self, _name):
            return [7]

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            return ("eq", name, value)

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.build_s1_base_collection", lambda *_args, **_kwargs: FakeCollection("BASE"))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.fc_time_ids", lambda _collection: [{"ms": 1000, "id": "ONLY_ONE"}])
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.List", lambda values: FakeList(values))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Number", lambda value: value if isinstance(value, FakeNumber) else FakeNumber(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Feature", FakeFeature)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.FeatureCollection", FakeFeatureCollection)

    with pytest.raises(StageError, match="Not enough ASC/DESC SAR pairs"):
        build_final_radar_image(grid_spec, start_date="2026-01-01", end_date="2026-03-01")


def test_select_pairs_uses_cell25_pixel_export_profile_not_cell21_master_units() -> None:
    asc_items = [
        _sar_item("S1C_IW_GRDH_1SDV_20260118T153231_20260118T153256_005960_00BF44_900B", "2026-01-18T15:32:31"),
        _sar_item("S1A_IW_GRDH_1SDV_20260124T153322_20260124T153347_062911_07E445_5A03", "2026-01-24T15:33:22"),
        _sar_item("S1A_IW_GRDH_1SDV_20260124T153347_20260124T153412_062911_07E445_CC8F", "2026-01-24T15:33:47"),
        _sar_item("S1C_IW_GRDH_1SDV_20260130T153231_20260130T153256_006135_00C4FC_B136", "2026-01-30T15:32:31"),
        _sar_item("APP_ONLY_20260205_ASC", "2026-02-05T15:32:31"),
        _sar_item("APP_ONLY_20260206_ASC", "2026-02-06T15:32:31"),
    ]
    desc_items = [
        _sar_item("S1A_IW_GRDH_1SDV_20260118T034301_20260118T034326_062816_07E10A_BAF5", "2026-01-18T05:32:31"),
        _sar_item("S1C_IW_GRDH_1SDV_20260124T034219_20260124T034244_006040_00C1BF_D131", "2026-01-24T04:33:22"),
        _sar_item("S1C_IW_GRDH_1SDV_20260124T034154_20260124T034219_006040_00C1BF_56CA", "2026-01-24T03:33:47"),
        _sar_item("S1A_IW_GRDH_1SDV_20260130T034301_20260130T034326_062991_07E753_7321", "2026-01-30T05:32:31"),
        _sar_item("APP_ONLY_20260205_DESC", "2026-02-05T05:32:31"),
        _sar_item("APP_ONLY_20260206_DESC", "2026-02-06T05:32:31"),
    ]

    selected = select_pairs(asc_items, desc_items)

    assert MAX_ORBIT_DT_DAYS == 9
    assert MAX_PAIR_DT_HOURS == 36
    assert MAX_PAIRS == 4
    assert MIN_PAIRS == 2
    assert [pair.asc_id for pair in selected] == [
        "S1C_IW_GRDH_1SDV_20260130T153231_20260130T153256_006135_00C4FC_B136",
        "APP_ONLY_20260205_ASC",
        "S1A_IW_GRDH_1SDV_20260124T153322_20260124T153347_062911_07E445_5A03",
        "S1A_IW_GRDH_1SDV_20260124T153347_20260124T153412_062911_07E445_CC8F",
    ]
    assert all("20260118" not in pair.asc_id for pair in selected)


def test_select_pairs_uses_36_hour_pair_cap() -> None:
    asc_items = [_sar_item("ASC_42H", "2026-01-24T12:00:00")]
    desc_items = [_sar_item("DESC_42H", "2026-01-22T18:00:00")]

    selected = select_pairs(asc_items, desc_items, min_pairs=0)
    cell21_profile_selected = select_pairs(asc_items, desc_items, max_pair_dt_hours=48, min_pairs=1)

    assert [(pair.asc_id, pair.desc_id) for pair in selected] == []
    assert [(pair.asc_id, pair.desc_id) for pair in cell21_profile_selected] == [("ASC_42H", "DESC_42H")]


def test_sar_rtc_stage_writes_classified_grid_aligned_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)
        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))

        result = asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "VV_dB",
            "VH_dB",
            "logRatio_dB",
            "incidence",
            "notebook_RADAR_VV_dB_640",
            "notebook_RADAR_VH_dB_640",
            "notebook_RADAR_logRatio_dB_640",
            "notebook_RADAR_angle_640",
            "sar_npy_VV_dB",
            "sar_npy_VH_dB",
            "sar_npy_logRatio_dB",
            "sar_npy_incidence",
            "notebook_sar_npy_RADAR_VV_dB_640",
            "notebook_sar_npy_RADAR_VH_dB_640",
            "notebook_sar_npy_RADAR_logRatio_dB_640",
            "notebook_sar_npy_RADAR_angle_640",
            "notebook_sar_intermediate_manifest",
            "notebook_sar_intermediate_post_rtc_VV_dB",
            "notebook_sar_intermediate_post_rtc_VH_dB",
            "notebook_sar_intermediate_post_rtc_logRatio_dB",
            "notebook_sar_intermediate_post_rtc_angle",
            "sar_pair_diagnostics",
            "sar_summary",
            "sar_nodata_audit",
            "sar_alignment_summary",
        ]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "VV_dB": ArtifactClass.LOCAL_SENSITIVE,
            "VH_dB": ArtifactClass.LOCAL_SENSITIVE,
            "logRatio_dB": ArtifactClass.LOCAL_SENSITIVE,
            "incidence": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_RADAR_VV_dB_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_RADAR_VH_dB_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_RADAR_logRatio_dB_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_RADAR_angle_640": ArtifactClass.LOCAL_SENSITIVE,
            "sar_npy_VV_dB": ArtifactClass.FILESYSTEM_ONLY,
            "sar_npy_VH_dB": ArtifactClass.FILESYSTEM_ONLY,
            "sar_npy_logRatio_dB": ArtifactClass.FILESYSTEM_ONLY,
            "sar_npy_incidence": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_npy_RADAR_VV_dB_640": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_npy_RADAR_VH_dB_640": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_npy_RADAR_logRatio_dB_640": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_npy_RADAR_angle_640": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_intermediate_manifest": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_intermediate_post_rtc_VV_dB": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_intermediate_post_rtc_VH_dB": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_intermediate_post_rtc_logRatio_dB": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_sar_intermediate_post_rtc_angle": ArtifactClass.FILESYSTEM_ONLY,
            "sar_pair_diagnostics": ArtifactClass.FILESYSTEM_ONLY,
            "sar_summary": ArtifactClass.FILESYSTEM_ONLY,
            "sar_nodata_audit": ArtifactClass.FILESYSTEM_ONLY,
            "sar_alignment_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        artifact_http_flags = {artifact.name: artifact.http_servable for artifact in result.artifacts}
        for artifact_name in SAR_NPY_ARTIFACT_NAMES.values():
            assert artifact_http_flags[artifact_name] is False
        for artifact_name in (
            "notebook_sar_npy_RADAR_VV_dB_640",
            "notebook_sar_npy_RADAR_VH_dB_640",
            "notebook_sar_npy_RADAR_logRatio_dB_640",
            "notebook_sar_npy_RADAR_angle_640",
            "notebook_sar_intermediate_manifest",
            "notebook_sar_intermediate_post_rtc_VV_dB",
            "notebook_sar_intermediate_post_rtc_VH_dB",
            "notebook_sar_intermediate_post_rtc_logRatio_dB",
            "notebook_sar_intermediate_post_rtc_angle",
        ):
            assert artifact_http_flags[artifact_name] is False
        assert artifact_http_flags["sar_pair_diagnostics"] is False
        assert artifact_http_flags["sar_summary"] is False
        assert artifact_http_flags["sar_nodata_audit"] is False
        assert artifact_http_flags["sar_alignment_summary"] is False
        assert {
            artifact.relative_path
            for artifact in result.artifacts
            if artifact.name in {"sar_pair_diagnostics", "sar_summary", "sar_nodata_audit", "sar_alignment_summary"}
        } == {
            "QA/sar/sar_pair_diagnostics.json",
            "QA/sar/sar_summary.csv",
            "QA/sar/sar_nodata_audit.csv",
            "QA/sar/sar_alignment_summary.json",
        }
        assert result.metadata["band_names"] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]
        assert result.metadata["sar_npy_artifact_names"] == [
            "sar_npy_VV_dB",
            "sar_npy_VH_dB",
            "sar_npy_logRatio_dB",
            "sar_npy_incidence",
        ]
        assert result.metadata["qa_artifact_names"] == [
            "sar_pair_diagnostics",
            "sar_summary",
            "sar_nodata_audit",
            "sar_alignment_summary",
        ]

        for name in ("VV_dB", "VH_dB", "logRatio_dB", "incidence"):
            sidecar = read_manifest(raster_sidecar_path(run_dir / f"{name}.tif"))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform
            npy_path = run_dir / SAR_NPY_OUTPUT_DIR / f"{name}.npy"
            assert npy_path.is_file()
            npy_array = np.load(npy_path)
            assert npy_array.dtype == np.float32
            assert npy_array.shape == (640, 640)

        expected_notebook_tifs = {
            "RADAR_VV_dB_640_app.tif",
            "RADAR_VH_dB_640_app.tif",
            "RADAR_logRatio_dB_640_app.tif",
            "RADAR_angle_640_app.tif",
        }
        notebook_tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
        assert {path.name for path in notebook_tif_dir.glob("*.tif")} == expected_notebook_tifs
        for filename in expected_notebook_tifs:
            sidecar = read_manifest(raster_sidecar_path(notebook_tif_dir / filename))
            assert sidecar["transform"] == grid_spec.manifest.crs_transform
            assert sidecar["height"] == 640
            assert sidecar["width"] == 640
            assert sidecar["dtype"] == "float32"

        expected_notebook_npys = {
            "RADAR_VV_dB_640_app.npy",
            "RADAR_VH_dB_640_app.npy",
            "RADAR_logRatio_dB_640_app.npy",
            "RADAR_angle_640_app.npy",
        }
        notebook_npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
        assert expected_notebook_npys <= {path.name for path in notebook_npy_dir.glob("*.npy")}
        for filename in expected_notebook_npys:
            array = np.load(notebook_npy_dir / filename)
            assert array.dtype == np.float32
            assert array.shape == (640, 640)

        intermediate_dir = run_dir / NOTEBOOK_SAR_INTERMEDIATE_DIR
        assert NOTEBOOK_SAR_INTERMEDIATE_DIR.startswith("QA/")
        assert all(
            artifact.relative_path.startswith("QA/sar/intermediates/")
            for artifact in result.artifacts
            if artifact.name.startswith("notebook_sar_intermediate")
        )
        intermediate_manifest = json.loads((intermediate_dir / "sar_intermediate_manifest.json").read_text(encoding="utf-8"))
        assert intermediate_manifest["schema"] == "notebook_sar_intermediates_v1"
        assert intermediate_manifest["stages"]["per_image_products_db"]["status"] == "not_implemented_no_source_equivalent"
        assert intermediate_manifest["stages"]["pair_median"]["status"] == "not_implemented_no_source_equivalent"
        assert intermediate_manifest["stages"]["final_median_pre_rtc"]["status"] == "not_implemented_no_source_equivalent"
        assert intermediate_manifest["stages"]["post_sample_pre_rtc"]["status"] == "not_implemented_no_source_equivalent"
        assert intermediate_manifest["stages"]["post_rtc"]["status"] == "implemented"
        assert intermediate_manifest["stages"]["post_rtc"]["bands"] == {
            "VV_dB": "post_rtc/final_VV_dB.npy",
            "VH_dB": "post_rtc/final_VH_dB.npy",
            "logRatio_dB": "post_rtc/final_logRatio_dB.npy",
            "angle": "post_rtc/final_angle.npy",
        }
        assert intermediate_manifest["stages"]["post_rtc"]["source_mapping"] == {
            "post_rtc/final_VV_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/VV_dB.npy",
            "post_rtc/final_VH_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/VH_dB.npy",
            "post_rtc/final_logRatio_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/logRatio_dB.npy",
            "post_rtc/final_angle.npy": f"{SAR_NPY_OUTPUT_DIR}/incidence.npy",
        }
        assert isinstance(intermediate_manifest["stages"]["post_rtc"]["source_description"], str)
        serialized_intermediate_manifest = json.dumps(intermediate_manifest, sort_keys=True)
        assert "bounds" not in serialized_intermediate_manifest
        assert "transform" not in serialized_intermediate_manifest
        assert "C:\\" not in serialized_intermediate_manifest
        post_rtc_filenames_to_source = {
            "final_VV_dB.npy": "VV_dB.npy",
            "final_VH_dB.npy": "VH_dB.npy",
            "final_logRatio_dB.npy": "logRatio_dB.npy",
            "final_angle.npy": "incidence.npy",
        }
        for filename, source_filename in post_rtc_filenames_to_source.items():
            intermediate_path = intermediate_dir / "post_rtc" / filename
            assert intermediate_path.is_file()
            intermediate_array = np.load(intermediate_path)
            source_array = np.load(run_dir / SAR_NPY_OUTPUT_DIR / source_filename)
            assert intermediate_array.dtype == np.float32
            assert intermediate_array.shape == (640, 640)
            np.testing.assert_array_equal(intermediate_array, source_array)

        pair_diagnostics = json.loads((run_dir / "QA" / "sar" / "sar_pair_diagnostics.json").read_text(encoding="utf-8"))
        assert pair_diagnostics["artifact_class"] == "FILESYSTEM_ONLY"
        assert pair_diagnostics["local_only"] is True
        assert pair_diagnostics["collection_id"] == S1_COLLECTION_ID
        assert pair_diagnostics["source_filters"]["selection_profile"] == SAR_SELECTION_PROFILE
        assert pair_diagnostics["source_filters"]["selection_profile"] == "cell25_pixel_export"
        assert pair_diagnostics["source_filters"]["pixel_output_source_cell"] == "Cell 25"
        assert pair_diagnostics["source_filters"]["auxiliary_master_units_profile"] == "cell21_master_units_qa_auxiliary"
        assert pair_diagnostics["source_filters"]["max_orbit_dt_days"] == 9
        assert pair_diagnostics["source_filters"]["max_pair_dt_hours"] == 36
        assert pair_diagnostics["source_filters"]["max_pairs"] == 4
        assert pair_diagnostics["selected_band_list"] == ["VV", "VH", "angle"]
        assert pair_diagnostics["sampled_band_list"] == ["VV_dB", "VH_dB", "angle"]
        assert pair_diagnostics["output_band_list"] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]
        assert pair_diagnostics["angle_incidence_mapping"]["notebook_band"] == "angle"
        assert pair_diagnostics["angle_incidence_mapping"]["app_output_band"] == "incidence"
        assert pair_diagnostics["processing_path"]["local_dem_rtc"] is True
        assert pair_diagnostics["processing_path"]["speckle_sigma_lee_filtering"] is True
        assert pair_diagnostics["processing_path"]["speckle_lee_filtering"] is True
        assert pair_diagnostics["processing_path"]["speckle_refined_lee_filtering"] is False
        assert pair_diagnostics["processing_path"]["border_noise_mask_db"] is True
        assert pair_diagnostics["processing_path"]["db_to_linear_to_db"] is True
        assert pair_diagnostics["pair_diagnostics_available"] is False
        assert pair_diagnostics["pair_count"] == 0
        assert "bounds" not in pair_diagnostics
        assert "transform" not in pair_diagnostics

        with (run_dir / "QA" / "sar" / "sar_summary.csv").open("r", encoding="utf-8", newline="") as handle:
            summary_rows = list(csv.DictReader(handle))
        assert [row["band_name"] for row in summary_rows] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]
        assert all("mean" in row for row in summary_rows)

        with (run_dir / "QA" / "sar" / "sar_nodata_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            nodata_rows = list(csv.DictReader(handle))
        assert [row["band_name"] for row in nodata_rows] == ["VV_dB", "VH_dB", "logRatio_dB", "incidence"]
        assert all(set(row) == {"band_name", "total_pixels", "nodata_count", "nodata_fraction", "all_nodata"} for row in nodata_rows)

        alignment_summary = json.loads((run_dir / "QA" / "sar" / "sar_alignment_summary.json").read_text(encoding="utf-8"))
        assert alignment_summary["all_shapes_match"] is True
        assert alignment_summary["all_float32"] is True
        assert alignment_summary["expected_shape"] == [640, 640]
        assert "crs_transform" not in alignment_summary


def test_pair_diagnostics_payload_records_source_selection_without_public_grid_leakage() -> None:
    payload = build_pair_diagnostics_payload(
        start_date="2026-01-01",
        end_date="2026-03-01",
        diagnostics=SarFetchDiagnostics(
            pairs=[SarPair(asc_id="ASC_1", desc_id="DESC_1", dt_ms=3_600_000, asc_ms=1_704_067_200_000, desc_ms=1_704_070_800_000)],
            tile_request_count=4,
        ),
    )

    assert payload["collection_id"] == S1_COLLECTION_ID
    assert payload["date_window"] == {"start_date": "2026-01-01", "end_date": "2026-03-01"}
    assert payload["source_filters"]["orbit_directions"] == ["ASCENDING", "DESCENDING"]
    assert payload["pairs"] == [
        {
            "asc_id": "ASC_1",
            "desc_id": "DESC_1",
            "asc_date": "2024-01-01",
            "desc_date": "2024-01-01",
            "dt_hours": 1.0,
        }
    ]
    serialized = json.dumps(payload, sort_keys=True)
    assert "bounds" not in serialized
    assert "transform" not in serialized
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")


def _sar_item(image_id: str, iso_timestamp: str) -> dict[str, object]:
    timestamp = datetime.fromisoformat(iso_timestamp).replace(tzinfo=UTC)
    return {"id": image_id, "ms": int(timestamp.timestamp() * 1000)}
