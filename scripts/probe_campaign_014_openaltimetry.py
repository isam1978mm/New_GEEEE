"""Probe NASA/NSIDC OpenAltimetry for the two Campaign 014 ATL08 passes.

This is a Campaign-014-only no-account diagnostic.  It calls the public
OpenAltimetry ATL08 API for the exact dates/RGTs of the two SlideRule-problem
resources and stores the raw responses for inspection.  It does not modify
scientific thresholds, campaign geometry, application behavior, or other
campaigns.
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

API_URL = "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/atl08"
CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
DEFAULT_OUTPUT_DIR = (
    Path("data")
    / "research"
    / "icesat2_broad_track_scan"
    / CAMPAIGN_ID
    / "openaltimetry_probe"
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


class OpenAltimetryProbeError(RuntimeError):
    pass


def _params(target: dict[str, Any], *, output_format: str) -> dict[str, str]:
    west, south, east, north = DEFAULT_BOUNDS
    return {
        "date": str(target["date"]),
        "minx": f"{west:.6f}",
        "miny": f"{south:.6f}",
        "maxx": f"{east:.6f}",
        "maxy": f"{north:.6f}",
        "trackId": str(int(target["track_id"])),
        "outputFormat": output_format,
        "client": "campaign014",
    }


def _fetch(url: str, *, timeout_seconds: float) -> tuple[int, str, bytes]:
    request = Request(url, headers={"User-Agent": "New_GEEEE-Campaign014/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed NASA HTTPS endpoint
        status = int(getattr(response, "status", 200))
        content_type = str(response.headers.get("Content-Type", ""))
        body = response.read()
    return status, content_type, body


def probe_target(
    target: dict[str, Any],
    *,
    output_dir: Path,
    timeout_seconds: float,
    output_format: str,
    fetch=_fetch,
) -> dict[str, Any]:
    params = _params(target, output_format=output_format)
    url = API_URL + "?" + urlencode(params)
    status, content_type, body = fetch(url, timeout_seconds=timeout_seconds)

    suffix = ".json" if output_format == "json" else ".csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / (str(target["resource"]) + suffix)
    raw_path.write_bytes(body)

    preview = body[:1000].decode("utf-8", errors="replace")
    result: dict[str, Any] = {
        "resource": target["resource"],
        "date": target["date"],
        "track_id": target["track_id"],
        "http_status": status,
        "content_type": content_type,
        "bytes": len(body),
        "raw_path": str(raw_path),
        "preview": preview,
    }

    if output_format == "json" and body:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            result["json_valid"] = False
        else:
            result["json_valid"] = True
            result["json_type"] = type(parsed).__name__
            if isinstance(parsed, dict):
                result["top_level_keys"] = sorted(str(key) for key in parsed.keys())[:50]
            elif isinstance(parsed, list):
                result["list_length"] = len(parsed)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--output-format", choices=("json", "csv"), default="json")
    args = parser.parse_args()

    if args.timeout_seconds <= 0:
        raise SystemExit("timeout must be positive")

    results: list[dict[str, Any]] = []
    failures = 0
    for target in TARGETS:
        print(
            "OpenAltimetry probe:",
            target["date"],
            f"RGT {int(target['track_id']):04d}",
            target["resource"],
        )
        try:
            result = probe_target(
                target,
                output_dir=args.output_dir,
                timeout_seconds=args.timeout_seconds,
                output_format=args.output_format,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic must report network/server errors
            failures += 1
            result = {
                "resource": target["resource"],
                "date": target["date"],
                "track_id": target["track_id"],
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        results.append(result)

    summary_path = args.output_dir / "probe_summary.json"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    print(f"probe summary: {summary_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
