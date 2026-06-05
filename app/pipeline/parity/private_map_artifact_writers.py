from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.pipeline.parity import resolve_run_output_path


PRIVATE_GEOJSON_DEFAULT_OUTPUT_DIR = "private_map_artifacts/geojson"
PRIVATE_GEOJSON_DEFAULT_FILENAME = "private_features.geojson"


@dataclass(frozen=True)
class PrivateGeoJsonWriteResult:
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
