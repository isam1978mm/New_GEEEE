from __future__ import annotations

from pydantic import BaseModel, Field


class GridManifest(BaseModel):
    crs_family: str = "utm"
    epsg: int
    utm_zone: int
    hemisphere: str
    scale_m: int = 10
    size_px: int = 640
    crs_transform: list[float] = Field(default_factory=list)
    bounds_m: dict[str, float] = Field(default_factory=dict)


def build_grid_manifest(lat: float, lon: float) -> GridManifest:
    utm_zone = int((lon + 180) // 6) + 1
    utm_zone = max(1, min(60, utm_zone))
    hemisphere = "north" if lat >= 0 else "south"
    epsg = 32600 + utm_zone if hemisphere == "north" else 32700 + utm_zone
    scale_m = 10
    size_px = 640
    half_extent_m = (size_px * scale_m) / 2

    return GridManifest(
        epsg=epsg,
        utm_zone=utm_zone,
        hemisphere=hemisphere,
        scale_m=scale_m,
        size_px=size_px,
        crs_transform=[scale_m, 0.0, -half_extent_m, 0.0, -scale_m, half_extent_m],
        bounds_m={
            "xmin": -half_extent_m,
            "ymin": -half_extent_m,
            "xmax": half_extent_m,
            "ymax": half_extent_m,
        },
    )
