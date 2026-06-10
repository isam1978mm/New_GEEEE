"""D1B — build the source-locked expected-output baseline used by D1A.

Reads the raw (untrusted) ``docs/parity_expected_outputs.json``, applies the
notebook-evidence reconciliation encoded in
``app.pipeline.parity.reference_scope_audit`` (DEM source-lock + scope tiers),
and writes ``docs/parity_expected_outputs_sourcelocked.json``.

Static-only. Does NOT execute notebooks/new.ipynb or Earth Engine. Run from the
repo root:

    python scripts/d1b_build_sourcelocked_baseline.py
"""
from __future__ import annotations

import json
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

from app.pipeline.parity.reference_scope_audit import (
    ALL_TIERS,
    DEM_FAMILY,
    DEM_SOURCE_LOCKED_OUTPUTS,
    PARITY_DOC_RELATIVE,
    SOURCELOCKED_DOC_RELATIVE,
    TIER_BY_ENTRY_ID,
    TIER_REQUIRED,
    expected_entries_from_parity_doc,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def build() -> dict:
    parity_doc = json.loads((REPO_ROOT / PARITY_DOC_RELATIVE).read_text(encoding="utf-8"))
    raw_entries = parity_doc.get("expected_outputs", [])

    # Group derived (family, tier, paths) keyed by source entry id, preserving
    # doc order. DEM is replaced wholesale with the source-locked set.
    derived = expected_entries_from_parity_doc(parity_doc)

    by_id: "OrderedDict[str, dict]" = OrderedDict()
    dem_done = False
    for raw in raw_entries:
        entry_id = str(raw.get("id"))
        family = raw.get("family") or "unclassified"
        if family == DEM_FAMILY:
            if dem_done:
                continue
            by_id["dem_source_locked"] = {
                "id": "dem_source_locked",
                "family": DEM_FAMILY,
                "scope_tier": TIER_REQUIRED,
                "paths": list(DEM_SOURCE_LOCKED_OUTPUTS),
                "notebook_verified": True,
                "evidence": "save_tif(name, arr) -> DEM_GEO8_TIFS/{name}_640.tif",
            }
            dem_done = True
            continue
        tier = TIER_BY_ENTRY_ID.get(entry_id, "optional")
        paths = [e.path for e in derived if e.family == family and e.scope_tier == tier
                 and e.path in raw.get("notebook_paths_or_patterns", [])]
        if not paths:
            continue
        by_id[entry_id] = {
            "id": entry_id,
            "family": str(family),
            "scope_tier": tier,
            "paths": paths,
            "notebook_verified": False,
        }

    entries = list(by_id.values())
    tier_totals = {tier: 0 for tier in ALL_TIERS}
    for e in entries:
        tier_totals[e["scope_tier"]] = tier_totals.get(e["scope_tier"], 0) + len(e["paths"])

    return {
        "schema": "parity_expected_outputs_sourcelocked_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "generated_from": PARITY_DOC_RELATIVE,
        "notebook_source": "notebooks/new.ipynb",
        "dem_source_locked": True,
        "dem_source_lock_note": (
            "DEM names locked from new.ipynb save_tif evidence: nine "
            "DEM_GEO8_TIFS/{name}_640.tif rasters. aspect_deg (not aspect); no tri/twi."
        ),
        "scope_tiers": list(ALL_TIERS),
        "tier_path_totals": tier_totals,
        "entries": entries,
    }


def main() -> None:
    out = build()
    out_path = REPO_ROOT / SOURCELOCKED_DOC_RELATIVE
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"entries: {len(out['entries'])}")
    print(f"tier path totals: {out['tier_path_totals']}")


if __name__ == "__main__":
    main()
