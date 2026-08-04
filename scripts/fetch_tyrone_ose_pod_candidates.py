#!/usr/bin/env python3
"""Fetch official NMOSE points of diversion near the Tyrone Mine.

This script supports the Tyrone Route B georeferencing investigation. It queries
New Mexico Office of the State Engineer public POD data, preserves the published
coordinate-quality fields, and ranks records that may match well labels visible
on the 2007/2020 Tyrone mine maps.

It does not georeference Test Plots 5 or 6 and does not unlock numerical depth.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SERVICE_URL = (
    "https://services2.arcgis.com/qXZbWTdPDbTjl7Dy/arcgis/rest/services/"
    "OSE_Points_of_Diversion/FeatureServer/0/query"
)

DEFAULT_BBOX = (-108.50, 32.55, -108.25, 32.75)
DEFAULT_TIMEOUT_SECONDS = 90

OUT_FIELDS = [
    "OBJECTID",
    "pod_name",
    "pod_file",
    "well_tag",
    "other_loc",
    "easting",
    "northing",
    "utm_zone",
    "datum",
    "utm_accuracy",
    "xy_accuracy",
    "own_lname",
    "own_fname",
    "nmwrrs_wrsum_url",
]

MAP_LABEL_HINTS = (
    "27-2005-05",
    "27-2005-04",
    "27-2005-03",
    "27-2005-06",
    "27-2004-01",
    "MVR-2",
    "P2-4",
    "P2-6",
)

OWNER_HINTS = (
    "freeport",
    "phelps",
    "tyrone",
    "fmi",
)


@dataclass(frozen=True)
class BBox:
    west: float
    south: float
    east: float
    north: float

    def validate(self) -> None:
        if not (-180 <= self.west < self.east <= 180):
            raise ValueError("bbox west/east values are invalid")
        if not (-90 <= self.south < self.north <= 90):
            raise ValueError("bbox south/north values are invalid")

    def as_arcgis_envelope(self) -> str:
        self.validate()
        return f"{self.west},{self.south},{self.east},{self.north}"


class PodFetchError(RuntimeError):
    """Raised when the public POD service cannot provide a valid response."""


def parse_bbox(raw: str) -> BBox:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be west,south,east,north")
    try:
        bbox = BBox(*(float(part) for part in parts))
    except ValueError as exc:
        raise ValueError("bbox values must be numeric") from exc
    bbox.validate()
    return bbox


def build_query_params(bbox: BBox) -> dict[str, str]:
    return {
        "where": "1=1",
        "geometry": bbox.as_arcgis_envelope(),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join(OUT_FIELDS),
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": "2000",
        "f": "json",
    }


def fetch_payload(
    *,
    service_url: str,
    params: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    url = f"{service_url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "New-GEE-Tyrone-Route-B/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            raw = response.read()
    except Exception as exc:  # pragma: no cover - exercised by local runtime
        raise PodFetchError(f"NMOSE POD request failed: {exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PodFetchError("NMOSE POD response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise PodFetchError("NMOSE POD response must be a JSON object")
    if "error" in payload:
        error = payload.get("error")
        raise PodFetchError(f"NMOSE POD service returned an error: {error}")
    if not isinstance(payload.get("features"), list):
        raise PodFetchError("NMOSE POD response did not contain a feature list")
    return payload


def _combined_text(attributes: dict[str, Any]) -> str:
    values = []
    for key in (
        "pod_name",
        "pod_file",
        "well_tag",
        "other_loc",
        "own_lname",
        "own_fname",
    ):
        value = attributes.get(key)
        if value not in (None, ""):
            values.append(str(value))
    return " | ".join(values).lower()


def score_candidate(attributes: dict[str, Any]) -> tuple[int, list[str]]:
    text = _combined_text(attributes)
    score = 0
    reasons: list[str] = []

    for label in MAP_LABEL_HINTS:
        if label.lower() in text:
            score += 100
            reasons.append(f"map_label:{label}")

    for owner in OWNER_HINTS:
        if owner in text:
            score += 25
            reasons.append(f"owner_or_location:{owner}")

    if attributes.get("easting") not in (None, ""):
        score += 5
        reasons.append("published_easting")
    if attributes.get("northing") not in (None, ""):
        score += 5
        reasons.append("published_northing")
    if attributes.get("datum") not in (None, ""):
        score += 3
        reasons.append("published_datum")
    if attributes.get("utm_accuracy") not in (None, ""):
        score += 2
        reasons.append("published_utm_accuracy")
    if attributes.get("xy_accuracy") not in (None, ""):
        score += 2
        reasons.append("published_xy_accuracy")

    return score, reasons


def normalize_feature(feature: dict[str, Any]) -> dict[str, Any]:
    attributes = feature.get("attributes")
    geometry = feature.get("geometry")
    if not isinstance(attributes, dict):
        attributes = {}
    if not isinstance(geometry, dict):
        geometry = {}

    score, reasons = score_candidate(attributes)
    return {
        "priority_score": score,
        "priority_reasons": reasons,
        "longitude": geometry.get("x"),
        "latitude": geometry.get("y"),
        **{field: attributes.get(field) for field in OUT_FIELDS},
    }


def normalize_features(features: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [normalize_feature(feature) for feature in features]
    rows.sort(
        key=lambda row: (
            -(row.get("priority_score") or 0),
            str(row.get("pod_name") or ""),
            str(row.get("OBJECTID") or ""),
        )
    )
    return rows


def write_outputs(
    *,
    output_dir: Path,
    bbox: BBox,
    service_url: str,
    payload: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "tyrone_ose_pod_candidates.json"
    csv_path = output_dir / "tyrone_ose_pod_candidates.csv"

    report = {
        "schema": "tyrone_ose_pod_candidates_v1",
        "status": "official_pod_candidates_downloaded",
        "source": "New Mexico Office of the State Engineer Points of Diversion",
        "service_url": service_url,
        "bbox_wgs84": {
            "west": bbox.west,
            "south": bbox.south,
            "east": bbox.east,
            "north": bbox.north,
        },
        "feature_count": len(rows),
        "exceeded_transfer_limit": bool(payload.get("exceededTransferLimit")),
        "candidates": rows,
        "does_not_prove": [
            "that an OSE point is the same well shown on the Tyrone map",
            "the Tyrone local-grid to UTM transformation",
            "coordinate-tied TP5 or TP6 geometry",
            "stable Sentinel-1 calibration geometry",
            "numerical depth readiness",
        ],
        "next_gate": (
            "Match at least six named map wells to high-quality official POD points, "
            "reserve at least two additional matches as independent check points, "
            "then fit and audit the local-grid to UTM transformation."
        ),
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    columns = [
        "priority_score",
        "priority_reasons",
        "pod_name",
        "pod_file",
        "well_tag",
        "other_loc",
        "own_lname",
        "own_fname",
        "longitude",
        "latitude",
        "easting",
        "northing",
        "utm_zone",
        "datum",
        "utm_accuracy",
        "xy_accuracy",
        "nmwrrs_wrsum_url",
        "OBJECTID",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["priority_reasons"] = ";".join(row.get("priority_reasons") or [])
            writer.writerow(csv_row)

    return json_path, csv_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch official NMOSE POD candidates for Tyrone Route B."
    )
    parser.add_argument(
        "--bbox",
        default=",".join(str(value) for value in DEFAULT_BBOX),
        help="WGS84 west,south,east,north search envelope.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for JSON and CSV output.",
    )
    parser.add_argument(
        "--service-url",
        default=SERVICE_URL,
        help="ArcGIS FeatureServer layer query endpoint.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        bbox = parse_bbox(args.bbox)
        if args.timeout_seconds <= 0:
            raise ValueError("timeout-seconds must be positive")
        params = build_query_params(bbox)
        payload = fetch_payload(
            service_url=args.service_url,
            params=params,
            timeout_seconds=args.timeout_seconds,
        )
        rows = normalize_features(payload["features"])
        json_path, csv_path = write_outputs(
            output_dir=args.output_dir,
            bbox=bbox,
            service_url=args.service_url,
            payload=payload,
            rows=rows,
        )
    except (ValueError, PodFetchError, OSError) as exc:
        print(
            json.dumps(
                {
                    "status": "official_pod_candidate_fetch_failed",
                    "error": str(exc),
                    "coordinate_geometry_unblocked": False,
                    "numerical_depth_unlocked": False,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "status": "official_pod_candidates_downloaded",
                "feature_count": len(rows),
                "json": str(json_path.resolve()),
                "csv": str(csv_path.resolve()),
                "coordinate_geometry_unblocked": False,
                "numerical_depth_unlocked": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
