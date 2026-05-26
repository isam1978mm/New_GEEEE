from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.db.models.enums import ArtifactClass
from app.errors import GridDriftError
from app.pipeline._base import ParityCategory, StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import read_manifest


def test_zero_shift_stage_accepts_grid_locked_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        result = asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))

        assert ZeroShiftStage(grid_spec=grid_spec).parity_category == ParityCategory.PARITY_REPRODUCES
        assert [artifact.name for artifact in result.artifacts] == ["zero_shift_summary", "drift_audit"]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert result.metadata["status"] == "grid_locked"

        summary = json.loads((run_dir / "qa" / "grid_dem" / "zero_shift_summary.json").read_text(encoding="utf-8"))
        assert summary["status"] == "grid_locked"
        with (run_dir / "qa" / "grid_dem" / "drift_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        artifact_names = {row["artifact_name"] for row in rows}
        assert {"dem.tif", "DEM_640.tif", "dem.npy"} <= artifact_names
        assert result.metadata["validated_tifs"] == sum(1 for row in rows if row["artifact_type"] == "tif")
        assert result.metadata["validated_arrays"] == sum(1 for row in rows if row["artifact_type"] == "npy")
        assert all(row["passes_alignment"] == "true" for row in rows)


def test_zero_shift_stage_raises_grid_drift_error_for_half_pixel_shift() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        sidecar_path = raster_sidecar_path(run_dir / "dem.tif")
        metadata = read_manifest(sidecar_path)
        metadata["transform"][2] = metadata["transform"][2] + 5.0
        sidecar_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

        with pytest.raises(GridDriftError):
            asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))

        summary = json.loads((run_dir / "qa" / "grid_dem" / "zero_shift_summary.json").read_text(encoding="utf-8"))
        assert summary["status"] == "grid_drift_detected"
        assert "dem.tif" in summary["failing_artifacts"]
        with (run_dir / "qa" / "grid_dem" / "drift_audit.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        dem_row = next(row for row in rows if row["artifact_name"] == "dem.tif")
        assert dem_row["passes_alignment"] == "false"
        assert "half_pixel_shift" in dem_row["issues"]


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
