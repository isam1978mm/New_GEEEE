"""Probe the two Campaign 014 problem passes against the official EPA-site envelope.

This Campaign-014-only diagnostic loads the already cached official EPA Hidden
Lane Landfill GeoJSON produced by the approved scanner, computes the tight WGS84
bounding box of the retained EPA polygon geometry, then calls OpenAltimetry's
public ``getTracks`` and ATL08 endpoints for the two SlideRule-problem passes.

The purpose is to distinguish a track that only intersects the broad Campaign
014 search box from one that also intersects the much smaller official EPA-site
envelope.  Envelope intersection is still not claimed to be exact polygon
intersection.  No scientific threshold, source/event gate, finalizer, generic
scanner, application behavior, or other campaign is changed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
REGION_ID = "epa_hidden_lane_landfill_recent_ou3_earthwork"
CAMPAIGN_DIR = Path("data") / "research" / "icesat2_broad_track_scan" / CAMPAIGN_ID
DEFAULT_EPA_GEOJSON = CAMPAIGN_DIR / REGION_ID / "epa_hidden_lane_superfund_boundary.geojson"
DEFAULT_OUTPUT_DIR = CAMPAIGN_DIR / "openaltimetry_epa_envelope_probe"
GET_TRACKS_URL = "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/getTracks"
ATL08_URL = "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/atl08"
TARGETS = (
    {
        "resource": "ATL08_20210504235905_06291102_007_01.h5",
        "date": "2021-05-04",
        "track_id": 629,
    },
    {
        "resource": "ATL08_20251226145703_01873002_007_01.h5",
        "date": "2025-12-26",
        "track_id": 187,
    },
)


class Campaign014EPAEnvelopeProbeError(RuntimeError):
    pass


def _iter_coordinate_pairs(value: Any):
    if isinstance(value, (list, tuple)):
        if (
            len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            lon = float(value[0])
            lat = float(value[1])
            if math.isfinite(lon) and math.isfinite(lat):
                yield lon, lat
            return
        for child in value:
            yield from _iter_coordinate_pairs(child)


def epa_envelope(path: Path) -> tuple[float, float, float, float]:
    path = Path(path)
    if not path.is_file():
        raise Campaign014EPAEnvelopeProbeError(
            f"missing cached official EPA polygon: {path}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list) or not features:
        raise Campaign014EPAEnvelopeProbeError("cached EPA GeoJSON has no features")

    points: list[tuple[float, float]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        points.extend(_iter_coordinate_pairs(geometry.get("coordinates")))
    if len(points) < 3:
        raise Campaign014EPAEnvelopeProbeError(
            "cached EPA GeoJSON has insufficient polygon coordinates"
        )
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def _fetch(url: str, *, timeout_seconds: float) -> tuple[int, str, bytes]:
    request = Request(url, headers={"User-Agent": "New_GEEEE-Campaign014/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed NASA HTTPS endpoints
        return (
            int(getattr(response, "status", 200)),
            str(response.headers.get("Content-Type", "")),
            response.read(),
        )


def _track_ids(value: Any) -> list[int]:
    found: set[int] = set()

    def visit(item: Any, parent_key: str | None = None) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                key_text = str(key).lower()
                if key_text in {"track", "trackid", "rgt", "rgt_id"}:
                    try:
                        parsed = int(child)
                    except (TypeError, ValueError):
                        pass
                    else:
                        if parsed >= 0:
                            found.add(parsed)
                visit(child, key_text)
        elif isinstance(item, list):
            for child in item:
                visit(child, parent_key)
        elif parent_key in {"track", "trackid", "rgt", "rgt_id"}:
            try:
                parsed = int(item)
            except (TypeError, ValueError):
                return
            if parsed >= 0:
                found.add(parsed)

    visit(value)
    return sorted(found)


def _atl08_counts(payload: Any) -> tuple[int, int, int | None]:
    if not isinstance(payload, dict):
        return 0, 0, None
    series = payload.get("series")
    if not isinstance(series, list):
        series = []
    point_count = 0
    for item in series:
        if not isinstance(item, dict):
            continue
        rows = item.get("lat_lon_elev_canopy")
        if isinstance(rows, list):
            point_count += len(rows)
    track_value = payload.get("trackId")
    try:
        returned_track = int(track_value)
    except (TypeError, ValueError):
        returned_track = None
    return len(series), point_count, returned_track


def _bbox_params(
    *,
    date: str,
    bounds: tuple[float, float, float, float],
) -> dict[str, str]:
    west, south, east, north = bounds
    return {
        "date": date,
        "minx": f"{west:.8f}",
        "miny": f"{south:.8f}",
        "maxx": f"{east:.8f}",
        "maxy": f"{north:.8f}",
        "outputFormat": "json",
    }


def probe_target(
    target: dict[str, Any],
    *,
    bounds: tuple[float, float, float, float],
    output_dir: Path,
    timeout_seconds: float,
    fetch=_fetch,
) -> dict[str, Any]:
    track_params = _bbox_params(date=str(target["date"]), bounds=bounds)
    track_url = GET_TRACKS_URL + "?" + urlencode(track_params)
    track_status, track_content_type, track_body = fetch(
        track_url, timeout_seconds=timeout_seconds
    )
    try:
        track_payload = json.loads(track_body)
    except json.JSONDecodeError as exc:
        raise Campaign014EPAEnvelopeProbeError(
            f"OpenAltimetry getTracks returned invalid JSON for {target['date']}: {exc}"
        ) from exc
    track_ids = _track_ids(track_payload)
    target_present = int(target["track_id"]) in track_ids

    atl08_params = dict(track_params)
    atl08_params["trackId"] = str(int(target["track_id"]))
    atl08_params["client"] = "campaign014"
    atl08_url = ATL08_URL + "?" + urlencode(atl08_params)
    atl08_status, atl08_content_type, atl08_body = fetch(
        atl08_url, timeout_seconds=timeout_seconds
    )
    try:
        atl08_payload = json.loads(atl08_body)
    except json.JSONDecodeError as exc:
        raise Campaign014EPAEnvelopeProbeError(
            f"OpenAltimetry ATL08 returned invalid JSON for {target['date']}: {exc}"
        ) from exc
    series_count, point_count, returned_track = _atl08_counts(atl08_payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    track_path = output_dir / f"tracks_{target['date']}.json"
    atl08_path = output_dir / f"atl08_{target['date']}_rgt{int(target['track_id']):04d}.json"
    track_path.write_bytes(track_body)
    atl08_path.write_bytes(atl08_body)

    if not target_present:
        decision = "target_track_absent_from_exact_epa_envelope"
    elif point_count > 0:
        decision = "target_track_and_atl08_present_in_exact_epa_envelope"
    else:
        decision = "target_track_crosses_exact_epa_envelope_but_atl08_unavailable"

    return {
        "resource": target["resource"],
        "date": target["date"],
        "target_track_id": int(target["track_id"]),
        "epa_envelope": {
            "west": bounds[0],
            "south": bounds[1],
            "east": bounds[2],
            "north": bounds[3],
        },
        "get_tracks_http_status": track_status,
        "get_tracks_content_type": track_content_type,
        "returned_track_ids": track_ids,
        "target_track_present": target_present,
        "atl08_http_status": atl08_status,
        "atl08_content_type": atl08_content_type,
        "atl08_returned_track_id": returned_track,
        "atl08_series_count": series_count,
        "atl08_point_count": point_count,
        "track_raw_path": str(track_path),
        "atl08_raw_path": str(atl08_path),
        "decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epa-geojson", type=Path, default=DEFAULT_EPA_GEOJSON)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        raise SystemExit("timeout must be positive")

    bounds = epa_envelope(args.epa_geojson)
    print(
        "Official EPA envelope:",
        f"west={bounds[0]:.8f}",
        f"south={bounds[1]:.8f}",
        f"east={bounds[2]:.8f}",
        f"north={bounds[3]:.8f}",
    )

    results: list[dict[str, Any]] = []
    failures = 0
    for target in TARGETS:
        print(
            "OpenAltimetry EPA-envelope probe:",
            target["date"],
            f"RGT {int(target['track_id']):04d}",
        )
        try:
            result = probe_target(
                target,
                bounds=bounds,
                output_dir=args.output_dir,
                timeout_seconds=args.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic preserves network/server failure
            failures += 1
            result = {
                "resource": target["resource"],
                "date": target["date"],
                "target_track_id": target["track_id"],
                "error_type": type(exc).__name__,
                "error": str(exc),
                "decision": "unresolved_request_failure",
            }
        results.append(result)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "epa_envelope_probe_summary.json"
    summary_path.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, indent=2, sort_keys=True))
    print(f"EPA-envelope probe summary: {summary_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
