from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts.export_tyrone_3x_historical_naip_geotiff import (
    MANIFEST_NAME,
    TARGET_CRS,
    GeotiffExportError,
    build_download_params,
    download_geotiff,
    inspect_geotiff,
    parse_years,
    write_manifest,
)


def test_parse_years_deduplicates_and_preserves_order() -> None:
    assert parse_years("2011, 2009,2011") == (2011, 2009)


@pytest.mark.parametrize("raw", ["", ",,", "year", "2001", "2101"])
def test_parse_years_rejects_invalid_input(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_years(raw)


def test_download_params_request_projected_single_rgb_geotiff() -> None:
    region = object()
    params = build_download_params(region=region, scale_m=1.0)
    assert params == {
        "bands": ["R", "G", "B"],
        "region": region,
        "crs": TARGET_CRS,
        "scale": 1.0,
        "format": "GEO_TIFF",
        "filePerBand": False,
    }


@pytest.mark.parametrize("scale", [0, -1, float("inf"), float("nan")])
def test_download_params_reject_invalid_scale(scale: float) -> None:
    with pytest.raises(ValueError):
        build_download_params(region=object(), scale_m=scale)


def _write_test_geotiff(path: Path, *, crs: str = TARGET_CRS, scale: float = 1.0) -> None:
    data = np.zeros((3, 12, 10), dtype=np.uint8)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=10,
        height=12,
        count=3,
        dtype="uint8",
        crs=crs,
        transform=from_origin(700000.0, 3620000.0, scale, scale),
    ) as dataset:
        dataset.write(data)


def test_inspect_geotiff_records_explicit_crs_transform_and_bounds(tmp_path: Path) -> None:
    path = tmp_path / "test.tif"
    _write_test_geotiff(path)
    row = inspect_geotiff(path, requested_scale_m=1.0)
    assert row["crs"] == TARGET_CRS
    assert row["width"] == 10
    assert row["height"] == 12
    assert row["band_count"] == 3
    assert row["pixel_size_m"] == {"x": 1.0, "y": 1.0}
    assert row["affine_transform"] == [1.0, 0.0, 700000.0, 0.0, -1.0, 3620000.0]
    assert row["bounds_m"] == {
        "left": 700000.0,
        "bottom": 3619988.0,
        "right": 700010.0,
        "top": 3620000.0,
    }


def test_inspect_geotiff_rejects_wrong_crs(tmp_path: Path) -> None:
    path = tmp_path / "wrong_crs.tif"
    _write_test_geotiff(path, crs="EPSG:32613")
    with pytest.raises(GeotiffExportError, match="CRS mismatch"):
        inspect_geotiff(path, requested_scale_m=1.0)


def test_inspect_geotiff_rejects_unexpected_resolution(tmp_path: Path) -> None:
    path = tmp_path / "wrong_scale.tif"
    _write_test_geotiff(path, scale=2.0)
    with pytest.raises(GeotiffExportError, match="unexpected x resolution"):
        inspect_geotiff(path, requested_scale_m=1.0)


def test_write_manifest_keeps_every_enablement_gate_closed(tmp_path: Path) -> None:
    export = {
        "year": 2009,
        "path": str((tmp_path / "2009.tif").resolve()),
        "crs": TARGET_CRS,
        "width": 100,
        "height": 100,
        "band_count": 3,
        "dtype": ["uint8", "uint8", "uint8"],
        "pixel_size_m": {"x": 1.0, "y": 1.0},
        "affine_transform": [1.0, 0.0, 700000.0, 0.0, -1.0, 3620000.0],
        "bounds_m": {
            "left": 700000.0,
            "bottom": 3619900.0,
            "right": 700100.0,
            "top": 3620000.0,
        },
        "source_image_count": 2,
    }
    path = write_manifest(
        output_dir=tmp_path,
        ee_project="example-project",
        scale_m=1.0,
        source_image_count=4,
        acquisition_dates=["2009-05-13", "2011-05-07"],
        source_image_ids=["a", "b"],
        requested_years=(2009, 2011),
        exports=[export],
    )
    assert path.name == MANIFEST_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "historical_naip_geotiffs_created"
    assert payload["target_crs"] == TARGET_CRS
    assert payload["coordinate_geometry_unblocked"] is False
    assert payload["earth_engine_depth_query_allowed"] is False
    assert payload["calibration_record_allowed"] is False
    assert payload["numerical_depth_unlocked"] is False


def test_download_geotiff_rejects_non_tiff_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b"not-a-tiff" * 1000

    monkeypatch.setattr(
        "scripts.export_tyrone_3x_historical_naip_geotiff.urlopen",
        lambda *_args, **_kwargs: Response(),
    )
    with pytest.raises(GeotiffExportError, match="not a TIFF"):
        download_geotiff("https://example.invalid/file", timeout_seconds=10)
