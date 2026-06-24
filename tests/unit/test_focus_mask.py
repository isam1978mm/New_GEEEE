from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.services.storage import read_manifest


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
        assert "ROI_Composite_Score" in pixel_rows[0]
        assert "Secret_Gold_Halo" in pixel_rows[0]
        assert "REPORT_640_Mass_Report" in pixel_rows[0]

        with target_report.open("r", encoding="utf-8", newline="") as handle:
            target_rows = list(csv.DictReader(handle))
        assert 1 <= len(target_rows) <= 5
        assert "Classification" in target_rows[0]
        assert "Confidence" in target_rows[0]

        geojson = json.loads(target_geojson.read_text(encoding="utf-8"))
        assert geojson["type"] == "FeatureCollection"
        assert 1 <= len(geojson["features"]) <= 5
        assert geojson["features"][0]["geometry"]["type"] == "Point"

        hard_csv = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.csv"
        hard_txt = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.txt"
        hard_json = run_dir / "full_job" / "focus" / "AI_HARD_TYPE_CLASSIFIER_CORE9.json"
        assert hard_csv.is_file()
        assert hard_txt.is_file()
        assert hard_json.is_file()

        with hard_csv.open("r", encoding="utf-8", newline="") as handle:
            hard_rows = list(csv.DictReader(handle))
        assert len(hard_rows) == 1
        assert hard_rows[0]["Source_Cell"] == "cell_128"
        assert hard_rows[0]["Primary_Class"]
        assert hard_rows[0]["Void_Type"]
        assert hard_rows[0]["Metal_Type"]
        assert hard_rows[0]["Content_Type"]
        assert "Final_Confidence" in hard_rows[0]

        hard_payload = json.loads(hard_json.read_text(encoding="utf-8"))
        assert hard_payload["source_cell"] == "cell_128"
        assert hard_payload["status"] == "implemented"
        assert hard_payload["record"]["Primary_Class"] == hard_rows[0]["Primary_Class"]
        assert "AI HARD TYPE CLASSIFIER" in hard_txt.read_text(encoding="utf-8")




def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
