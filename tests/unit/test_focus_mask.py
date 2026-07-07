from __future__ import annotations

import asyncio
import csv
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

PNG_SIGNATURE = bytes.fromhex("89504E470D0A1A0A")

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.focus_mask import FocusMaskStage, _hard_get_vals
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.services.storage import read_manifest


def test_hard_get_vals_excludes_nodata_sentinel() -> None:
    arr = np.array(
        [
            [1.5, -9999.0],
            [np.nan, 2.5],
        ],
        dtype=np.float32,
    )
    mask = np.ones(arr.shape, dtype=bool)

    vals = _hard_get_vals(arr, mask)

    np.testing.assert_array_equal(vals, np.array([1.5, 2.5], dtype=np.float64))


def test_focus_mask_stage_writes_filesystem_only_local_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(SecretLayersStage(grid_spec=grid_spec).run(context))
        asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))

        result = asyncio.run(FocusMaskStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "focus_zone_17m_tif",
            "focus_zone_17m_npy",
            "focus_zone_ai_ready_window",
            "focus_zone_summary",
            "focus_band_summary",
            "focus_17m_pixel_report_v7_2",
            "focus_17m_targets_v7_2",
            "focus_17m_targets_geojson_v7_2",
            "hard_type_classifier_core9_csv",
            "hard_type_classifier_core9_txt",
            "hard_type_classifier_core9_json",
            "core_ring_scene_targets_v7_2c_csv",
            "core_ring_scene_decision_v7_2c_txt",
            "core_ring_scene_decision_v7_2c_json",
            "detected_features_wgs84_geojson_v7_2",
            "ai_heatmap_classification_png",
            "ai_heatmap_classification_kmz",
            "ai_3d_target_visualization_kmz",
            "final_archeo_intelligence_map_geojson",
            "tesla_v7_2_field_operations_kmz",
            "app_native_live_overlay_manifest_v7_2",
            "metal_fingerprint_diagnostic_csv",
            "metal_fingerprint_diagnostic_json",
            "metal_fingerprint_diagnostic_txt",
        ]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        mask = np.load(run_dir / "full_job" / "focus" / "focus_zone_17m.npy")
        assert mask.shape == (grid_spec.size, grid_spec.size)
        assert int(mask.sum()) == 9
        mask_sidecar = read_manifest(raster_sidecar_path(run_dir / "full_job" / "focus" / "focus_zone_17m.tif"))
        assert mask_sidecar["transform"] == grid_spec.manifest.crs_transform
        assert mask_sidecar["dtype"] == "uint8"
        assert mask_sidecar["nodata"] == 0.0

        focus_window = np.load(run_dir / "full_job" / "focus" / "focus_zone_ai_ready_window.npy")
        assert focus_window.ndim == 3
        assert focus_window.shape[:2] == (3, 3)
        assert focus_window.shape[-1] > 1

        summary = json.loads((run_dir / "full_job" / "focus" / "focus_zone_summary.json").read_text(encoding="utf-8"))
        assert summary["focus_size_m"] == 17.0
        assert summary["mask_pixel_count"] == int(mask.sum())
        assert "coordinates" not in json.dumps(summary).casefold()
        assert "geometry" not in json.dumps(summary).casefold()

        with (run_dir / "full_job" / "focus" / "focus_zone_band_summary.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert rows[0]["band_name"] == "VV_dB"

        pixel_report = run_dir / "full_job" / "focus" / "AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv"
        target_report = run_dir / "full_job" / "focus" / "AI_FOCUS_17M_TARGETS_V7_2.csv"
        target_geojson = run_dir / "full_job" / "focus" / "AI_FOCUS_17M_TARGETS_V7_2.geojson"
        assert pixel_report.is_file()
        assert target_report.is_file()
        assert target_geojson.is_file()

        with pixel_report.open("r", encoding="utf-8", newline="") as handle:
            pixel_rows = list(csv.DictReader(handle))
        assert len(pixel_rows) == int(mask.sum())
        assert "X_native" in pixel_rows[0]
        assert "Y_native" in pixel_rows[0]
        assert "Lon" in pixel_rows[0]
        assert "Lat" in pixel_rows[0]
        assert "Google_Maps_Link" in pixel_rows[0]
        assert "z_Gold" in pixel_rows[0]
        assert "z_Mass" in pixel_rows[0]
        assert "محور_معدني" in pixel_rows[0]
        assert "محور_فراغ" in pixel_rows[0]
        assert "محور_بنيوي" in pixel_rows[0]
        assert "درجة_مركبة" in pixel_rows[0]
        assert "Secret_Gold_Halo" in pixel_rows[0]
        assert "REPORT_640_Mass_Report" in pixel_rows[0]

        with target_report.open("r", encoding="utf-8", newline="") as handle:
            target_rows = list(csv.DictReader(handle))
        assert 1 <= len(target_rows) <= 5
        assert "الهدف_المرجح" in target_rows[0]
        assert "المحتوى_المرجح" in target_rows[0]
        assert "نظام_الدفن_او_الحقبة_المرجحة" in target_rows[0]
        assert "تحذير_الفخاخ" in target_rows[0]
        assert "الثقة_النهائية_%" in target_rows[0]
        assert "تفسير_الذكاء" in target_rows[0]
        assert "Google_Maps_Link" in target_rows[0]

        geojson = json.loads(target_geojson.read_text(encoding="utf-8"))
        assert geojson["type"] == "FeatureCollection"
        assert 1 <= len(geojson["features"]) <= 5
        assert geojson["features"][0]["geometry"]["type"] == "Point"
        assert "الهدف_المرجح" in geojson["features"][0]["properties"]
        assert "الثقة_النهائية_%" in geojson["features"][0]["properties"]
        assert "Google_Maps_Link" in geojson["features"][0]["properties"]

        hard_csv = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.csv"
        hard_txt = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.txt"
        hard_json = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.json"
        assert hard_csv.is_file()
        assert hard_txt.is_file()
        assert hard_json.is_file()

        with hard_csv.open("r", encoding="utf-8", newline="") as handle:
            hard_reader = csv.DictReader(handle)
            hard_rows = list(hard_reader)
        assert len(hard_rows) == 1
        assert hard_reader.fieldnames == [
            "Core_Mask_Source",
            "Core_Pixels",
            "Primary_Class",
            "Void_Type",
            "Metal_Type",
            "Metal_Shape",
            "Content_Type",
            "Estimated_Stacked_Boxes",
            "Estimated_Aligned_Jars",
            "Final_Confidence",
            "Void_Probability",
            "Metal_Probability",
            "Fill_Probability",
            "Entrance_Probability",
            "Surface_Exclusion",
            "Dominant_Direction",
            "Directionality_Strength",
            "Entrance_Score",
            "Shaft_Score",
            "Chamber_Score",
            "Drain_Void_Score",
            "Gold_Like_Score",
            "Silver_Like_Score",
            "Dense_Metal_Score",
            "Coins_Score",
            "Ingots_Score",
            "Statues_Score",
            "Pottery_Treasures_Score",
            "General_Antiquities_Score",
        ]
        assert "Source_Cell" not in hard_rows[0]
        expected_core_mask_source = "FOCUS_MASK_" + "17M"
        assert hard_rows[0]["Core_Mask_Source"] == expected_core_mask_source
        assert float(hard_rows[0]["Final_Confidence"]) >= 0.0

        hard_payload = json.loads(hard_json.read_text(encoding="utf-8"))
        assert "source_cell" not in hard_payload
        assert "record" not in hard_payload
        assert hard_payload["core_mask_name"] == expected_core_mask_source
        assert hard_payload["primary_class"] in {
            "MIXED_VOID_METAL",
            "STRUCTURAL_VOID",
            "METAL_DENSE",
            "FILL_OR_POTTERY_DISTURBANCE",
            "INCONCLUSIVE",
        }

        core_csv = run_dir / "full_job" / "focus" / "AI_CORE_RING_SCENE_TARGETS_V7_2C.csv"
        core_txt = run_dir / "full_job" / "focus" / "AI_CORE_RING_SCENE_DECISION_V7_2C.txt"
        core_json = run_dir / "full_job" / "focus" / "AI_CORE_RING_SCENE_DECISION_V7_2C.json"
        assert core_csv.is_file()
        assert core_txt.is_file()
        assert core_json.is_file()

        with core_csv.open("r", encoding="utf-8", newline="") as handle:
            core_rows = list(csv.DictReader(handle))
        assert len(core_rows) == 1
        assert "Source_Cell" not in core_rows[0]
        assert core_rows[0]["Scenario"]
        assert core_rows[0]["Decision_Grade"]
        assert "Detection_Confidence" in core_rows[0]
        assert "Interpretation_Confidence" in core_rows[0]
        assert "Final_Confidence" in core_rows[0]
        assert "Resolution_Note" in core_rows[0]

        core_payload = json.loads(core_json.read_text(encoding="utf-8"))
        assert "source_cell" not in core_payload
        assert "status" not in core_payload
        assert "target_count" not in core_payload
        assert core_payload["core_pixel_count"] == int(mask.sum())
        assert core_payload["ring_near_pixel_count"] >= int(mask.sum())
        assert "band_analysis" in core_payload
        assert "Secret_Gold_Halo" in core_payload["band_analysis"]
        assert "AI CORE-vs-RING-vs-SCENE DECISION" in core_txt.read_text(encoding="utf-8")

        detected_geojson = run_dir / "full_job" / "focus" / "AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson"
        assert detected_geojson.is_file()

        detected_payload = json.loads(detected_geojson.read_text(encoding="utf-8"))
        assert detected_payload["type"] == "FeatureCollection"
        assert detected_payload["source_cell"] == "cell_123"
        assert detected_payload["coordinate_reference_system"] == "EPSG:4326"
        assert len(detected_payload["features"]) == len(target_rows)

        first_feature = detected_payload["features"][0]
        assert first_feature["geometry"]["type"] == "Point"
        lon, lat = first_feature["geometry"]["coordinates"]
        assert -180.0 <= float(lon) <= 180.0
        assert -90.0 <= float(lat) <= 90.0
        assert detected_payload["app_output_contract"] == "app_enhanced_local_v1"
        assert detected_payload["production_redaction_required"] is True
        assert detected_payload["parity_status"] == "app_enhanced_local_contract_not_exact_file_parity"
        assert first_feature["properties"]["Source_Cell"] == "cell_123"
        assert first_feature["properties"]["App_Output_Contract"] == "app_enhanced_local_v1"
        assert first_feature["properties"]["Production_Redaction_Required"] is True
        assert first_feature["properties"]["Notebook_Semantic_Source"] == "cell_123_AI_FOCUS_17M_TARGETS_V7_2"
        assert "UTM_E" in first_feature["properties"]
        assert "UTM_N" in first_feature["properties"]
        assert "Google_Maps_Link" in first_feature["properties"]
        assert "Classification" in first_feature["properties"]
        assert "Hard_Primary_Class" in first_feature["properties"]
        assert "Decision_Grade" in first_feature["properties"]
        assert "الهدف_المرجح" in first_feature["properties"]
        assert "المحتوى_المرجح" in first_feature["properties"]
        assert "نظام_الدفن_او_الحقبة_المرجحة" in first_feature["properties"]
        assert "تحذير_الفخاخ" in first_feature["properties"]
        assert "الثقة_النهائية_%" in first_feature["properties"]
        assert "تفسير_الذكاء" in first_feature["properties"]

        heatmap_png = run_dir / "full_job" / "focus" / "AI_HEATMAP_CLASSIFICATION.png"
        heatmap_kmz = run_dir / "full_job" / "focus" / "AI_HEATMAP_CLASSIFICATION.kmz"
        targets_3d_kmz = run_dir / "full_job" / "focus" / "AI_3D_TARGET_VISUALIZATION.kmz"

        assert heatmap_png.is_file()
        assert heatmap_png.read_bytes().startswith(PNG_SIGNATURE)
        assert heatmap_kmz.is_file()
        assert targets_3d_kmz.is_file()

        with zipfile.ZipFile(heatmap_kmz, "r") as zf:
            heatmap_names = set(zf.namelist())
            assert "doc.kml" in heatmap_names
            assert "heat.png" in heatmap_names
            assert zf.read("heat.png").startswith(PNG_SIGNATURE)
            heatmap_kml = zf.read("doc.kml").decode("utf-8")

        assert "AI Heatmap Classification" in heatmap_kml
        assert "<GroundOverlay>" in heatmap_kml
        assert "<LatLonBox>" in heatmap_kml
        assert "source_cell=cell_155" in heatmap_kml

        with zipfile.ZipFile(targets_3d_kmz, "r") as zf:
            target_names = set(zf.namelist())
            assert "doc.kml" in target_names
            target_kml = zf.read("doc.kml").decode("utf-8")

        assert "AI 3D Target Visualization" in target_kml
        assert "source_cell=cell_155" in target_kml
        assert target_kml.count("<Placemark>") == len(target_rows)
        assert "<altitudeMode>relativeToGround</altitudeMode>" in target_kml

        field_geojson = run_dir / "full_job" / "focus" / "FINAL_ARCHEO_INTELLIGENCE_MAP.geojson"
        field_kmz = run_dir / "full_job" / "focus" / "TESLA_V7_2_FIELD_OPERATIONS.kmz"

        assert field_geojson.is_file()
        assert field_kmz.is_file()

        field_payload = json.loads(field_geojson.read_text(encoding="utf-8"))
        assert field_payload["type"] == "FeatureCollection"
        assert field_payload["source_cell"] == "cell_200"
        assert field_payload["coordinate_reference_system"] == "EPSG:4326"
        assert len(field_payload["features"]) == len(target_rows)

        field_first = field_payload["features"][0]
        assert field_first["geometry"]["type"] == "Point"
        field_lon, field_lat = field_first["geometry"]["coordinates"]
        assert -180.0 <= float(field_lon) <= 180.0
        assert -90.0 <= float(field_lat) <= 90.0
        assert field_first["properties"]["Source_Cell"] == "cell_200"
        assert "Material_Content" in field_first["properties"]
        assert "Field_Notes" in field_first["properties"]
        assert "UTM" in field_first["properties"]

        with zipfile.ZipFile(field_kmz, "r") as zf:
            field_names = set(zf.namelist())
            assert "doc.kml" in field_names
            field_kml = zf.read("doc.kml").decode("utf-8")

        assert "Tesla v7.2 Mission: Advanced Intelligence Assets" in field_kml
        assert "source_cell=cell_200" in field_kml
        assert field_kml.count("<Placemark>") == len(target_rows)
        assert "Strategic Intelligence Data" in field_kml

        live_manifest = run_dir / "full_job" / "focus" / "APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json"

        assert live_manifest.is_file()
        live_payload = json.loads(live_manifest.read_text(encoding="utf-8"))

        assert live_payload["type"] == "AppNativeLiveOverlayManifest"
        assert live_payload["source_cell"] == "cell_243"
        assert live_payload["privacy"] == "FILESYSTEM_ONLY"
        assert live_payload["http_servable"] is False
        assert live_payload["downloadable_via_api"] is False
        assert live_payload["basemap"] == "HYBRID"
        assert live_payload["target_count"] == len(target_rows)
        assert live_payload["exact_coordinates_in_manifest"] is False
        assert live_payload["raw_geometry_in_manifest"] is False

        live_layers = live_payload["layers"]
        layer_ids = {layer["id"] for layer in live_layers}
        assert "cnn_digital_matrix" in layer_ids
        assert "detected_target_markers" in layer_ids
        assert "detected_target_area_buffers" in layer_ids
        assert "subterranean_corridor_candidates" in layer_ids
        assert any(layer["status"] == "pending_dependency" for layer in live_layers)

        metal_csv = run_dir / "full_job" / "focus" / "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv"
        metal_json = run_dir / "full_job" / "focus" / "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json"
        metal_txt = run_dir / "full_job" / "focus" / "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt"

        assert metal_csv.is_file()
        assert metal_json.is_file()
        assert metal_txt.is_file()

        metal_payload = json.loads(metal_json.read_text(encoding="utf-8"))
        assert metal_payload["schema_version"] == "plan_b33_metal_fingerprint_diagnostic_v1"
        assert metal_payload["source_cell"] == "cell_185"
        assert metal_payload["privacy"] == "FILESYSTEM_ONLY"
        assert metal_payload["http_servable"] is False
        assert metal_payload["downloadable_via_api"] is False
        assert metal_payload["uses_model_inference"] is False
        assert metal_payload["imports_torch"] is False
        assert metal_payload["loads_weights"] is False
        assert metal_payload["runs_forward_pass"] is False
        assert metal_payload["creates_geojson"] is False
        assert metal_payload["creates_kmz"] is False
        assert metal_payload["target_count"] == len(target_rows)
        assert "AI METAL FINGERPRINT DIAGNOSTIC V7.2" in metal_txt.read_text(encoding="utf-8")






def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
