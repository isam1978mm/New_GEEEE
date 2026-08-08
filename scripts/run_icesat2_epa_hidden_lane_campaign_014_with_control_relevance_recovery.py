"""Run Campaign 014 using a positive-control proof for failed off-site ATL08 resources.

This launcher layers one narrow correction on top of the existing Campaign 014
site-relevance recovery.  A failed CMR-listed ATL08 resource may be excluded
from tile completeness only when the public NASA OpenAltimetry ``getTracks``
service proves, for that exact date and RGT, both of these facts:

1. the RGT is present inside the broad Campaign-014 control bounds; and
2. the same RGT is absent from the tight official EPA Hidden Lane envelope.

The broad control bounds are the same bounds independently probed before this
launcher was added.  Requiring a positive control prevents an empty EPA-envelope
response from being mistaken for proof when the service/date is unavailable.

The current 25 km tile no longer has to contain the RGT.  That requirement was
unnecessary: if the track is absent from the EPA envelope, it cannot contribute
an observation inside the EPA polygon contained by that envelope, regardless of
whether CMR listed the granule for a neighbouring acquisition tile.

Scientific thresholds, EPA event gates, finalizers, the generic scanner, and
application behavior are unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_icesat2_epa_hidden_lane_campaign_014_with_site_relevance_recovery as site

# Same broad Campaign-014 bounds used by the successful independent getTracks
# probe that returned RGT 0629 on 2021-05-04 and RGT 0187 on 2025-12-26.
CONTROL_BOUNDS = (-77.70, 38.80, -77.10, 39.20)


def _failed_resource_is_proven_off_site_with_control(
    resource: str,
    *,
    tile_polygon: list[dict[str, float]],
    timeout_seconds: float,
    track_lookup=site._openaltimetry_tracks,
) -> tuple[bool, dict[str, Any]]:
    """Prove off-site only with control presence plus EPA-envelope absence."""

    del tile_polygon  # acquisition-tile presence is not required for site relevance
    date, rgt = site._resource_date_rgt(resource)
    control_tracks = track_lookup(
        date=date,
        bounds=CONTROL_BOUNDS,
        timeout_seconds=timeout_seconds,
    )
    epa_tracks = track_lookup(
        date=date,
        bounds=site.EPA_ENVELOPE,
        timeout_seconds=timeout_seconds,
    )
    control_present = rgt in control_tracks
    epa_present = rgt in epa_tracks
    proof = {
        "resource": resource,
        "date": date,
        "rgt": rgt,
        "control_track_present": control_present,
        "epa_envelope_track_present": epa_present,
        "control_track_ids": control_tracks,
        "epa_envelope_track_ids": epa_tracks,
        "control_bounds": {
            "west": CONTROL_BOUNDS[0],
            "south": CONTROL_BOUNDS[1],
            "east": CONTROL_BOUNDS[2],
            "north": CONTROL_BOUNDS[3],
        },
    }
    return control_present and not epa_present, proof


def install_control_relevance_recovery() -> None:
    site._failed_resource_is_proven_off_site = (
        _failed_resource_is_proven_off_site_with_control
    )


def main() -> int:
    install_control_relevance_recovery()
    return site.main()


if __name__ == "__main__":
    raise SystemExit(main())
