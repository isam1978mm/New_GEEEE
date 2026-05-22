from __future__ import annotations

import csv
import json
from pathlib import Path

from pyproj import Transformer

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.grid import GridSpec

GPS_COMPARISON_JSON_NAME = "gps_point_comparison.json"
GPS_COMPARISON_CSV_NAME = "gps_point_comparison.csv"


def build_gps_comparison_payloads(
    *,
    input_lat: float,
    input_lon: float,
    grid_spec: GridSpec,
) -> dict[str, object]:
    bounds = grid_spec.manifest.bounds_m
    center_x = (float(bounds["xmin"]) + float(bounds["xmax"])) / 2.0
    center_y = (float(bounds["ymin"]) + float(bounds["ymax"])) / 2.0
    transformer_to_wgs84 = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)
    transformer_to_utm = Transformer.from_crs("EPSG:4326", grid_spec.crs, always_xy=True)

    center_lon, center_lat = transformer_to_wgs84.transform(center_x, center_y)
    input_x, input_y = transformer_to_utm.transform(input_lon, input_lat)
    delta_x_m = float(center_x - input_x)
    delta_y_m = float(center_y - input_y)
    planar_offset_m = float((delta_x_m**2 + delta_y_m**2) ** 0.5)

    summary = {
        "report_type": "gps_point_comparison",
        "local_only": True,
        "grid_epsg": int(grid_spec.manifest.epsg),
        "input_point": {
            "lat": float(input_lat),
            "lon": float(input_lon),
        },
        "grid_center_point": {
            "lat": float(center_lat),
            "lon": float(center_lon),
        },
        "offset_m": {
            "delta_x_m": delta_x_m,
            "delta_y_m": delta_y_m,
            "planar_offset_m": planar_offset_m,
        },
    }
    rows = [
        {
            "point_role": "input_point",
            "lat": float(input_lat),
            "lon": float(input_lon),
            "delta_x_m": 0.0,
            "delta_y_m": 0.0,
            "planar_offset_m": 0.0,
        },
        {
            "point_role": "grid_center_point",
            "lat": float(center_lat),
            "lon": float(center_lon),
            "delta_x_m": delta_x_m,
            "delta_y_m": delta_y_m,
            "planar_offset_m": planar_offset_m,
        },
    ]
    return {
        "summary": summary,
        "rows": rows,
    }


def write_gps_comparison_outputs(run_dir: Path, payloads: dict[str, object]) -> dict[str, Path]:
    gps_dir = run_dir / "full_job" / "gps"
    gps_dir.mkdir(parents=True, exist_ok=True)

    json_path = gps_dir / GPS_COMPARISON_JSON_NAME
    csv_path = gps_dir / GPS_COMPARISON_CSV_NAME
    json_path.write_text(json.dumps(payloads["summary"], indent=2, sort_keys=True), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["point_role", "lat", "lon", "delta_x_m", "delta_y_m", "planar_offset_m"],
        )
        writer.writeheader()
        for row in payloads["rows"]:
            writer.writerow(row)

    return {
        "json": json_path,
        "csv": csv_path,
    }


class GpsComparisonStage(Stage):
    name = "gps_compare"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook GPS/reference comparison outputs with local-only FILESYSTEM_ONLY run artifacts."

    def __init__(self, *, input_lat: float, input_lon: float, grid_spec: GridSpec) -> None:
        self.input_lat = input_lat
        self.input_lon = input_lon
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        payloads = build_gps_comparison_payloads(
            input_lat=self.input_lat,
            input_lon=self.input_lon,
            grid_spec=self.grid_spec,
        )
        outputs = write_gps_comparison_outputs(context.run_dir, payloads)
        artifacts = [
            build_stage_artifact(
                name="gps_point_comparison_json",
                relative_path=outputs["json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="gps_point_comparison_csv",
                relative_path=outputs["csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["csv"].stat().st_size,
                http_servable=False,
            ),
        ]
        summary = payloads["summary"]
        assert isinstance(summary, dict)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "planar_offset_m": float(summary["offset_m"]["planar_offset_m"]),
                "local_only": True,
            },
        )
