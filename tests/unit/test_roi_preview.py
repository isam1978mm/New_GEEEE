from __future__ import annotations

import inspect

import pytest

from app.pipeline.roi_preview import build_roi_grid_preview
from app.services.redaction import verify_redacted


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
}


def test_valid_lat_lon_returns_preview_metadata() -> None:
    preview = build_roi_grid_preview(latitude=35.59499, longitude=36.12694).model_dump()

    assert preview["mode"] == "point"
    assert preview["selected_point_preview"] == {
        "north_south_degrees": pytest.approx(35.59499),
        "east_west_degrees": pytest.approx(36.12694),
    }
    assert preview["roi_window_preview"]["width_meters"] == pytest.approx(6400.0)
    assert preview["roi_window_preview"]["height_meters"] == pytest.approx(6400.0)
    assert preview["grid_preview"]["width_cells"] == 640
    assert preview["grid_preview"]["height_cells"] == 640
    assert preview["grid_preview"]["cell_size_meters"] == 10
    assert preview["grid_preview"]["reference_system_label"].startswith("EPSG:")
    assert len(preview["grid_preview"]["affine_coefficients"]) == 6
    assert preview["warnings"]
    verify_redacted(preview)


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (91.0, 36.0),
        (-91.0, 36.0),
        (35.0, 181.0),
        (35.0, -181.0),
    ],
)
def test_invalid_coordinate_ranges_are_rejected(latitude: float, longitude: float) -> None:
    with pytest.raises(ValueError):
        build_roi_grid_preview(latitude=latitude, longitude=longitude)


def test_nonnumeric_coordinates_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_roi_grid_preview(latitude="north", longitude=36.0)  # type: ignore[arg-type]


def test_preview_does_not_create_artifacts(tmp_path) -> None:
    build_roi_grid_preview(latitude=35.59499, longitude=36.12694)

    created_artifacts = [
        path
        for path in tmp_path.rglob("*")
        if path.suffix.casefold() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created_artifacts == []


def test_preview_module_does_not_import_or_call_earth_engine() -> None:
    import app.pipeline.roi_preview as roi_preview

    source = inspect.getsource(roi_preview).casefold()
    assert "import ee" not in source
    assert "earthengine" not in source
    assert "ee." not in source
    assert "authenticate" not in source
