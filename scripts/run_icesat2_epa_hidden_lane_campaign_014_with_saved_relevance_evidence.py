"""Run Campaign 014 using previously saved OpenAltimetry relevance evidence.

The public OpenAltimetry getTracks service returned the expected Campaign-014
RGTs during the standalone probes, but later returned transient empty lists when
called repeatedly from inside the long scanner run.  This launcher therefore
uses the saved outputs from those successful probes instead of re-querying the
service during resource recovery.

A failed ATL08 resource may be excluded from tile completeness only when BOTH
saved artifacts contain the exact matching resource/date/RGT and prove:

* broad Campaign-014 control probe: target track present;
* exact EPA-envelope probe: target track absent.

Any missing, malformed, contradictory, or non-matching saved evidence fails
closed and the resource continues to block the tile.  No scientific threshold,
EPA event gate, finalizer, generic scanner, application behavior, or other
campaign is changed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_icesat2_epa_hidden_lane_campaign_014_with_control_relevance_recovery as control

CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
CAMPAIGN_DIR = Path("data") / "research" / "icesat2_broad_track_scan" / CAMPAIGN_ID
CONTROL_SUMMARY_PATH = (
    CAMPAIGN_DIR / "openaltimetry_track_probe" / "track_probe_summary.json"
)
EPA_SUMMARY_PATH = (
    CAMPAIGN_DIR
    / "openaltimetry_epa_envelope_probe"
    / "epa_envelope_probe_summary.json"
)


class Campaign014SavedEvidenceError(RuntimeError):
    """Raised when saved relevance evidence cannot prove a resource off-site."""


def _load_summary(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise Campaign014SavedEvidenceError(f"missing saved relevance evidence: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Campaign014SavedEvidenceError(
            f"cannot read saved relevance evidence {path}: {exc}"
        ) from exc
    if not isinstance(payload, list):
        raise Campaign014SavedEvidenceError(
            f"saved relevance evidence is not a list: {path}"
        )
    rows = [item for item in payload if isinstance(item, dict)]
    if len(rows) != len(payload):
        raise Campaign014SavedEvidenceError(
            f"saved relevance evidence contains non-object rows: {path}"
        )
    return rows


def _matching_row(
    rows: list[dict[str, Any]],
    *,
    resource: str,
    date: str,
    rgt: int,
    label: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in rows
        if row.get("resource") == resource
        and row.get("date") == date
        and int(row.get("target_track_id", -1)) == rgt
    ]
    if len(matches) != 1:
        raise Campaign014SavedEvidenceError(
            f"{label} evidence has {len(matches)} exact matches for {resource}"
        )
    return matches[0]


def _saved_relevance_proof(
    resource: str,
    *,
    control_summary_path: Path = CONTROL_SUMMARY_PATH,
    epa_summary_path: Path = EPA_SUMMARY_PATH,
) -> tuple[bool, dict[str, Any]]:
    date, rgt = control.site._resource_date_rgt(resource)
    control_rows = _load_summary(control_summary_path)
    epa_rows = _load_summary(epa_summary_path)

    control_row = _matching_row(
        control_rows,
        resource=resource,
        date=date,
        rgt=rgt,
        label="control",
    )
    epa_row = _matching_row(
        epa_rows,
        resource=resource,
        date=date,
        rgt=rgt,
        label="EPA-envelope",
    )

    control_present = control_row.get("target_track_present") is True
    control_decision = control_row.get("decision")
    epa_present = epa_row.get("target_track_present") is True
    epa_decision = epa_row.get("decision")

    control_valid = (
        control_present
        and control_decision == "target_track_intersects_campaign_bounds"
        and rgt in [int(value) for value in control_row.get("returned_track_ids", [])]
    )
    epa_valid = (
        not epa_present
        and epa_decision == "target_track_absent_from_exact_epa_envelope"
        and rgt not in [int(value) for value in epa_row.get("returned_track_ids", [])]
    )

    proof = {
        "resource": resource,
        "date": date,
        "rgt": rgt,
        "saved_control_summary": str(control_summary_path),
        "saved_epa_summary": str(epa_summary_path),
        "control_track_present": control_present,
        "control_decision": control_decision,
        "control_track_ids": control_row.get("returned_track_ids", []),
        "epa_envelope_track_present": epa_present,
        "epa_decision": epa_decision,
        "epa_envelope_track_ids": epa_row.get("returned_track_ids", []),
    }
    return control_valid and epa_valid, proof


def _failed_resource_is_proven_off_site_from_saved_evidence(
    resource: str,
    *,
    tile_polygon: list[dict[str, float]],
    timeout_seconds: float,
) -> tuple[bool, dict[str, Any]]:
    del tile_polygon, timeout_seconds
    return _saved_relevance_proof(resource)


def install_saved_evidence_recovery() -> None:
    control.site._failed_resource_is_proven_off_site = (
        _failed_resource_is_proven_off_site_from_saved_evidence
    )


def main() -> int:
    install_saved_evidence_recovery()
    return control.site.main()


if __name__ == "__main__":
    raise SystemExit(main())
