from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from scripts.probe_tyrone_historical_naip import (
    CONTACT_SHEET_NAME,
    COLLECTION_ID,
    create_contact_sheet,
    parse_bbox,
    summarize_dates,
    timestamp_ms_to_date,
    validate_date,
    write_manifest,
)


def _ms(date_text: str) -> int:
    dt = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def test_parse_bbox_accepts_valid_values() -> None:
    assert parse_bbox("-108.5,32.6,-108.3,32.8") == (
        -108.5,
        32.6,
        -108.3,
        32.8,
    )


@pytest.mark.parametrize(
    "raw",
    [
        "-108.5,32.6,-108.3",
        "west,32.6,-108.3,32.8",
        "-108.3,32.6,-108.5,32.8",
        "-108.5,32.9,-108.3,32.8",
    ],
)
def test_parse_bbox_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_bbox(raw)


def test_validate_date_requires_iso_date() -> None:
    assert validate_date("2006-09-01") == "2006-09-01"
    with pytest.raises(ValueError):
        validate_date("09/01/2006")


def test_timestamp_and_year_summary() -> None:
    timestamps = [
        _ms("2005-06-01"),
        _ms("2005-07-01"),
        _ms("2009-08-15"),
        None,
        "bad",
    ]
    dates, counts = summarize_dates(timestamps)

    assert dates == ["2005-06-01", "2005-07-01", "2009-08-15"]
    assert counts == {2005: 2, 2009: 1}
    assert timestamp_ms_to_date("bad") is None


def test_create_contact_sheet_uses_available_year_images(tmp_path: Path) -> None:
    first = tmp_path / "2005.jpg"
    second = tmp_path / "2009.jpg"
    Image.new("RGB", (100, 80), "white").save(first)
    Image.new("RGB", (100, 80), "gray").save(second)

    output = tmp_path / CONTACT_SHEET_NAME
    create_contact_sheet(
        [
            {"year": 2005, "image_count": 3, "image": str(first)},
            {"year": 2009, "image_count": 2, "image": str(second)},
        ],
        output,
        cell_width=120,
    )

    assert output.exists()
    with Image.open(output) as image:
        assert image.width == 240
        assert image.height > 80


def test_write_manifest_keeps_geometry_gate_closed(tmp_path: Path) -> None:
    image = tmp_path / "tyrone_naip_2005.jpg"
    image.write_bytes(b"placeholder")
    manifest_path = write_manifest(
        output_dir=tmp_path,
        bbox=(-108.4, 32.6, -108.3, 32.7),
        start_date="2003-01-01",
        end_date="2013-01-01",
        ee_project="example-project",
        image_count=2,
        acquisition_dates=["2005-06-01", "2005-07-01"],
        image_ids=["a", "b"],
        year_counts={2005: 2},
        year_rows=[
            {"year": 2005, "image_count": 2, "image": str(image.resolve())}
        ],
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["status"] == "historical_naip_review_pack_created"
    assert payload["collection_id"] == COLLECTION_ID
    assert payload["year_counts"] == {"2005": 2}
    assert payload["coordinate_geometry_unblocked"] is False
    assert payload["numerical_depth_unlocked"] is False
    assert "thumbnail_url" not in payload["year_mosaics"][0]


def test_write_manifest_handles_no_available_imagery(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        output_dir=tmp_path,
        bbox=(-108.4, 32.6, -108.3, 32.7),
        start_date="2003-01-01",
        end_date="2013-01-01",
        ee_project=None,
        image_count=0,
        acquisition_dates=[],
        image_ids=[],
        year_counts={},
        year_rows=[],
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["status"] == "no_historical_naip_available_in_requested_period"
    assert payload["contact_sheet"] is None
