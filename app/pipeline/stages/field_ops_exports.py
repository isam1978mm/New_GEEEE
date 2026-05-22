from __future__ import annotations

import json
import zipfile
from pathlib import Path

from pyproj import Transformer

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.focus_mask import FOCUS_SIZE_M
from app.pipeline.stages.grid import GridSpec

FIELD_OPS_KMZ_NAME = "field_ops_navigation.kmz"
FIELD_OPS_REPORT_NAME = "field_ops_report.json"
FIELD_OPS_BRIEF_NAME = "field_ops_brief.txt"


def build_field_ops_payloads(grid_spec: GridSpec) -> dict[str, str]:
    bounds = grid_spec.manifest.bounds_m
    center_x = (float(bounds["xmin"]) + float(bounds["xmax"])) / 2.0
    center_y = (float(bounds["ymin"]) + float(bounds["ymax"])) / 2.0
    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(center_x, center_y)

    report_payload = {
        "deliverable": "field_operations",
        "navigation_point": {"lat": float(lat), "lon": float(lon)},
        "focus_size_m": float(FOCUS_SIZE_M),
        "grid": {
            "epsg": int(grid_spec.manifest.epsg),
            "scale_m": int(grid_spec.manifest.scale_m),
            "size_px": int(grid_spec.manifest.size_px),
        },
        "local_only": True,
    }
    brief_text = (
        "Local field-operations brief\n"
        f"Navigation point: {lat:.8f}, {lon:.8f}\n"
        f"Focus window: {FOCUS_SIZE_M:.1f} m\n"
        f"Grid EPSG: {grid_spec.manifest.epsg}\n"
    )
    kml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>field_ops_navigation</name>
      <Point>
        <coordinates>{lon},{lat},0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
"""
    return {
        "report_json": json.dumps(report_payload, indent=2, sort_keys=True),
        "brief_text": brief_text,
        "kml": kml_payload,
    }


def write_field_ops_outputs(run_dir: Path, payloads: dict[str, str]) -> dict[str, Path]:
    field_ops_dir = run_dir / "full_job" / "field_ops"
    kmz_dir = run_dir / "kmz"
    field_ops_dir.mkdir(parents=True, exist_ok=True)
    kmz_dir.mkdir(parents=True, exist_ok=True)

    report_path = field_ops_dir / FIELD_OPS_REPORT_NAME
    brief_path = field_ops_dir / FIELD_OPS_BRIEF_NAME
    kmz_path = kmz_dir / FIELD_OPS_KMZ_NAME
    report_path.write_text(payloads["report_json"], encoding="utf-8")
    brief_path.write_text(payloads["brief_text"], encoding="utf-8")
    with zipfile.ZipFile(kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("doc.kml", payloads["kml"])
    return {
        "report": report_path,
        "brief": brief_path,
        "kmz": kmz_path,
    }


class FieldOpsExportsStage(Stage):
    name = "field_ops_exports"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook field-operation KMZ and report deliverables with local-only FILESYSTEM_ONLY run artifacts."

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        payloads = build_field_ops_payloads(self.grid_spec)
        outputs = write_field_ops_outputs(context.run_dir, payloads)
        artifacts = [
            build_stage_artifact(
                name="field_ops_navigation_kmz",
                relative_path=outputs["kmz"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["kmz"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="field_ops_report",
                relative_path=outputs["report"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["report"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="field_ops_brief",
                relative_path=outputs["brief"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["brief"].stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "export_count": 3,
                "local_only": True,
            },
        )
