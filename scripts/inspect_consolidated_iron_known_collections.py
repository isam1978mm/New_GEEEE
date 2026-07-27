"""Inspect the two EPA SEMS collections returned for Consolidated Iron.

The live SEMS search returns Special Collection 70219 and Administrative Record
62153. This bounded utility downloads both collection inventories, preserves all
document metadata, and flags construction, as-built, survey, geotextile, Site
Management Plan, and Final Remedial Action Report terms. It does not call Earth
Engine or create calibration records.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

COLLECTIONS = (
    ("SC", "70219", "Key Documents"),
    ("AR", "62153", "FY2007 ROD AR OU1"),
)
TERMS = (
    "remedial action report",
    "final remedial action",
    "site management plan",
    "site modification plan",
    "as-built",
    "as built",
    "record drawing",
    "construction completion",
    "construction report",
    "survey",
    "geotextile",
    "demarcation",
    "excavation",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "consolidated_iron_collection_inventory"
    output.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)"}

    collection_records: list[dict[str, object]] = []
    all_matches: list[dict[str, object]] = []
    for kind, collection_id, description in COLLECTIONS:
        url = f"https://semspub.epa.gov/src/cachejson/02/{kind}/{collection_id}"
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        payload = response.json()
        (output / f"collection_{kind}_{collection_id}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        documents = payload.get("data", [])
        matches: list[dict[str, object]] = []
        for document in documents:
            searchable = " ".join(str(value) for value in document.values()).lower()
            found = [term for term in TERMS if term in searchable]
            if found:
                record = {"matches": found, "document": document}
                matches.append(record)
                all_matches.append({"kind": kind, "collection_id": collection_id, **record})
        collection_records.append(
            {
                "kind": kind,
                "collection_id": collection_id,
                "description": description,
                "url": url,
                "meta": payload.get("meta", {}),
                "document_count": len(documents),
                "documents": documents,
                "target_matches": matches,
            }
        )

    report = {
        "status": "CONSOLIDATED_IRON_COLLECTION_INVENTORY_COMPLETE",
        "collections": collection_records,
        "all_target_matches": all_matches,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_FINAL_RAR_OR_EQUIVALENT_MEASURED_DEPTH_SURVEY_IS_RECOVERED",
    }
    (output / "inventory_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "INVENTORY_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
