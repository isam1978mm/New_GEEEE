from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.gps_compare import (
    GpsComparisonStage,
    build_gps_comparison_payloads,
)
from app.pipeline.stages.grid import build_run_grid


def test_build_gps_comparison_payloads_includes_local_only_offsets() -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)

    payloads = build_gps_comparison_payloads(
        input_lat=35.59499,
        input_lon=36.12694,
        grid_spec=grid_spec,
    )

    summary = payloads["summary"]
    rows = payloads["rows"]
    assert summary["report_type"] == "gps_point_comparison"
    assert summary["local_only"] is True
    assert set(summary["offset_m"]) == {"delta_x_m", "delta_y_m", "planar_offset_m"}
    assert len(rows) == 2
    assert rows[0]["point_role"] == "input_point"
    assert rows[1]["point_role"] == "grid_center_point"


def test_gps_comparison_stage_writes_filesystem_only_reports() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        result = asyncio.run(
            GpsComparisonStage(input_lat=35.59499, input_lon=36.12694, grid_spec=grid_spec).run(context)
        )

        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "gps_point_comparison_json": ArtifactClass.FILESYSTEM_ONLY,
            "gps_point_comparison_csv": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        json_path = run_dir / "full_job" / "gps" / "gps_point_comparison.json"
        csv_path = run_dir / "full_job" / "gps" / "gps_point_comparison.csv"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        assert payload["input_point"]["lat"] == 35.59499
        assert payload["input_point"]["lon"] == 36.12694
        assert len(rows) == 2
        assert rows[1]["point_role"] == "grid_center_point"


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
