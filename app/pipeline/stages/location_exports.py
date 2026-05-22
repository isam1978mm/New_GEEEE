from __future__ import annotations

import json
import zipfile
from pathlib import Path

from pyproj import Transformer

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.focus_mask import FOCUS_SIZE_M
from app.pipeline.stages.grid import GridSpec

LOCATION_GEOJSON_NAME = "site_location.geojson"
LOCATION_KMZ_NAME = "site_location.kmz"


def build_location_export_payloads(grid_spec: GridSpec) -> dict[str, str]:
    bounds = grid_spec.manifest.bounds_m
    center_x = (float(bounds["xmin"]) + float(bounds["xmax"])) / 2.0
    center_y = (float(bounds["ymin"]) + float(bounds["ymax"])) / 2.0
    half_focus_m = FOCUS_SIZE_M / 2.0
    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)

    point_lon, point_lat = transformer.transform(center_x, center_y)
    polygon_utm = [
        (center_x - half_focus_m, center_y - half_focus_m),
        (center_x + half_focus_m, center_y - half_focus_m),
        (center_x + half_focus_m, center_y + half_focus_m),
        (center_x - half_focus_m, center_y + half_focus_m),
        (center_x - half_focus_m, center_y - half_focus_m),
    ]
    polygon_wgs84 = [transformer.transform(x, y) for x, y in polygon_utm]
    polygon_coordinates = [[float(lon), float(lat)] for lon, lat in polygon_wgs84]

    geojson_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"export_role": "site_point"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(point_lon), float(point_lat)],
                },
            },
            {
                "type": "Feature",
                "properties": {"export_role": "focus_zone_17m"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon_coordinates],
                },
            },
        ],
    }

    polygon_kml_coordinates = " ".join(f"{lon},{lat},0" for lon, lat in polygon_wgs84)
    kml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>site_point</name>
      <Point>
        <coordinates>{point_lon},{point_lat},0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>focus_zone_17m</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{polygon_kml_coordinates}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""
    return {
        "geojson": json.dumps(geojson_payload, indent=2, sort_keys=True),
        "kml": kml_payload,
    }


def write_location_exports(run_dir: Path, payloads: dict[str, str]) -> dict[str, Path]:
    location_dir = run_dir / "full_job" / "location"
    kmz_dir = run_dir / "kmz"
    location_dir.mkdir(parents=True, exist_ok=True)
    kmz_dir.mkdir(parents=True, exist_ok=True)

    geojson_path = location_dir / LOCATION_GEOJSON_NAME
    kmz_path = kmz_dir / LOCATION_KMZ_NAME
    geojson_path.write_text(payloads["geojson"], encoding="utf-8")
    with zipfile.ZipFile(kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("doc.kml", payloads["kml"])
    return {
        "geojson": geojson_path,
        "kmz": kmz_path,
    }


class LocationExportsStage(Stage):
    name = "location_exports"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook exact-location GeoJSON and KMZ exports with local-only FILESYSTEM_ONLY run artifacts."

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        payloads = build_location_export_payloads(self.grid_spec)
        outputs = write_location_exports(context.run_dir, payloads)
        artifacts = [
            build_stage_artifact(
                name="location_geojson",
                relative_path=outputs["geojson"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["geojson"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="location_kmz",
                relative_path=outputs["kmz"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["kmz"].stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "export_count": 2,
                "local_only": True,
            },
        )
