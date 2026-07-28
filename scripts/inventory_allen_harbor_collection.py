"""Inventory decisive Allen Harbor records from official EPA SEMS feeds."""
from __future__ import annotations

import json
from pathlib import Path

import requests

COLLECTIONS = {
    "key_documents": "https://semspub.epa.gov/src/cachejson/01/SC/70121",
    "public_documents": "https://semspub.epa.gov/src/cachejson/01/SC/31799",
    "five_year_reviews": "https://semspub.epa.gov/src/cachejson/01/SC/32764",
    "decision_documents": "https://semspub.epa.gov/src/cachejson/01/SC/32765",
}
TERMS = (
    "allen harbor",
    "site 09",
    "site 9",
    "remedial action report",
    "design analysis report",
    "final design",
    "construction completion",
    "as-built",
    "as built",
    "settlement survey",
    "long-term management",
    "long term management",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/json,*/*",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "allen_harbor_collection_inventory"
    out.mkdir(parents=True, exist_ok=True)
    selected: dict[str, dict[str, object]] = {}
    counts: dict[str, int] = {}
    errors: list[dict[str, str]] = []
    session = requests.Session()
    for label, url in COLLECTIONS.items():
        try:
            response = session.get(url, headers=HEADERS, timeout=(30, 90))
            response.raise_for_status()
            payload = response.json()
            (out / f"{label}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            counts[label] = len(rows) if isinstance(rows, list) else 0
            for row in rows if isinstance(rows, list) else []:
                if not isinstance(row, dict):
                    continue
                title = str(row.get("docTitle") or "").strip()
                lower = title.lower()
                if not any(term in lower for term in TERMS):
                    continue
                doc_id = str(row.get("docId") or "").strip()
                if not doc_id:
                    continue
                item = selected.setdefault(doc_id, {
                    "doc_id": doc_id,
                    "title": title,
                    "doc_date": row.get("docDate"),
                    "author": row.get("author"),
                    "addressee": row.get("addressee"),
                    "collections": [],
                    "pdf_url": f"https://semspub.epa.gov/work/01/{doc_id}.pdf",
                })
                item["collections"].append(label)
        except Exception as exc:
            errors.append({"collection": label, "error": repr(exc)})
    report = {
        "status": "INVENTORY_COMPLETE",
        "collection_counts": counts,
        "selected_count": len(selected),
        "selected_records": list(selected.values()),
        "errors": errors,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }
    (out / "inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "selected_count": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
