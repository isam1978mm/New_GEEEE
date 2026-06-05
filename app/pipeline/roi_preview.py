from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.grid import build_grid_manifest


class SelectedPointPreview(BaseModel):
    north_south_degrees: float
    east_west_degrees: float


class RoiWindowPreview(BaseModel):
    west_meters: float
    south_meters: float
    east_meters: float
    north_meters: float
    width_meters: float
    height_meters: float


class GridPreview(BaseModel):
    reference_system_label: str
    reference_code_value: int
    zone_number: int
    hemisphere: str
    width_cells: int
    height_cells: int
    cell_size_meters: int
    affine_coefficients: list[float] = Field(default_factory=list)


class RoiGridPreview(BaseModel):
    mode: str = "point"
    selected_point_preview: SelectedPointPreview
    roi_window_preview: RoiWindowPreview
    grid_preview: GridPreview
    warnings: list[str] = Field(default_factory=list)


def build_roi_grid_preview(*, latitude: Any, longitude: Any) -> RoiGridPreview:
    north_south = _coerce_coordinate(latitude, minimum=-90.0, maximum=90.0, label="latitude")
    east_west = _coerce_coordinate(longitude, minimum=-180.0, maximum=180.0, label="longitude")
    grid = build_grid_manifest(north_south, east_west)
    window = grid.bounds_m
    width_meters = float(window["xmax"]) - float(window["xmin"])
    height_meters = float(window["ymax"]) - float(window["ymin"])

    return RoiGridPreview(
        selected_point_preview=SelectedPointPreview(
            north_south_degrees=north_south,
            east_west_degrees=east_west,
        ),
        roi_window_preview=RoiWindowPreview(
            west_meters=float(window["xmin"]),
            south_meters=float(window["ymin"]),
            east_meters=float(window["xmax"]),
            north_meters=float(window["ymax"]),
            width_meters=width_meters,
            height_meters=height_meters,
        ),
        grid_preview=GridPreview(
            reference_system_label=f"EPSG:{grid.epsg}",
            reference_code_value=grid.epsg,
            zone_number=grid.utm_zone,
            hemisphere=grid.hemisphere,
            width_cells=grid.size_px,
            height_cells=grid.size_px,
            cell_size_meters=grid.scale_m,
            affine_coefficients=list(grid.crs_transform),
        ),
        warnings=[
            "Preview uses deterministic local GRID metadata only; no Earth Engine request, run start, or file write occurs.",
        ],
    )


def _coerce_coordinate(value: Any, *, minimum: float, maximum: float, label: str) -> float:
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if coordinate < minimum or coordinate > maximum:
        raise ValueError(f"{label} is outside the allowed range.")
    return coordinate
