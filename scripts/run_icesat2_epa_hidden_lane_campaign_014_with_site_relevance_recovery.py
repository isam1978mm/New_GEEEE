"""Run Campaign 014 while excluding only proven off-site failed ATL08 resources.

This launcher layers one narrow completeness rule on top of the existing strict
Campaign 014 watchdog.  Broad and explicit-resource SlideRule retries remain
unchanged.  If a CMR-listed resource still fails after those retries, the
resource may be excluded from tile completeness only when the public NASA
OpenAltimetry getTracks service proves both of these facts for that exact date
and RGT:

1. the RGT crosses the current 25 km acquisition tile; and
2. the same RGT does not cross the tight official EPA Hidden Lane envelope.

Absence from that envelope is sufficient to prove absence from the EPA polygon
contained by it.  If either check is unavailable or ambiguous, the failed
resource continues to block the tile.  Scientific thresholds, EPA event gates,
finalizers, and application behavior are unchanged.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_icesat2_epa_hidden_lane_campaign_014_with_tile_watchdog as watchdog

OPENALTIMETRY_TRACKS_URL = (
    "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/getTracks"
)
# Tight envelope derived from the cached official EPA Hidden Lane polygon and
# independently verified by the Campaign 014 EPA-envelope probe.
EPA_ENVELOPE = (
    -77.42677485999997,
    39.052508687000056,
    -77.41625001099999,
    39.06693744100005,
)
_RESOURCE_RE = re.compile(
    r"^ATL08_(?P<date>\d{8})\d{6}_(?P<rgt>\d{4})\d{4}_007_\d{2}\.h5$"
)
_ORIGINAL_RECOVER = watchdog._recover_by_explicit_resources


class Campaign014SiteRelevanceError(RuntimeError):
    """Raised when a failed resource cannot be proven irrelevant to the EPA site."""


def _resource_date_rgt(resource: str) -> tuple[str, int]:
    match = _RESOURCE_RE.fullmatch(resource)
    if match is None:
        raise Campaign014SiteRelevanceError(
            f"cannot parse Campaign 014 ATL08 resource metadata: {resource}"
        )
    raw_date = match.group("date")
    date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    return date, int(match.group("rgt"))


def _bounds_from_polygon(
    polygon: list[dict[str, float]],
) -> tuple[float, float, float, float]:
    if not polygon:
        raise Campaign014SiteRelevanceError("Campaign 014 tile polygon is empty")
    longitudes = [float(point["lon"]) for point in polygon]
    latitudes = [float(point["lat"]) for point in polygon]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def _track_ids(value: Any) -> list[int]:
    found: set[int] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).lower() in {"track", "trackid", "rgt", "rgt_id"}:
                    try:
                        parsed = int(child)
                    except (TypeError, ValueError):
                        pass
                    else:
                        if parsed >= 0:
                            found.add(parsed)
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return sorted(found)


def _openaltimetry_tracks(
    *,
    date: str,
    bounds: tuple[float, float, float, float],
    timeout_seconds: float,
) -> list[int]:
    west, south, east, north = bounds
    url = OPENALTIMETRY_TRACKS_URL + "?" + urlencode(
        {
            "date": date,
            "minx": f"{west:.8f}",
            "miny": f"{south:.8f}",
            "maxx": f"{east:.8f}",
            "maxy": f"{north:.8f}",
            "outputFormat": "json",
        }
    )
    request = Request(url, headers={"User-Agent": "New_GEEEE-Campaign014/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed NASA HTTPS endpoint
        status = int(getattr(response, "status", 200))
        body = response.read()
    if status != 200:
        raise Campaign014SiteRelevanceError(
            f"OpenAltimetry getTracks returned HTTP {status}"
        )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise Campaign014SiteRelevanceError(
            "OpenAltimetry getTracks returned invalid JSON"
        ) from exc
    return _track_ids(payload)


def _failed_resource_is_proven_off_site(
    resource: str,
    *,
    tile_polygon: list[dict[str, float]],
    timeout_seconds: float,
    track_lookup=_openaltimetry_tracks,
) -> tuple[bool, dict[str, Any]]:
    """Return true only when tile presence + EPA-envelope absence are both proven."""

    date, rgt = _resource_date_rgt(resource)
    tile_bounds = _bounds_from_polygon(tile_polygon)
    tile_tracks = track_lookup(
        date=date,
        bounds=tile_bounds,
        timeout_seconds=timeout_seconds,
    )
    epa_tracks = track_lookup(
        date=date,
        bounds=EPA_ENVELOPE,
        timeout_seconds=timeout_seconds,
    )
    tile_present = rgt in tile_tracks
    epa_present = rgt in epa_tracks
    proof = {
        "resource": resource,
        "date": date,
        "rgt": rgt,
        "tile_track_present": tile_present,
        "epa_envelope_track_present": epa_present,
        "tile_track_ids": tile_tracks,
        "epa_envelope_track_ids": epa_tracks,
    }
    return tile_present and not epa_present, proof


def _recover_by_explicit_resources_with_site_relevance(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float,
    attempts: int = watchdog.DEFAULT_ATL08_RESOURCE_ATTEMPTS,
):
    """Recover every relevant CMR resource; exclude only independently proven off-site failures."""

    if attempts <= 0:
        raise ValueError("ATL08 resource attempts must be positive")

    resources_value, cmr_failures = watchdog._run_worker_request(
        {
            "operation": "cmr",
            "polygon": polygon,
            "start": start,
            "end": end,
        },
        timeout_seconds=timeout_seconds,
    )
    if cmr_failures:
        raise watchdog.Campaign014ResourceRecoveryError(
            "Campaign 014 CMR resource lookup unexpectedly reported resource-read failures: "
            + " | ".join(cmr_failures[:8])
        )

    resources = watchdog._unique_resource_names(resources_value)
    print(
        "      broad ATL08 reads remained partial; "
        f"recovering {len(resources)} CMR-listed resources individually"
    )

    frames: list[Any] = []
    unresolved: list[dict[str, Any]] = []
    excluded_off_site: list[dict[str, Any]] = []

    for resource_index, resource in enumerate(resources, start=1):
        history: list[str] = []
        recovered = False
        for attempt_number in range(1, attempts + 1):
            try:
                frame, failures = watchdog._run_worker_request(
                    {
                        "operation": "resource",
                        "resource": resource,
                        "polygon": polygon,
                        "start": start,
                        "end": end,
                    },
                    timeout_seconds=timeout_seconds,
                )
            except (watchdog.Campaign014TileTimeoutError, RuntimeError) as exc:
                history.append(
                    f"attempt {attempt_number}/{attempts}: {type(exc).__name__}: {exc}"
                )
                continue

            if failures:
                history.extend(
                    f"attempt {attempt_number}/{attempts}: {line}"
                    for line in failures[:8]
                )
                continue

            frames.append(frame)
            recovered = True
            break

        if recovered:
            if resource_index == len(resources) or resource_index % 10 == 0:
                print(
                    "      explicit-resource recovery "
                    f"{resource_index}/{len(resources)}"
                )
            continue

        failure = {
            "resource": resource,
            "attempts": attempts,
            "history": history[-12:],
        }
        try:
            proven_off_site, proof = _failed_resource_is_proven_off_site(
                resource,
                tile_polygon=polygon,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - failed proof must keep resource blocking
            failure["site_relevance_check_error"] = f"{type(exc).__name__}: {exc}"
            unresolved.append(failure)
            continue

        failure["site_relevance_proof"] = proof
        if proven_off_site:
            excluded_off_site.append(failure)
            print(
                "      excluded failed off-site resource after exact EPA-envelope proof: "
                f"{resource}"
            )
        else:
            unresolved.append(failure)

    if unresolved:
        details = json.dumps(unresolved[:8], sort_keys=True)
        raise watchdog.Campaign014ResourceRecoveryError(
            "Campaign 014 explicit-resource recovery remains incomplete after "
            "site-relevance checks; unresolved relevant/ambiguous resources: "
            + details
        )

    combined = watchdog._combine_resource_frames(frames)
    attrs = getattr(combined, "attrs", None)
    if isinstance(attrs, dict):
        attrs["campaign014_excluded_failed_off_site_resources"] = [
            item["resource"] for item in excluded_off_site
        ]
        attrs["campaign014_site_relevance_rule"] = (
            "failed resource excluded only when RGT is present in current tile "
            "and absent from exact EPA Hidden Lane envelope"
        )
    return combined


def install_site_relevance_recovery() -> None:
    watchdog._recover_by_explicit_resources = (
        _recover_by_explicit_resources_with_site_relevance
    )


def main() -> int:
    install_site_relevance_recovery()
    return watchdog.main()


if __name__ == "__main__":
    raise SystemExit(main())
