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
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher


def test_location_exports_stage_writes_filesystem_only_geojson_and_kmz() -> None:
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

        result = asyncio.run(LocationExportsStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "location_geojson",
            "location_kmz",
        ]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        geojson_path = run_dir / "full_job" / "location" / "site_location.geojson"
        geojson_payload = json.loads(geojson_path.read_text(encoding="utf-8"))
        assert geojson_payload["type"] == "FeatureCollection"
        feature_roles = {feature["properties"]["export_role"] for feature in geojson_payload["features"]}
        assert feature_roles == {"site_point", "focus_zone_17m"}

        kmz_path = run_dir / "kmz" / "site_location.kmz"
        with zipfile.ZipFile(kmz_path, "r") as archive:
            assert archive.namelist() == ["doc.kml"]
            kml_text = archive.read("doc.kml").decode("utf-8")
        assert "<Point>" in kml_text
        assert "<Polygon>" in kml_text


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
