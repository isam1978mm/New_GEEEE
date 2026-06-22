from __future__ import annotations

import pytest

from app.services.grid import build_grid_manifest
from app.services.roi_contract import (
    ROI_CONTRACT_SCHEMA,
    build_run_roi_contract,
    build_run_roi_contract_from_grid_manifest,
)


def test_roi_contract_contains_notebook_point_roi_and_grid_contract() -> None:
    lat = 35.59499
    lon = 36.12694
    grid = build_grid_manifest(lat, lon)

    contract = build_run_roi_contract(latitude=lat, longitude=lon, grid_manifest=grid)

    assert contract["schema"] == ROI_CONTRACT_SCHEMA
    assert contract["source_notebook_inventory"] == {
        "map_point_picker_roi": "Phase B cells 9-13",
        "run_folder_grid_manifest": "Phase C cell 14",
    }
    assert contract["selected_point"]["crs"] == "EPSG:4326"
    assert contract["selected_point"]["latitude"] == pytest.approx(lat)
    assert contract["selected_point"]["longitude"] == pytest.approx(lon)
    assert contract["selected_point"]["utm"]["crs"] == f"EPSG:{grid.epsg}"

    assert contract["roi_15km_wgs84_approx"]["side_length_km"] == pytest.approx(15.0)
    assert len(contract["roi_15km_wgs84_approx"]["coordinates_lon_lat"]) == 5
    assert contract["roi_15km_wgs84_approx"]["coordinates_lon_lat"][0] == contract["roi_15km_wgs84_approx"]["coordinates_lon_lat"][-1]

    roi_utm = contract["roi_6_4km_utm"]
    assert roi_utm["crs"] == f"EPSG:{grid.epsg}"
    assert roi_utm["side_length_m"] == pytest.approx(6400.0)
    assert roi_utm["bounds_m"] == grid.bounds_m
    assert len(roi_utm["coordinates_xy_m"]) == 5
    assert roi_utm["coordinates_xy_m"][0] == roi_utm["coordinates_xy_m"][-1]

    assert contract["grid"] == {
        "crs": f"EPSG:{grid.epsg}",
        "epsg": grid.epsg,
        "utm_zone": grid.utm_zone,
        "hemisphere": grid.hemisphere,
        "scale_m": grid.scale_m,
        "size_px": grid.size_px,
        "crs_transform": grid.crs_transform,
        "bounds_m": grid.bounds_m,
    }
    assert contract["notebook_grid_dict"] == {
        "CRS": f"EPSG:{grid.epsg}",
        "SCALE": float(grid.scale_m),
        "OUT_SIZE": grid.size_px,
        "crsTransform": grid.crs_transform,
        "bounds_utm": [
            grid.bounds_m["xmin"],
            grid.bounds_m["ymin"],
            grid.bounds_m["xmax"],
            grid.bounds_m["ymax"],
        ],
    }
    assert contract["privacy"] == {
        "artifact_class": "LOCAL_SENSITIVE",
        "public_api_exposure": "forbidden",
        "operator_output_listing": "forbidden",
    }


def test_roi_contract_can_be_rebuilt_from_authoritative_grid_manifest() -> None:
    grid = build_grid_manifest(35.59499, 36.12694)

    contract = build_run_roi_contract_from_grid_manifest(grid_manifest=grid)

    assert contract["grid"]["crs_transform"] == grid.crs_transform
    assert contract["grid"]["bounds_m"] == grid.bounds_m
    assert contract["notebook_grid_dict"]["bounds_utm"] == [
        grid.bounds_m["xmin"],
        grid.bounds_m["ymin"],
        grid.bounds_m["xmax"],
        grid.bounds_m["ymax"],
    ]
    assert contract["selected_point"]["latitude"] == pytest.approx(35.59499, abs=1e-8)
    assert contract["selected_point"]["longitude"] == pytest.approx(36.12694, abs=1e-8)
