from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio
from affine import Affine

from app.pipeline._base import StageContext
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.field_ops_exports import FieldOpsExportsStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.gps_compare import GpsComparisonStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.report_640 import Report640Stage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import read_manifest


def test_notebook_compatible_raster_metadata_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = _build_full_deterministic_run(run_dir)

        expected_band_counts = {
            "DEM_GEO8_TIFS/DEM_640.tif": 1,
            "DEM_GEO8_TIFS/slope_deg_640.tif": 1,
            "DEM_GEO8_TIFS/aspect_deg_640.tif": 1,
            "DEM_GEO8_TIFS/roughness_100m_640.tif": 1,
            "DEM_GEO8_TIFS/tpi_100m_640.tif": 1,
            "DEM_GEO8_TIFS/hillshade_0to1_640.tif": 1,
            "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif": 1,
            "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif": 1,
            "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif": 1,
            "GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif": 1,
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif": 9,
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif": 13,
            "QA/QA_GRID_dx_m_640.tif": 1,
            "QA/QA_GRID_dy_m_640.tif": 1,
            "QA/QA_GRID_validmask_640.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Gold_Halo.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Silver_Oxide.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Tunnel_Ceiling.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Thermal_Inertia.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Chemical_Protector.tif": 1,
            "AI_READY_640/AI_READY_640_Secret_Hidden_Doors.tif": 1,
            "REPORT_640_Pottery_Report.tif": 1,
            "REPORT_640_Mass_Report.tif": 1,
            "REPORT_640_FINAL_Zero_Point_Targets.tif": 1,
        }

        for relative_path, expected_count in expected_band_counts.items():
            path = run_dir / relative_path
            sidecar = read_manifest(raster_sidecar_path(path))
            with rasterio.open(path) as dataset:
                assert dataset.width == grid_spec.size
                assert dataset.height == grid_spec.size
                assert str(dataset.crs) == grid_spec.crs
                assert dataset.transform != Affine.identity()
                assert [float(value) for value in dataset.transform][:6] == [float(value) for value in sidecar["transform"]]
                assert dataset.count == expected_count
                assert dataset.dtypes == ("float32",) * expected_count
                assert float(dataset.nodata) == float(grid_spec.nodata)
                tags_text = json.dumps(
                    {
                        "dataset": dataset.tags(),
                        "bands": {str(index): dataset.tags(index) for index in range(1, dataset.count + 1)},
                    },
                    sort_keys=True,
                )
            assert sidecar["width"] == grid_spec.size
            assert sidecar["height"] == grid_spec.size
            assert sidecar["crs"] == grid_spec.crs
            assert sidecar["dtype"] == "float32"
            assert float(sidecar["nodata"]) == float(grid_spec.nodata)
            _assert_no_sensitive_text(tags_text, run_dir)
            _assert_no_sensitive_text(path.read_bytes()[:64].decode("latin-1", errors="ignore"), run_dir)


def test_notebook_compatible_npy_metadata_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = _build_full_deterministic_run(run_dir)

        radar_stack = np.load(run_dir / "NPY_STACKS" / "RADAR_STACK_HWC_640_app.npy")
        assert radar_stack.dtype == np.float32
        assert radar_stack.shape == (grid_spec.size, grid_spec.size, 4)
        assert radar_stack.dtype != object
        assert np.isfinite(radar_stack).all()

        final_tesla = np.load(run_dir / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.npy")
        assert final_tesla.dtype == np.float32
        assert final_tesla.shape == (9, grid_spec.size, grid_spec.size)
        assert final_tesla.dtype != object
        assert np.isfinite(final_tesla).all()

        notebook_band_paths = {
            "NPY_RADAR_BANDS/RADAR_angle_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy",
        }
        observed_files = {path.relative_to(run_dir).as_posix() for path in run_dir.rglob("*") if path.is_file()}
        assert not any(path.startswith("qa/") for path in observed_files)

        for relative_path in notebook_band_paths:
            assert (run_dir / relative_path).is_file(), relative_path
            array = np.load(run_dir / relative_path)
            assert array.dtype == np.float32
            assert array.shape == (grid_spec.size, grid_spec.size)
            assert array.dtype != object
            assert np.isfinite(array).all()


def test_notebook_compatible_csv_and_json_schema_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_full_deterministic_run(run_dir)

        run_manifest_text = (run_dir / "QA" / "RUN_MANIFEST.json").read_text(encoding="utf-8")
        run_manifest = json.loads(run_manifest_text)
        assert run_manifest["schema"] == "notebook_compatible_run_manifest_v1"
        assert set(run_manifest) == {"schema", "run_id", "grid", "output_groups", "qa_grid_outputs"}
        assert set(run_manifest["grid"]) == {"crs", "epsg", "scale_m", "out_size", "nodata"}
        assert run_manifest["output_groups"] == [
            "DEM_GEO8_TIFS",
            "GEOTIFF_RADAR_BANDS",
            "NPY_RADAR_BANDS",
            "NPY_STACKS",
            "QA",
        ]
        assert run_manifest["qa_grid_outputs"] == [
            "QA_GRID_dx_m_640.tif",
            "QA_GRID_dy_m_640.tif",
            "QA_GRID_validmask_640.tif",
        ]
        _assert_no_sensitive_text(run_manifest_text, run_dir)

        report_manifest_text = (run_dir / "QA" / "REPORT_640_manifest.json").read_text(encoding="utf-8")
        report_manifest = json.loads(report_manifest_text)
        assert report_manifest["schema"] == "notebook_report_640_manifest_v1"
        assert report_manifest["stage"] == "report_640"
        assert set(report_manifest["reports"]) == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }
        assert report_manifest["reports"]["REPORT_640_Pottery_Report.tif"]["status"] == "implemented"
        assert report_manifest["reports"]["REPORT_640_FINAL_Zero_Point_Targets.tif"]["status"] == "implemented"
        mass_report = report_manifest["reports"]["REPORT_640_Mass_Report.tif"]
        assert mass_report["status"] == "implemented"
        assert mass_report["formula"] == "B12 * ST_B10 / 1000"
        assert "s2_raw_cube.npy" in mass_report["source_equivalent"]
        assert "st_b10_raw.npy" in mass_report["source_equivalent"]
        _assert_no_sensitive_text(report_manifest_text, run_dir)

        intermediate_manifest_text = (run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json").read_text(
            encoding="utf-8"
        )
        intermediate_manifest = json.loads(intermediate_manifest_text)
        assert intermediate_manifest["schema"] == "notebook_sar_intermediates_v1"
        assert intermediate_manifest["stage"] == "sar_rtc"
        assert intermediate_manifest["local_only"] is True
        missing_stage_names = {
            "per_image_products_db",
            "pair_median",
            "final_median_pre_rtc",
            "post_sample_pre_rtc",
        }
        assert missing_stage_names <= set(intermediate_manifest["stages"])
        for name in missing_stage_names:
            item = intermediate_manifest["stages"][name]
            assert set(item) == {"status", "items", "missing_reason"}
            assert item["status"] == "not_implemented_no_source_equivalent"
            assert item["items"] == []
            assert isinstance(item["missing_reason"], str) and item["missing_reason"]
        post_rtc = intermediate_manifest["stages"]["post_rtc"]
        assert set(post_rtc) == {"status", "bands", "source_mapping", "source_description"}
        assert post_rtc["status"] == "implemented"
        assert set(post_rtc["bands"]) == {"VV_dB", "VH_dB", "logRatio_dB", "angle"}
        assert set(post_rtc["source_mapping"]) == {
            "post_rtc/final_VV_dB.npy",
            "post_rtc/final_VH_dB.npy",
            "post_rtc/final_logRatio_dB.npy",
            "post_rtc/final_angle.npy",
        }
        assert isinstance(post_rtc["source_description"], str) and post_rtc["source_description"]
        _assert_no_sensitive_text(intermediate_manifest_text, run_dir)

        with (run_dir / "objects_index.csv").open("r", encoding="utf-8", newline="") as handle:
            object_rows = list(csv.DictReader(handle))
        assert object_rows
        assert set(object_rows[0]) == {
            "object_id",
            "cluster_id",
            "row_min",
            "row_max",
            "col_min",
            "col_max",
            "row_center",
            "col_center",
            "area_px",
            "mean_anomaly",
            "max_anomaly",
        }
        _assert_no_sensitive_text((run_dir / "objects_index.csv").read_text(encoding="utf-8"), run_dir)

        with (run_dir / "clusters_summary.csv").open("r", encoding="utf-8", newline="") as handle:
            cluster_rows = list(csv.DictReader(handle))
        assert cluster_rows
        assert set(cluster_rows[0]) == {
            "cluster_id",
            "object_count",
            "total_area_px",
            "mean_object_area_px",
            "max_object_anomaly",
        }
        _assert_no_sensitive_text((run_dir / "clusters_summary.csv").read_text(encoding="utf-8"), run_dir)

        alignment_summary_text = (run_dir / "alignment_qa.json").read_text(encoding="utf-8")
        alignment_summary = json.loads(alignment_summary_text)
        assert set(alignment_summary) == {"pass", "checked_raster_count", "failing_artifacts", "max_center_offset_px", "threshold_px"}
        _assert_no_sensitive_text(alignment_summary_text, run_dir)

        with (run_dir / "alignment_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            audit_rows = list(csv.DictReader(handle))
        assert audit_rows
        assert set(audit_rows[0]) == {
            "artifact_name",
            "dtype",
            "height",
            "width",
            "valid_fraction",
            "edge_valid_fraction",
            "center_offset_px",
            "passes_alignment",
        }
        _assert_no_sensitive_text((run_dir / "alignment_audit.csv").read_text(encoding="utf-8"), run_dir)

        mask_selection_text = (run_dir / "alignment_mask_selection.json").read_text(encoding="utf-8")
        mask_selection = json.loads(mask_selection_text)
        assert set(mask_selection) == {"anchor_artifact", "anchor_valid_fraction", "selection_rule"}
        _assert_no_sensitive_text(mask_selection_text, run_dir)


def _build_full_deterministic_run(run_dir: Path):
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))
    asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
    asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
    asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
    asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
    asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
    asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))
    asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))
    asyncio.run(FocusMaskStage(grid_spec=grid_spec).run(context))
    asyncio.run(LocationExportsStage(grid_spec=grid_spec).run(context))
    asyncio.run(FieldOpsExportsStage(grid_spec=grid_spec).run(context))
    asyncio.run(GpsComparisonStage(input_lat=35.59499, input_lon=36.12694, grid_spec=grid_spec).run(context))
    asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))
    asyncio.run(PcaAnomalyStage(grid_spec=grid_spec).run(context))
    asyncio.run(ObjectExtractStage(grid_spec=grid_spec).run(context))
    asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))
    return grid_spec


def _assert_no_sensitive_text(text: str, run_dir: Path) -> None:
    for forbidden in (
        ".env",
        "PATH_MAP.local.json",
        "service-account",
        "service_account",
        "traceback",
        str(run_dir),
        "C:\\",
    ):
        assert forbidden not in text


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
