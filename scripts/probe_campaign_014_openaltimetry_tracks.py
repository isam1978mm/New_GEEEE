"""Verify whether the two Campaign 014 RGTs actually intersect the AOI on their dates.

This is a no-account, read-only diagnostic using OpenAltimetry's public
``getTracks`` endpoint.  It exists to distinguish an unreadable but relevant
ATL08 granule from a CMR near-miss that does not actually cross the Campaign 014
bounding box.  It does not change any scientific threshold or campaign result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

API_URL = "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/getTracks"
CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
DEFAULT_OUTPUT_DIR = (
    Path("data")
    / "research"
    / "icesat2_broad_track_scan"
    / CAMPAIGN_ID
    / "openaltimetry_track_probe"
)
DEFAULT_BOUNDS = (-77.70, 38.80, -77.10, 39.20)
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


def _params(target: dict[str, Any]) -> dict[str, str]:
    west, south, east, north = DEFAULT_BOUNDS
    return {
        "date": str(target["date"]),
        "minx": f"{west:.6f}",
        "miny": f"{south:.6f}",
        "maxx": f"{east:.6f}",
        "maxy": f"{north:.6f}",
        "outputFormat": "json",
    }


def _fetch(url: str, *, timeout_seconds: float) -> tuple[int, str, bytes]:
    request = Request(url, headers={"User-Agent": "New_GEEEE-Campaign014/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed NASA HTTPS endpoint
        return (
            int(getattr(response, "status", 200)),
            str(response.headers.get("Content-Type", "")),
            response.read(),
        )


def _track_ids(value: Any) -> list[int]:
    """Extract track/RGT identifiers from tolerant OpenAltimetry JSON shapes."""

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


def probe_target(
    target: dict[str, Any],
    *,
    output_dir: Path,
    timeout_seconds: float,
    fetch=_fetch,
) -> dict[str, Any]:
    url = API_URL + "?" + urlencode(_params(target))
    status, content_type, body = fetch(url, timeout_seconds=timeout_seconds)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"tracks_{target['date']}.json"
    raw_path.write_bytes(body)

    result: dict[str, Any] = {
        "resource": target["resource"],
        "date": target["date"],
        "target_track_id": int(target["track_id"]),
        "http_status": status,
        "content_type": content_type,
        "bytes": len(body),
        "raw_path": str(raw_path),
    }

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        result.update({"json_valid": False, "decision": "unresolved_invalid_json", "error": str(exc)})
        return result

    tracks = _track_ids(payload)
    target_present = int(target["track_id"]) in tracks
    result.update(
        {
            "json_valid": True,
            "returned_track_ids": tracks,
            "returned_track_count": len(tracks),
            "target_track_present": target_present,
        }
    )
    if target_present:
        result["decision"] = "target_track_intersects_campaign_bounds"
    elif tracks:
        result["decision"] = "target_track_absent_while_other_tracks_intersect"
    else:
        result["decision"] = "no_tracks_returned_date_or_service_unresolved"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        raise SystemExit("timeout must be positive")

    results: list[dict[str, Any]] = []
    failures = 0
    for target in TARGETS:
        print(
            "OpenAltimetry getTracks:",
            target["date"],
            f"target RGT {int(target['track_id']):04d}",
        )
        try:
            result = probe_target(
                target,
                output_dir=args.output_dir,
                timeout_seconds=args.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic must preserve remote errors
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

    summary_path = args.output_dir / "track_probe_summary.json"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    print(f"track probe summary: {summary_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
