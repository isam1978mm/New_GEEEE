"""Inspect Fletcher's Paint Works public EPA document collections.

The final report courtesy copy omits several large appendices. This bounded
utility downloads the metadata inventories for Fletcher's public Special
Collections and flags documents that may contain the missing as-built survey,
Appendix D-2, Appendix O, cover verification, final survey, record drawings, or
construction quality records. It does not call Earth Engine or create a
calibration record.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

COLLECTIONS = (
    ("70042", "Key Documents"),
    ("32798", "Decision Documents"),
    ("32794", "Fact Sheets and Public Meeting Documents"),
    ("37022", "Five Year Review Report"),
    ("31807", "Publicly Available Documents"),
    ("42234", "Redevelopment"),
    ("32793", "Technical Reports and Studies"),
)
TERMS = (
    "final remedial action report",
    "remedial action report",
    "as-built",
    "as built",
    "record drawing",
    "appendix d-2",
    "appendix d",
    "appendix o",
    "final survey",
    "post-restoration survey",
    "survey",
    "cover verification",
    "cover thickness",
    "quality assurance",
    "construction completion",
    "final cover",
    "elm street",
    "mill street",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "fletcher_public_collection_inventory"
    output.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)"}

    collection_records: list[dict[str, object]] = []
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
                all_matches.append({"collection_id": collection_id, "description": description, **record})
        collection_records.append(
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
        "status": "FLETCHER_PUBLIC_COLLECTION_INVENTORY_COMPLETE",
        "collections": collection_records,
        "all_target_matches": all_matches,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_EXACT_AS_BUILT_GEOMETRY_AND_PIXEL_SUPPORT_ARE_CONFIRMED",
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
