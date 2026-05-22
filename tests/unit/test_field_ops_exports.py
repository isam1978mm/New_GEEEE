from __future__ import annotations

import asyncio
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.field_ops_exports import FieldOpsExportsStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_field_ops_exports_stage_writes_filesystem_only_kmz_and_reports() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))
        asyncio.run(FocusMaskStage(grid_spec=grid_spec).run(context))
        asyncio.run(LocationExportsStage(grid_spec=grid_spec).run(context))

        result = asyncio.run(FieldOpsExportsStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "field_ops_navigation_kmz",
            "field_ops_report",
            "field_ops_brief",
        ]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        report_path = run_dir / "full_job" / "field_ops" / "field_ops_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["deliverable"] == "field_operations"
        assert report["local_only"] is True

        brief_path = run_dir / "full_job" / "field_ops" / "field_ops_brief.txt"
        assert "Local field-operations brief" in brief_path.read_text(encoding="utf-8")

        kmz_path = run_dir / "kmz" / "field_ops_navigation.kmz"
        with zipfile.ZipFile(kmz_path, "r") as archive:
            assert archive.namelist() == ["doc.kml"]
            kml_text = archive.read("doc.kml").decode("utf-8")
        assert "<Point>" in kml_text


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
