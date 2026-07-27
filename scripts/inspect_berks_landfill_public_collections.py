"""Inspect Berks Landfill public EPA collections for final cap evidence.

This bounded research utility downloads the known Key Documents and both
Administrative Record inventories, discovers any additional Special Collection
IDs from the public site profile, and flags records that may contain the final
remedial-action/construction report, as-built cap survey, final cap-thickness
measurements, CQA, survey accuracy, vegetation, and long-term maintenance.
It does not call Earth Engine, create calibration rows, train a model, or enable
depth output.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

SITE_ID = "0301944"
REGION = "03"
KNOWN_COLLECTIONS = (
    ("SC", "30665", "Key Documents"),
    ("AR", "205", "Administrative Record 205"),
    ("AR", "206", "Administrative Record 206"),
)
PROFILE_URLS = (
    f"https://cumulis.epa.gov/supercpad/cursites/csitinfo.cfm?id={SITE_ID}",
    f"https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.docdata&id={SITE_ID}",
)
TERMS = (
    "remedial action report",
    "final remedial action",
    "construction completion",
    "construction report",
    "final construction",
    "preliminary close out report",
    "final close out report",
    "close-out report",
    "construction quality assurance",
    "quality assurance",
    "cqa",
    "as-built",
    "as built",
    "record drawing",
    "final survey",
    "licensed surveyor",
    "survey accuracy",
    "horizontal accuracy",
    "vertical accuracy",
    "cap thickness",
    "cover thickness",
    "soil cover",
    "cap repair",
    "cover repair",
    "one foot",
    "1 foot",
    "12 inches",
    "two feet",
    "2 feet",
    "24 inches",
    "eastern landfill",
    "western landfill",
    "vegetation",
    "operation and maintenance",
    "five-year review",
)


def collection_ids_from_html(html: str) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for match in re.finditer(r"colid=(\d+)", html, re.I):
        collection_id = match.group(1)
        # Site-profile document pages normally expose Special Collections.
        found.add(("SC", collection_id))
    for match in re.finditer(r"cachejson/03/(SC|AR)/(\d+)", html, re.I):
        found.add((match.group(1).upper(), match.group(2)))
    return found


def load_collection(kind: str, collection_id: str, headers: dict[str, str]) -> dict[str, object]:
    url = f"https://semspub.epa.gov/src/cachejson/{REGION}/{kind}/{collection_id}"
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    payload = response.json()
    documents = payload.get("data", [])
    matches: list[dict[str, object]] = []
    for document in documents:
        searchable = " ".join(str(value) for value in document.values()).lower()
        found = [term for term in TERMS if term in searchable]
        if found:
            matches.append({"matches": found, "document": document})
    return {
        "kind": kind,
        "collection_id": collection_id,
        "url": url,
        "meta": payload.get("meta", {}),
        "document_count": len(documents),
        "documents": documents,
        "target_matches": matches,
        "payload": payload,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "berks_landfill_collection_inventory"
    output.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)",
        "Accept": "text/html,application/json,application/xhtml+xml,*/*",
    }

    profile_records: list[dict[str, object]] = []
    discovered: set[tuple[str, str]] = {(kind, cid) for kind, cid, _ in KNOWN_COLLECTIONS}
    for index, url in enumerate(PROFILE_URLS, start=1):
        record: dict[str, object] = {"url": url}
        try:
            response = requests.get(url, headers=headers, timeout=120, allow_redirects=True)
            record["status_code"] = response.status_code
            record["final_url"] = response.url
            record["content_type"] = response.headers.get("content-type", "")
            response.raise_for_status()
            html = response.text
            record["bytes"] = len(response.content)
            record["collection_ids"] = sorted(collection_ids_from_html(html))
            discovered.update(collection_ids_from_html(html))
            (output / f"profile_{index}.html").write_text(html, encoding="utf-8")
        except Exception as exc:
            record["error"] = str(exc)
        profile_records.append(record)

    descriptions = {(kind, cid): description for kind, cid, description in KNOWN_COLLECTIONS}
    collection_records: list[dict[str, object]] = []
    all_matches: list[dict[str, object]] = []
    for kind, collection_id in sorted(discovered):
        record: dict[str, object]
        try:
            loaded = load_collection(kind, collection_id, headers)
            payload = loaded.pop("payload")
            (output / f"collection_{kind}_{collection_id}.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
            record = {
                "description": descriptions.get((kind, collection_id), "Discovered public collection"),
                **loaded,
            }
            for match in record["target_matches"]:
                all_matches.append(
                    {
                        "kind": kind,
                        "collection_id": collection_id,
                        "description": record["description"],
                        **match,
                    }
                )
        except Exception as exc:
            record = {
                "kind": kind,
                "collection_id": collection_id,
                "description": descriptions.get((kind, collection_id), "Discovered public collection"),
                "error": str(exc),
            }
        collection_records.append(record)

    report = {
        "status": "BERKS_LANDFILL_PUBLIC_COLLECTION_INVENTORY_COMPLETE",
        "site_name": "Berks Landfill",
        "site_id": SITE_ID,
        "profile_records": profile_records,
        "collections": collection_records,
        "all_target_matches": all_matches,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "decision": "HOLD_UNTIL_FINAL_POST_REPAIR_THICKNESS_GEOMETRY_UNCERTAINTY_AND_SURFACE_REVIEW",
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
