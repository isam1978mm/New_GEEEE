"""Compatibility entry point for CDL years without the cultivated band.

The USDA/NASS CDL collection currently exposes only the ``cropland`` band for
2024, while earlier supported years can also expose ``cultivated``.  The base
context auditor selected both bands unconditionally and therefore failed before
Dynamic World or context decisions could run.

This wrapper replaces only the CDL-year query.  Missing ``cultivated`` data is
reported as unavailable and is never interpreted as non-cultivated.  All
context thresholds, candidate gates, records flags, and depth protections stay
unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_icesat2_candidate_gee_context as base


def _selected_cdl_bands(values: object) -> tuple[list[str], bool]:
    """Return safe CDL selectors and whether cultivated is available."""

    if not isinstance(values, list):
        raise ValueError("CDL image bandNames response must be a list")
    names = {str(value) for value in values}
    if "cropland" not in names:
        raise ValueError("CDL image is missing required cropland band")
    cultivated_available = "cultivated" in names
    selected = ["cropland"]
    if cultivated_available:
        selected.append("cultivated")
    return selected, cultivated_available


def _query_cdl_year(ee, *, geometry, point, year: int) -> dict[str, Any]:
    collection = ee.ImageCollection(base.CDL_COLLECTION).filterDate(
        f"{year}-01-01", f"{year + 1}-01-01"
    )
    count = int(collection.size().getInfo() or 0)
    if count <= 0:
        return {"year": year, "status": "cdl_year_unavailable"}

    image = ee.Image(collection.first())
    raw_band_names = image.bandNames().getInfo()
    selected_bands, cultivated_available = _selected_cdl_bands(raw_band_names)
    available_bands = sorted({str(value) for value in raw_band_names})

    property_names = [
        "cropland_class_values",
        "cropland_class_names",
    ]
    if cultivated_available:
        property_names.extend(
            ["cultivated_class_values", "cultivated_class_names"]
        )
    properties = image.toDictionary(property_names).getInfo()
    properties = properties if isinstance(properties, dict) else {}

    cropland_names = base._class_name_map(
        properties.get("cropland_class_values"),
        properties.get("cropland_class_names"),
    )
    cultivated_names = (
        base._class_name_map(
            properties.get("cultivated_class_values"),
            properties.get("cultivated_class_names"),
        )
        if cultivated_available
        else {}
    )

    selected_image = image.select(selected_bands)
    point_values = selected_image.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point,
        scale=30,
        bestEffort=True,
        maxPixels=1_000_000,
    ).getInfo()
    point_values = point_values if isinstance(point_values, dict) else {}

    point_crop_value = point_values.get("cropland")
    point_cultivated_value = (
        point_values.get("cultivated") if cultivated_available else None
    )
    point_crop_key = (
        int(point_crop_value)
        if isinstance(point_crop_value, (int, float))
        else None
    )
    point_cultivated_key = (
        int(point_cultivated_value)
        if isinstance(point_cultivated_value, (int, float))
        else None
    )

    histograms = selected_image.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=geometry,
        scale=30,
        bestEffort=True,
        maxPixels=2_000_000,
    ).getInfo()
    histograms = histograms if isinstance(histograms, dict) else {}
    crop_rows = base._named_histogram(
        histograms.get("cropland"), cropland_names
    )
    cultivated_rows = (
        base._named_histogram(
            histograms.get("cultivated"), cultivated_names
        )
        if cultivated_available
        else []
    )

    return {
        "year": year,
        "status": "cdl_context_available",
        "source_collection": base.CDL_COLLECTION,
        "available_bands": available_bands,
        "cultivated_band_available": cultivated_available,
        "cultivated_band_interpretation": (
            "observed_from_provider_band"
            if cultivated_available
            else "unavailable_not_interpreted_as_non_cultivated"
        ),
        "point_cropland_value": point_crop_key,
        "point_cropland_name": (
            cropland_names.get(point_crop_key)
            if point_crop_key is not None
            else None
        ),
        "point_cultivated_value": point_cultivated_key,
        "point_cultivated_name": (
            cultivated_names.get(point_cultivated_key)
            if point_cultivated_key is not None
            else None
        ),
        "buffer_top_cropland_classes": crop_rows,
        "buffer_cultivated_classes": cultivated_rows,
        "buffer_cultivated_fraction": (
            base._cultivated_fraction(cultivated_rows)
            if cultivated_available
            else None
        ),
    }


base._query_cdl_year = _query_cdl_year


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
