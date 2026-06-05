from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.pipeline.parity import ParityPathError
from app.pipeline.parity.private_map_artifact_writers import (
    write_private_geojson_feature_collection,
)
from app.services.redaction import verify_redacted


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
}


def _private_features() -> list[dict[str, object]]:
    return [
        {
            "type": "Feature",
            "properties": {"role": "operator_private_point", "rank": 1},
            "geometry": {"type": "Point", "coordinates": [36.12694, 35.59499]},
        },
        {
            "type": "Feature",
            "properties": {"role": "operator_private_area"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [36.12690, 35.59490],
                        [36.12700, 35.59490],
                        [36.12700, 35.59500],
                        [36.12690, 35.59500],
                        [36.12690, 35.59490],
                    ]
                ],
            },
        },
    ]


def test_valid_private_features_write_geojson_feature_collection_under_run_dir(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"

    result = write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=_private_features(),
        filename="operator_private_features.geojson",
    )

    private_path = result.private_path
    assert private_path.is_file()
    assert private_path.suffix == ".geojson"
    assert private_path.resolve().is_relative_to(run_dir.resolve())

    payload = json.loads(private_path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 2
    assert payload["features"][0]["geometry"]["coordinates"] == [36.12694, 35.59499]


def test_output_path_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    result = write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=_private_features(),
    )

    assert result.private_path.resolve().is_relative_to(run_dir.resolve())


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ParityPathError):
        write_private_geojson_feature_collection(
            run_dir=tmp_path / "run",
            features=_private_features(),
            output_relative_dir="../outside",
        )

    with pytest.raises(ParityPathError):
        write_private_geojson_feature_collection(
            run_dir=tmp_path / "run",
            features=_private_features(),
            filename="../outside.geojson",
        )


def test_redacted_public_summary_contains_no_coordinates_geometry_or_paths(
    tmp_path: Path,
) -> None:
    result = write_private_geojson_feature_collection(
        run_dir=tmp_path / "run",
        features=_private_features(),
    )

    summary = result.redacted_summary

    verify_redacted(summary)
    serialized = json.dumps(summary, sort_keys=True).lower()
    assert "coordinates" not in serialized
    assert "geometry" not in serialized
    assert "36.12694" not in serialized
    assert "35.59499" not in serialized
    assert ".geojson" not in serialized
    assert str(tmp_path).lower() not in serialized


def test_artifact_metadata_is_private_filesystem_only(tmp_path: Path) -> None:
    result = write_private_geojson_feature_collection(
        run_dir=tmp_path / "run",
        features=_private_features(),
    )

    metadata = result.artifact_metadata
    assert metadata["artifact_type"] == "GeoJSON FeatureCollection"
    assert metadata["artifact_class"] == "FILESYSTEM_ONLY"
    assert metadata["private_classification"] == "PRIVATE_COORDINATE_ARTIFACT"
    assert metadata["filesystem_only"] is True
    assert metadata["http_servable"] is False
    assert metadata["frontend_visible"] is False
    assert metadata["downloadable_via_api"] is False


def test_invalid_feature_payload_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Feature"):
        write_private_geojson_feature_collection(
            run_dir=tmp_path / "run",
            features=[{"type": "Point", "coordinates": [36.0, 35.0]}],
        )

    with pytest.raises(ValueError, match="geometry"):
        write_private_geojson_feature_collection(
            run_dir=tmp_path / "run",
            features=[{"type": "Feature", "properties": {}}],
        )

    with pytest.raises(ValueError, match="properties"):
        write_private_geojson_feature_collection(
            run_dir=tmp_path / "run",
            features=[
                {
                    "type": "Feature",
                    "properties": [],
                    "geometry": {"type": "Point", "coordinates": [36.0, 35.0]},
                }
            ],
        )


def test_writer_creates_no_other_artifact_types(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=_private_features(),
    )

    forbidden = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]

    assert forbidden == []


def test_writer_creates_no_files_outside_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=_private_features(),
    )

    outside_files = [
        path
        for path in tmp_path.rglob("*")
        if path.is_file() and not path.resolve().is_relative_to(run_dir.resolve())
    ]

    assert outside_files == []


def test_phase_d_writer_adds_no_public_exposure_or_runtime_calls() -> None:
    import app.pipeline.parity.private_map_artifact_writers as module

    source = inspect.getsource(module)

    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
