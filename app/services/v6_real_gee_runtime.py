"""V6 real-generation runtime boundary and AOI/grid helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import importlib
import math
from typing import Any


@dataclass(frozen=True)
class V6AoiBounds:
    west: float
    south: float
    east: float
    north: float

    @property
    def width_degrees(self) -> float:
        return self.east - self.west

    @property
    def height_degrees(self) -> float:
        return self.north - self.south

    def safe_summary(self) -> dict[str, Any]:
        return {
            "aoi_kind": "bbox",
            "bounds_values_redacted": True,
            "width_degrees": round(self.width_degrees, 6),
            "height_degrees": round(self.height_degrees, 6),
        }


@dataclass(frozen=True)
class V6GridConfig:
    rows: int
    cols: int

    def __post_init__(self) -> None:
        if isinstance(self.rows, bool) or isinstance(self.cols, bool):
            raise ValueError("grid rows and cols must be positive integers")
        if not isinstance(self.rows, int) or not isinstance(self.cols, int):
            raise ValueError("grid rows and cols must be positive integers")
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("grid rows and cols must be positive integers")


@dataclass(frozen=True)
class V6GridCell:
    cell_id: str
    row: int
    col: int
    bounds: V6AoiBounds

    def safe_summary(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "row": self.row,
            "col": self.col,
            "bounds_values_redacted": True,
        }


@dataclass(frozen=True)
class V6RuntimeConfig:
    project_id: str | None = None
    allow_interactive_auth: bool = False


class V6EarthEngineRuntime:
    """Lazy runtime adapter.

    The external library is imported only when initialize() is called. Unit tests
    can inject a fake module and never call the real service.
    """

    def __init__(self, config: V6RuntimeConfig | None = None, *, ee_module: Any | None = None) -> None:
        self.config = config or V6RuntimeConfig()
        self._ee_module = ee_module
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> Any:
        if self.config.allow_interactive_auth:
            raise ValueError("interactive Earth Engine authentication is not allowed in app runtime")
        ee = self._ee_module or importlib.import_module("ee")
        if self.config.project_id:
            ee.Initialize(project=self.config.project_id)
        else:
            ee.Initialize()
        self._initialized = True
        return ee

    def rectangle_geometry(self, aoi: V6AoiBounds) -> Any:
        ee = self.initialize()
        return ee.Geometry.Rectangle(
            [aoi.west, aoi.south, aoi.east, aoi.north],
            proj=None,
            geodesic=False,
        )


def v6_aoi_from_mapping(payload: Mapping[str, Any]) -> V6AoiBounds:
    if "bbox" in payload:
        bbox = payload["bbox"]
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("bbox must contain four numeric values")
        west, south, east, north = bbox
    else:
        try:
            west = payload["west"]
            south = payload["south"]
            east = payload["east"]
            north = payload["north"]
        except KeyError as exc:
            raise ValueError("AOI requires west, south, east, north or bbox") from exc
    return validate_v6_aoi_bounds(west=west, south=south, east=east, north=north)


def validate_v6_aoi_bounds(*, west: object, south: object, east: object, north: object) -> V6AoiBounds:
    west_f = _finite_float(west, "west")
    south_f = _finite_float(south, "south")
    east_f = _finite_float(east, "east")
    north_f = _finite_float(north, "north")

    if not -180 <= west_f <= 180 or not -180 <= east_f <= 180:
        raise ValueError("AOI longitude bounds are outside the supported range")
    if not -90 <= south_f <= 90 or not -90 <= north_f <= 90:
        raise ValueError("AOI latitude bounds are outside the supported range")
    if west_f >= east_f:
        raise ValueError("AOI west must be less than east")
    if south_f >= north_f:
        raise ValueError("AOI south must be less than north")

    return V6AoiBounds(west=west_f, south=south_f, east=east_f, north=north_f)


def build_v6_grid(*, aoi: V6AoiBounds, config: V6GridConfig) -> tuple[V6GridCell, ...]:
    cell_width = aoi.width_degrees / config.cols
    cell_height = aoi.height_degrees / config.rows
    cells: list[V6GridCell] = []

    for row in range(config.rows):
        for col in range(config.cols):
            cells.append(
                V6GridCell(
                    cell_id=f"V6_CELL_R{row + 1:03d}_C{col + 1:03d}",
                    row=row + 1,
                    col=col + 1,
                    bounds=V6AoiBounds(
                        west=aoi.west + (col * cell_width),
                        south=aoi.south + (row * cell_height),
                        east=aoi.west + ((col + 1) * cell_width),
                        north=aoi.south + ((row + 1) * cell_height),
                    ),
                )
            )

    return tuple(cells)


def safe_grid_summary(cells: tuple[V6GridCell, ...]) -> dict[str, Any]:
    return {
        "cell_count": len(cells),
        "bounds_values_redacted": True,
        "first_cell_id": cells[0].cell_id if cells else None,
        "last_cell_id": cells[-1].cell_id if cells else None,
    }


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number
