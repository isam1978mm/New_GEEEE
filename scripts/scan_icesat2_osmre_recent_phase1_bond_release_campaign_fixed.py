"""Campaign 012 live-source compatibility layer.

The original Campaign 012 implementation applied the full status/contact/date
filter in the ArcGIS ``where`` clause. The first live run returned zero
eligible polygons before ICESat-2 acquisition. This compatibility layer keeps
exactly the same approved Campaign 012 target and scientific gates, but asks
OSMRE only for Phase I records in the spatial envelope and applies the contact,
date, identity, and >=40 m component filters locally.

This distinguishes a true zero-target result from an ArcGIS SQL/date-filter
compatibility issue without broadening the campaign.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import scan_icesat2_osmre_recent_phase1_bond_release_campaign as campaign012

# Compatibility alias used by the existing Campaign 012 watchdog/tests.
campaign = campaign012.campaign

SOURCE_COMPAT_SCHEMA = "campaign012_osmre_source_compat_v1"


def fetch_recent_phase1_bond_release_compat(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json=campaign012.campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch Phase I polygons broadly, then enforce approved gates locally."""

    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid WGS84 bounds")

    envelope = json.dumps(
        {
            "xmin": west,
            "ymin": south,
            "xmax": east,
            "ymax": north,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )

    retained: list[dict[str, Any]] = []
    seen_identities: set[str] = set()
    rejection_counts: Counter[str] = Counter()
    raw_phase1_count = 0
    offset = 0

    for _page_number in range(1, campaign012.MAX_PAGES + 1):
        payload = fetch_json(
            campaign012.OSMRE_BOND_LAYER_URL,
            {
                "where": "reclamation_bond_status = 1",
                "geometry": envelope,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "objectid ASC",
                "resultOffset": str(offset),
                "resultRecordCount": str(campaign012.PAGE_SIZE),
                "f": "geojson",
            },
            timeout_seconds,
        )
        if payload.get("type") != "FeatureCollection":
            raise ValueError("OSMRE response is not a GeoJSON FeatureCollection")
        raw_features = payload.get("features")
        if not isinstance(raw_features, list):
            raise ValueError("OSMRE FeatureCollection has no features list")
        if not raw_features:
            break

        raw_phase1_count += len(raw_features)
        for raw_feature in raw_features:
            if not isinstance(raw_feature, dict):
                rejection_counts["malformed_feature"] += 1
                continue
            if campaign012._status_code(raw_feature) != campaign012.PHASE_I_STATUS_CODE:
                rejection_counts["not_phase_i_after_server_filter"] += 1
                continue

            contact_code = campaign012._contact_code(raw_feature)
            if contact_code not in campaign012.CONTACT_CODES:
                rejection_counts["outside_approved_contacts"] += 1
                continue

            status_date = campaign012._bond_status_date(raw_feature)
            if status_date is None:
                rejection_counts["missing_or_unparseable_bond_status_date"] += 1
                continue
            if not campaign012.BOND_DATE_MIN <= status_date <= campaign012.BOND_DATE_MAX:
                rejection_counts["outside_approved_2019_2024_date_window"] += 1
                continue

            identity = campaign012._identity(raw_feature)
            if identity is None:
                rejection_counts["missing_identity"] += 1
                continue
            if identity in seen_identities:
                rejection_counts["duplicate_identity"] += 1
                continue

            geometry = campaign012._filtered_geometry(raw_feature.get("geometry"))
            if geometry is None:
                rejection_counts["below_40m_component_envelope_screen"] += 1
                continue

            feature = copy.deepcopy(raw_feature)
            feature["geometry"] = geometry
            properties = feature.get("properties")
            if isinstance(properties, dict):
                properties["CAMPAIGN_OSMRE_IDENTITY"] = identity
                properties["CAMPAIGN_PHASE_I_DATE"] = status_date.isoformat()
                properties["CAMPAIGN_CONTACT_NAME"] = campaign012.CONTACT_CODES[contact_code]
                properties["CAMPAIGN_MINIMUM_ENVELOPE_SPAN_M"] = (
                    campaign012.MINIMUM_ENVELOPE_SPAN_M
                )
                properties["CAMPAIGN_SOURCE_COMPAT_SCHEMA"] = SOURCE_COMPAT_SCHEMA
            retained.append(feature)
            seen_identities.add(identity)

        offset += len(raw_features)
        exceeded = payload.get("exceededTransferLimit") is True
        if len(raw_features) < campaign012.PAGE_SIZE and not exceeded:
            break
    else:
        raise ValueError("OSMRE Phase I pagination exceeded the safety page limit")

    diagnostics = {
        "schema": SOURCE_COMPAT_SCHEMA,
        "server_where": "reclamation_bond_status = 1",
        "raw_phase1_feature_count": raw_phase1_count,
        "retained_approved_feature_count": len(retained),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "approved_contact_codes": sorted(campaign012.CONTACT_CODES),
        "approved_date_min": campaign012.BOND_DATE_MIN.isoformat(),
        "approved_date_max": campaign012.BOND_DATE_MAX.isoformat(),
        "minimum_component_envelope_span_m": campaign012.MINIMUM_ENVELOPE_SPAN_M,
    }

    if not retained:
        raise ValueError(
            "no eligible OSMRE Campaign 012 polygons after local approved gates; "
            + json.dumps(diagnostics, sort_keys=True)
        )

    return {
        "type": "FeatureCollection",
        "features": retained,
        "campaign_source_diagnostics": diagnostics,
    }


def install_campaign_source_compat() -> None:
    """Install Campaign 012 normally, then replace only its source fetch hook."""

    campaign012.install_campaign()
    campaign012.campaign.fetch_active_mines = fetch_recent_phase1_bond_release_compat


def main() -> int:
    install_campaign_source_compat()
    return campaign012.campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
