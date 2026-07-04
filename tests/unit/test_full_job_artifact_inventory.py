from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.classifier import ClassifierStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import OUTPUT_NAMES as DEM_DERIVATIVE_NAMES, DemDerivativesStage
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
from app.pipeline.stages.s2_indices import INDEX_NAMES, S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SAR_NPY_OUTPUT_DIR, SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage


def test_full_job_artifact_families_are_emitted_by_owner_stages() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        grid_result = asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        dem_result = asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        zero_shift_result = asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))
        sar_result = asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        s2_result = asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        dem_derivatives_result = asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        thermal_result = asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        secret_layers_result = asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        report_640_result = asyncio.run(Report640Stage(grid_spec=grid_spec).run(context))
        feature_stacks_result = asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))
        focus_mask_result = asyncio.run(FocusMaskStage(grid_spec=grid_spec).run(context))
        location_exports_result = asyncio.run(LocationExportsStage(grid_spec=grid_spec).run(context))
        field_ops_result = asyncio.run(FieldOpsExportsStage(grid_spec=grid_spec).run(context))
        gps_compare_result = asyncio.run(GpsComparisonStage(input_lat=35.59499, input_lon=36.12694, grid_spec=grid_spec).run(context))
        hypercube_result = asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))
        pca_result = asyncio.run(PcaAnomalyStage(grid_spec=grid_spec).run(context))
        object_result = asyncio.run(ObjectExtractStage(grid_spec=grid_spec).run(context))
        classifier_result = asyncio.run(ClassifierStage().run(context))
        alignment_result = asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))

        assert _artifact_classes(grid_result) == {
            "grid_manifest": ArtifactClass.LOCAL_SENSITIVE,
            "grid_guard_summary": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_QA_GRID_dx_m_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_QA_GRID_dy_m_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_QA_GRID_validmask_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_RUN_MANIFEST": ArtifactClass.LOCAL_SENSITIVE,
        }
        assert _artifact_classes(dem_result) == {
            "dem_tif": ArtifactClass.LOCAL_SENSITIVE,
            "dem_npy": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_dem_640_tif": ArtifactClass.LOCAL_SENSITIVE,
            "dem_audit_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(zero_shift_result) == {
            "zero_shift_summary": ArtifactClass.FILESYSTEM_ONLY,
            "drift_audit": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(sar_result) == {
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
        assert _artifact_classes(s2_result) == {
            **{name: ArtifactClass.LOCAL_SENSITIVE for name in INDEX_NAMES},
            "s2_raw_valid_mask_640": ArtifactClass.FILESYSTEM_ONLY,
            "s2_index_valid_mask_640": ArtifactClass.FILESYSTEM_ONLY,
            "s2_dem_matched_masks_manifest": ArtifactClass.FILESYSTEM_ONLY,
            "s2_indices_summary": ArtifactClass.FILESYSTEM_ONLY,
            "s2_raw_cube": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_REPORT_640_FINAL_INTELLIGENCE_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_TESLA_V7_2_ATOMIC_INFERENCE_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "aix_extra_tensors_stack_alias_manifest": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(dem_derivatives_result) == {
            **{name: ArtifactClass.LOCAL_SENSITIVE for name in DEM_DERIVATIVE_NAMES},
            "notebook_DEM_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_slope_deg_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_aspect_deg_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_roughness_100m_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_tpi_100m_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_hillshade_0to1_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_curv_laplacian_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_curv_plan_640": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_curv_profile_640": ArtifactClass.LOCAL_SENSITIVE,
            "dem_derivatives_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(thermal_result) == {
            "lst": ArtifactClass.LOCAL_SENSITIVE,
            "thermal_summary": ArtifactClass.FILESYSTEM_ONLY,
            "st_b10_raw": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(secret_layers_result) == {
            "AI_READY_640_Secret_Gold_Halo": ArtifactClass.LOCAL_SENSITIVE,
            "AI_READY_640_Secret_Silver_Oxide": ArtifactClass.LOCAL_SENSITIVE,
            "AI_READY_640_Secret_Tunnel_Ceiling": ArtifactClass.LOCAL_SENSITIVE,
            "AI_READY_640_Secret_Thermal_Inertia": ArtifactClass.LOCAL_SENSITIVE,
            "AI_READY_640_Secret_Chemical_Protector": ArtifactClass.LOCAL_SENSITIVE,
            "AI_READY_640_Secret_Hidden_Doors": ArtifactClass.LOCAL_SENSITIVE,
            "secret_layers_manifest": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(report_640_result) == {
            "REPORT_640_Pottery_Report": ArtifactClass.LOCAL_SENSITIVE,
            "REPORT_640_Mass_Report": ArtifactClass.LOCAL_SENSITIVE,
            "REPORT_640_FINAL_Zero_Point_Targets": ArtifactClass.LOCAL_SENSITIVE,
            "REPORT_640_manifest": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(feature_stacks_result) == {
            "science_core_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "science_core_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "radar_linear_support_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "radar_linear_support_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "radar_db_support_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "radar_db_support_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "ai_ready_support_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "ai_ready_support_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "s2_mask_support_valid": ArtifactClass.FILESYSTEM_ONLY,
            "band_stats": ArtifactClass.FILESYSTEM_ONLY,
            "stack_presence_summary": ArtifactClass.FILESYSTEM_ONLY,
            "tensor_audit_summary": ArtifactClass.FILESYSTEM_ONLY,
            "geometry_consistency_summary": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_RADAR_STACK_HWC_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_SCIENCE_CORE_STACK_HWC_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_RADAR_LINEAR_SUPPORT_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_AI_READY_SUPPORT_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_RAD_S0_MASTER_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_RAD_MASTER_CUBE_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_GPHYS_MASTER_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_MASTER_RTC_REFINED_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_ARCH_TARGETS_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_ULTIMATE_GPHYS_SCAN_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_AUX_BONUS_FEATURES_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_SIM_GEOPHYSICAL_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_NANO_GEOPHYSICS_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_TREASURE_GEOPHYSICS_STACK_640_npy": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_stack_alias_manifest": ArtifactClass.FILESYSTEM_ONLY,
        }
        focus_classes = _artifact_classes(focus_mask_result)
        assert {
            "focus_zone_17m_tif",
            "focus_zone_17m_npy",
            "focus_zone_ai_ready_window",
            "focus_zone_summary",
            "focus_band_summary",
        } <= set(focus_classes)
        assert all(
            artifact_class == ArtifactClass.FILESYSTEM_ONLY
            for artifact_class in focus_classes.values()
        )
        assert _artifact_classes(location_exports_result) == {
            "location_geojson": ArtifactClass.FILESYSTEM_ONLY,
            "location_kmz": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(field_ops_result) == {
            "field_ops_navigation_kmz": ArtifactClass.FILESYSTEM_ONLY,
            "field_ops_report": ArtifactClass.FILESYSTEM_ONLY,
            "field_ops_brief": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(gps_compare_result) == {
            "gps_point_comparison_json": ArtifactClass.FILESYSTEM_ONLY,
            "gps_point_comparison_csv": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(hypercube_result) == {
            "hypercube_tif": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_npy": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_order": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_stats": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_norm_params": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_audit": ArtifactClass.FILESYSTEM_ONLY,
            "notebook_FINAL_TESLA_V7_2_HYPERCUBE_tif": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_FINAL_TESLA_V7_2_HYPERCUBE_npy": ArtifactClass.LOCAL_SENSITIVE,
            "notebook_FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B_tif": ArtifactClass.LOCAL_SENSITIVE,
        }
        notebook_outputs = {item["filename"]: item for item in hypercube_result.metadata["notebook_output_statuses"]}
        assert notebook_outputs["FINAL_TESLA_V7_2_HYPERCUBE.tif"]["status"] == "implemented"
        assert notebook_outputs["FINAL_TESLA_V7_2_HYPERCUBE.npy"]["status"] == "implemented"
        assert notebook_outputs["FINAL_TESLA_V7_2_HYPERCUBE.npy"]["layout"] == "CHW"
        patched = notebook_outputs["FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif"]
        assert patched["status"] == "implemented"
        assert patched["actual_band_count"] == 13
        assert patched["em_anomaly_source_equivalent"] == "DEM_GEO8_TIFS/DEM_640.tif"
        assert "13 bands" in patched["note"]
        assert isinstance(patched["reason"], str)
        assert _artifact_classes(pca_result) == {
            "pca_anomaly_tif": ArtifactClass.LOCAL_SENSITIVE,
            "pca_eigenvalues": ArtifactClass.LOCAL_SENSITIVE,
            "parity_qa_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        object_classes = _artifact_classes(object_result)
        assert object_classes["objects_index"] == ArtifactClass.REDACTED_PUBLIC
        assert object_classes["clusters_summary"] == ArtifactClass.REDACTED_PUBLIC
        assert object_classes["object_mask"] == ArtifactClass.FILESYSTEM_ONLY
        patch_names = [name for name in object_classes if name.startswith("object_patch_")]
        assert patch_names
        assert all(object_classes[name] == ArtifactClass.FILESYSTEM_ONLY for name in patch_names)
        assert _artifact_classes(classifier_result) == {
            "experimental_classifications": ArtifactClass.REDACTED_PUBLIC,
            "experimental_summary": ArtifactClass.REDACTED_PUBLIC,
            "experimental_neutral_labels": ArtifactClass.REDACTED_PUBLIC,
        }
        assert _artifact_classes(alignment_result) == {
            "alignment_qa": ArtifactClass.REDACTED_PUBLIC,
            "alignment_audit": ArtifactClass.REDACTED_PUBLIC,
            "alignment_mask_selection": ArtifactClass.REDACTED_PUBLIC,
            "alignment_summary_redacted": ArtifactClass.LOCAL_SENSITIVE,
        }


def test_full_job_run_dir_matches_notebook_compatible_inventory_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
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
        asyncio.run(ClassifierStage().run(context))
        asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))

        expected_groups = {
            "DEM_GEO8_TIFS",
            "GEOTIFF_RADAR_BANDS",
            "NPY_RADAR_BANDS",
            "NPY_STACKS",
            "QA",
            "QA/sar/intermediates",
            "objects",
            "experimental",
        }
        assert "qa" not in {path.name for path in run_dir.iterdir() if path.is_dir()}
        for relative_dir in expected_groups:
            assert (run_dir / relative_dir).is_dir(), relative_dir

        observed_files = {path.relative_to(run_dir).as_posix() for path in run_dir.rglob("*") if path.is_file()}
        required_files = {
            "DEM_GEO8_TIFS/DEM_640.tif",
            "DEM_GEO8_TIFS/slope_deg_640.tif",
            "DEM_GEO8_TIFS/aspect_deg_640.tif",
            "DEM_GEO8_TIFS/roughness_100m_640.tif",
            "DEM_GEO8_TIFS/tpi_100m_640.tif",
            "DEM_GEO8_TIFS/hillshade_0to1_640.tif",
            "DEM_GEO8_TIFS/curv_laplacian_640.tif",
            "DEM_GEO8_TIFS/curv_plan_640.tif",
            "DEM_GEO8_TIFS/curv_profile_640.tif",
            "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif",
            "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif",
            "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif",
            "GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif",
            "NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy",
            "NPY_RADAR_BANDS/RADAR_angle_640_app.npy",
            "NPY_STACKS/RADAR_STACK_HWC_640_app.npy",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
            "QA/QA_GRID_dx_m_640.tif",
            "QA/QA_GRID_dy_m_640.tif",
            "QA/QA_GRID_validmask_640.tif",
            "QA/RUN_MANIFEST.json",
            "QA/REPORT_640_manifest.json",
            "QA/sar/intermediates/sar_intermediate_manifest.json",
            "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
            "QA/sar/intermediates/post_rtc/final_VH_dB.npy",
            "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy",
            "QA/sar/intermediates/post_rtc/final_angle.npy",
            "QA/stacks/secret_layers_manifest.json",
            "AI_READY_640/AI_READY_640_Secret_Gold_Halo.tif",
            "AI_READY_640/AI_READY_640_Secret_Silver_Oxide.tif",
            "AI_READY_640/AI_READY_640_Secret_Tunnel_Ceiling.tif",
            "AI_READY_640/AI_READY_640_Secret_Thermal_Inertia.tif",
            "AI_READY_640/AI_READY_640_Secret_Chemical_Protector.tif",
            "AI_READY_640/AI_READY_640_Secret_Hidden_Doors.tif",
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
            "objects_index.csv",
            "clusters_summary.csv",
            "objects/object_mask.npy",
            "experimental/classifications.csv",
            "experimental/summary.json",
            "experimental/neutral_target_labels.json",
        }
        for relative_path in required_files:
            assert (run_dir / relative_path).is_file(), relative_path
        assert not any(path.startswith("qa/") for path in observed_files)

        report_manifest = json.loads((run_dir / "QA" / "REPORT_640_manifest.json").read_text(encoding="utf-8"))
        assert report_manifest["schema"] == "notebook_report_640_manifest_v1"
        assert report_manifest["stage"] == "report_640"
        not_implemented_reports = {
            name
            for name, item in report_manifest["reports"].items()
            if item["status"] == "not_implemented_no_source_equivalent"
        }
        implemented_reports = {
            name
            for name, item in report_manifest["reports"].items()
            if item["status"] == "implemented"
        }
        assert not_implemented_reports == set()
        assert implemented_reports == {
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        }

        sar_manifest = json.loads(
            (run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json").read_text(encoding="utf-8")
        )
        assert sar_manifest["stages"]["per_image_products_db"]["status"] == "not_implemented_no_source_equivalent"
        assert sar_manifest["stages"]["pair_median"]["status"] == "not_implemented_no_source_equivalent"
        assert sar_manifest["stages"]["final_median_pre_rtc"]["status"] == "not_implemented_no_source_equivalent"
        assert sar_manifest["stages"]["post_sample_pre_rtc"]["status"] == "not_implemented_no_source_equivalent"
        assert sar_manifest["stages"]["post_rtc"]["status"] == "implemented"
        assert sar_manifest["stages"]["post_rtc"]["bands"] == {
            "VV_dB": "post_rtc/final_VV_dB.npy",
            "VH_dB": "post_rtc/final_VH_dB.npy",
            "logRatio_dB": "post_rtc/final_logRatio_dB.npy",
            "angle": "post_rtc/final_angle.npy",
        }
        assert sar_manifest["stages"]["post_rtc"]["source_mapping"] == {
            "post_rtc/final_VV_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/VV_dB.npy",
            "post_rtc/final_VH_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/VH_dB.npy",
            "post_rtc/final_logRatio_dB.npy": f"{SAR_NPY_OUTPUT_DIR}/logRatio_dB.npy",
            "post_rtc/final_angle.npy": f"{SAR_NPY_OUTPUT_DIR}/incidence.npy",
        }
        assert isinstance(sar_manifest["stages"]["post_rtc"]["source_description"], str)


def _artifact_classes(result) -> dict[str, ArtifactClass]:
    return {artifact.name: artifact.artifact_class for artifact in result.artifacts}


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
