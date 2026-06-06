from __future__ import annotations

from dataclasses import dataclass
import math
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from xml.sax.saxutils import escape as xml_escape
import zipfile

from app.pipeline.parity import resolve_run_output_path


PRIVATE_GEOJSON_DEFAULT_OUTPUT_DIR = "private_map_artifacts/geojson"
PRIVATE_GEOJSON_DEFAULT_FILENAME = "private_features.geojson"
PRIVATE_KMZ_DEFAULT_OUTPUT_DIR = "private_map_artifacts/kmz"
PRIVATE_KMZ_DEFAULT_FILENAME = "private_points.kmz"
PRIVATE_KMZ_KML_FILENAME = "doc.kml"


@dataclass(frozen=True)
class PrivateGeoJsonWriteResult:
    private_path: Path
    artifact_metadata: dict[str, object]
    redacted_summary: dict[str, object]


@dataclass(frozen=True)
class PrivateKmzWriteResult:
    private_path: Path
    artifact_metadata: dict[str, object]
    redacted_summary: dict[str, object]


def write_private_geojson_feature_collection(
    *,
    run_dir: str | Path,
    features: Iterable[Mapping[str, Any]],
    output_relative_dir: str | Path = PRIVATE_GEOJSON_DEFAULT_OUTPUT_DIR,
    filename: str | Path = PRIVATE_GEOJSON_DEFAULT_FILENAME,
) -> PrivateGeoJsonWriteResult:
    """Write a private filesystem-only GeoJSON FeatureCollection under ``run_dir``."""

    normalized_features = tuple(_validate_feature(feature) for feature in features)
    if not normalized_features:
        raise ValueError("private GeoJSON FeatureCollection requires at least one Feature")

    output_dir = resolve_run_output_path(run_dir, output_relative_dir)
    output_path = resolve_run_output_path(run_dir, Path(output_relative_dir) / filename)
    if output_path.suffix.lower() != ".geojson":
        raise ValueError("private GeoJSON filename must end with .geojson")

    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": list(normalized_features),
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    artifact_metadata: dict[str, object] = {
        "artifact_type": "GeoJSON FeatureCollection",
        "artifact_class": "FILESYSTEM_ONLY",
        "private_classification": "PRIVATE_COORDINATE_ARTIFACT",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "feature_count": len(normalized_features),
        "local_path": str(output_path),
    }
    redacted_summary: dict[str, object] = {
        "artifact_type": "GeoJSON FeatureCollection",
        "feature_count": len(normalized_features),
        "private_classification": "PRIVATE_COORDINATE_ARTIFACT",
        "artifact_class": "FILESYSTEM_ONLY",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
    }
    return PrivateGeoJsonWriteResult(
        private_path=output_path,
        artifact_metadata=artifact_metadata,
        redacted_summary=redacted_summary,
    )


def write_private_kmz_points(
    *,
    run_dir: str | Path,
    points: Iterable[Mapping[str, Any]],
    output_relative_dir: str | Path = PRIVATE_KMZ_DEFAULT_OUTPUT_DIR,
    filename: str | Path = PRIVATE_KMZ_DEFAULT_FILENAME,
    kml_filename: str = PRIVATE_KMZ_KML_FILENAME,
) -> PrivateKmzWriteResult:
    """Write a private filesystem-only KMZ point overlay under ``run_dir``."""

    normalized_points = tuple(_validate_kmz_point(point) for point in points)
    if not normalized_points:
        raise ValueError("private KMZ requires at least one point")

    _validate_kml_filename(kml_filename)
    output_dir = resolve_run_output_path(run_dir, output_relative_dir)
    output_path = resolve_run_output_path(run_dir, Path(output_relative_dir) / filename)
    if output_path.suffix.lower() != ".kmz":
        raise ValueError("private KMZ filename must end with .kmz")

    output_dir.mkdir(parents=True, exist_ok=True)
    kml_payload = _build_private_points_kml(normalized_points)
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(kml_filename, kml_payload)

    artifact_metadata: dict[str, object] = {
        "artifact_type": "KMZ",
        "artifact_class": "FILESYSTEM_ONLY",
        "private_classification": "PRIVATE_COORDINATE_ARTIFACT",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "point_count": len(normalized_points),
        "kml_filename": kml_filename,
        "local_path": str(output_path),
    }
    redacted_summary: dict[str, object] = {
        "artifact_type": "KMZ",
        "point_count": len(normalized_points),
        "private_classification": "PRIVATE_COORDINATE_ARTIFACT",
        "artifact_class": "FILESYSTEM_ONLY",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
    }
    return PrivateKmzWriteResult(
        private_path=output_path,
        artifact_metadata=artifact_metadata,
        redacted_summary=redacted_summary,
    )


def _validate_feature(feature: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(feature, Mapping) or feature.get("type") != "Feature":
        raise ValueError("private GeoJSON payload entries must be GeoJSON Feature objects")

    properties = feature.get("properties")
    if not isinstance(properties, Mapping):
        raise ValueError("private GeoJSON Feature properties must be an object")

    geometry = feature.get("geometry")
    if not isinstance(geometry, Mapping):
        raise ValueError("private GeoJSON Feature geometry must be an object")
    geometry_type = geometry.get("type")
    if not isinstance(geometry_type, str) or not geometry_type:
        raise ValueError("private GeoJSON Feature geometry type must be a non-empty string")
    if "coordinates" not in geometry:
        raise ValueError("private GeoJSON Feature geometry must include coordinates")
    _validate_coordinates(geometry["coordinates"])

    return {
        "type": "Feature",
        "properties": dict(properties),
        "geometry": dict(geometry),
    }


def _validate_coordinates(value: Any) -> None:
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError("private GeoJSON coordinates must be numeric arrays")
    if isinstance(value, (int, float)):
        return
    if not isinstance(value, Iterable):
        raise ValueError("private GeoJSON coordinates must be numeric arrays")

    items = tuple(value)
    if not items:
        raise ValueError("private GeoJSON coordinates must not be empty")
    for item in items:
        _validate_coordinates(item)


def _validate_kmz_point(point: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(point, Mapping):
        raise ValueError("private KMZ points must be objects")

    raw_name = point.get("id", point.get("name"))
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise ValueError("private KMZ points require an id or name")

    latitude = _validate_lat_lon(point.get("latitude"), "latitude", -90.0, 90.0)
    longitude = _validate_lat_lon(point.get("longitude"), "longitude", -180.0, 180.0)
    normalized: dict[str, object] = {
        "name": raw_name.strip(),
        "latitude": latitude,
        "longitude": longitude,
    }

    description = point.get("description")
    if description is not None:
        if not isinstance(description, str):
            raise ValueError("private KMZ point description must be a string")
        normalized["description"] = description

    class_label = point.get("class_label")
    if class_label is not None:
        if not isinstance(class_label, str) or not class_label.startswith("Class_"):
            raise ValueError("private KMZ class_label must use neutral Class_* labels")
        normalized["class_label"] = class_label

    for key in ("score", "probability", "uncertainty", "rank"):
        if key in point:
            value = point[key]
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"private KMZ {key} must be a finite number")
            normalized[key] = float(value)

    return normalized


def _validate_lat_lon(
    value: object,
    field_name: str,
    minimum: float,
    maximum: float,
) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"private KMZ point {field_name} must be numeric")
    numeric_value = float(value)
    if numeric_value < minimum or numeric_value > maximum:
        raise ValueError(f"private KMZ point {field_name} is outside the allowed range")
    return numeric_value


def _validate_kml_filename(kml_filename: str) -> None:
    if not isinstance(kml_filename, str) or not kml_filename.strip():
        raise ValueError("private KMZ KML filename must be a non-empty string")
    candidate = Path(kml_filename)
    if candidate.name != kml_filename or candidate.suffix.lower() != ".kml":
        raise ValueError("private KMZ KML filename must be a simple .kml file name")


def _build_private_points_kml(points: Iterable[Mapping[str, object]]) -> str:
    placemarks = "\n".join(_build_private_point_placemark(point) for point in points)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        "    <name>Private KMZ point overlay</name>\n"
        f"{placemarks}\n"
        "  </Document>\n"
        "</kml>\n"
    )


def _build_private_point_placemark(point: Mapping[str, object]) -> str:
    name = xml_escape(str(point["name"]))
    description_lines = []
    for key in ("description", "class_label", "score", "probability", "uncertainty", "rank"):
        if key in point:
            description_lines.append(f"{key}: {point[key]}")
    description = xml_escape("\n".join(description_lines))
    longitude = float(point["longitude"])
    latitude = float(point["latitude"])
    return (
        "    <Placemark>\n"
        f"      <name>{name}</name>\n"
        f"      <description>{description}</description>\n"
        "      <Point>\n"
        f"        <coordinates>{longitude:.12g},{latitude:.12g},0</coordinates>\n"
        "      </Point>\n"
        "    </Placemark>"
    )
