"""Inspect Elizabeth Mine public EPA document collections for usable calibration evidence.

This bounded research utility downloads metadata inventories for the public
Special Collections exposed by EPA and flags documents that may contain final
construction reports, CQA, as-built surveys, cap cross-sections, excavation and
restoration limits, survey accuracy, and stable post-construction monitoring.
It does not call Earth Engine, create calibration rows, train a model, or enable
depth output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

COLLECTIONS = (
    ("70040", "Key Documents"),
    ("32789", "Decision Documents"),
    ("32785", "Fact Sheets and Public Meeting Documents"),
    ("32788", "Five Year Review Reports"),
    ("32787", "History of Elizabeth Mine: Reports and Studies"),
    ("33344", "Institutional Controls - Elizabeth Mine"),
    ("35054", "News Releases"),
    ("31805", "Publicly Available Documents - Elizabeth Mine"),
    ("42243", "Redevelopment"),
    ("32786", "Technical Reports and Studies"),
)
TERMS = (
    "remedial action report",
    "final remedial action",
    "construction completion",
    "construction report",
    "final construction",
    "construction quality assurance",
    "cqa",
    "quality assurance",
    "as-built",
    "as built",
    "record drawing",
    "final survey",
    "licensed surveyor",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "coordinate system",
    "state plane",
    "navd",
    "tailing pile 1",
    "tailing pile 2",
    "tp-1",
    "tp-2",
    "cover system",
    "cap system",
    "soil cover",
    "cover thickness",
    "excavation limit",
    "limits of excavation",
    "waste rock",
    "restoration plan",
    "restored areas",
    "final grading",
    "vegetation",
    "post-construction monitoring",
    "operation and maintenance",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "elizabeth_mine_collection_inventory"
    output.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)"}

    collections: list[dict[str, object]] = []
    all_matches: list[dict[str, object]] = []
    for collection_id, description in COLLECTIONS:
        url = f"https://semspub.epa.gov/src/cachejson/01/SC/{collection_id}"
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        payload = response.json()
        (output / f"collection_SC_{collection_id}.json").write_text(
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
                all_matches.append(
                    {
                        "collection_id": collection_id,
                        "description": description,
                        **record,
                    }
                )
        collections.append(
            {
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
        "status": "ELIZABETH_MINE_PUBLIC_COLLECTION_INVENTORY_COMPLETE",
        "site_name": "Elizabeth Mine",
        "epa_id": "VTD988366621",
        "collections": collections,
        "all_target_matches": all_matches,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_FINAL_CONSTRUCTION_SURVEY_SURFACE_AND_UNCERTAINTY_REVIEW",
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
