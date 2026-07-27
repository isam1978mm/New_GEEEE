"""Discover all SEMS public collections for Consolidated Iron and Metal.

EPA's search form populates Collection Type only after Region is selected. This
one-off utility follows that dynamic sequence for Region 02, searches both
Special Collections and Administrative Records by EPA ID, and inspects every
returned collection JSON for the Final Remedial Action Report, Site Management
Plan, as-built surveys, and related construction records. It does not call Earth
Engine or create calibration records.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from playwright.async_api import async_playwright

EPA_ID = "NY0002455756"
REGION = "02"
SEARCH_URL = "https://semspub.epa.gov/src/search"
REGION_ID = "arsearchformid:regionselectboxid"
TYPE_ID = "arsearchformid:collTypeId"
EPA_INPUT_ID = "arsearchformid:inpuEPAId"
SUBMIT_ID = "arsearchformid:searchButtonId"
TARGET_TERMS = (
    "remedial action report",
    "final remedial action",
    "site management plan",
    "site modification plan",
    "as-built",
    "as built",
    "record drawing",
    "construction completion",
    "survey",
    "geotextile",
    "demarcation",
)


def id_selector(element_id: str) -> str:
    """Return an attribute selector safe for JSF IDs containing colons."""
    return f'[id="{element_id}"]'


async def options_for(page, element_id: str) -> list[dict[str, str]]:  # noqa: ANN001
    return await page.locator(id_selector(element_id)).evaluate(
        "el => [...el.options].map(o => ({text:(o.textContent||'').trim(), value:o.value}))"
    )


def choose_collection_value(options: list[dict[str, str]], kind: str) -> str:
    needle = "special" if kind == "SC" else "administrative"
    for option in options:
        if needle in option["text"].lower():
            return option["value"]
    for option in options:
        if option["value"].upper() == kind:
            return option["value"]
    raise RuntimeError(f"Could not resolve collection type {kind}: {options}")


async def submit_search(page, collection_kind: str, output: Path) -> dict[str, object]:  # noqa: ANN001
    await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=120_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=45_000)
    except Exception:
        pass
    await page.wait_for_timeout(2_000)

    # EPA populates Collection Type only after a Region change event.
    region = page.locator(id_selector(REGION_ID))
    collection_type = page.locator(id_selector(TYPE_ID))
    epa_input = page.locator(id_selector(EPA_INPUT_ID))
    submit = page.locator(id_selector(SUBMIT_ID))
    for label, locator in (
        ("region", region),
        ("collection type", collection_type),
        ("EPA ID", epa_input),
        ("submit", submit),
    ):
        if await locator.count() != 1:
            raise RuntimeError(f"SEMS {label} control not found uniquely")

    initial_controls = {
        "region_options": await options_for(page, REGION_ID),
        "collection_type_options_before_region": await options_for(page, TYPE_ID),
    }
    await region.select_option(value=REGION)

    # Wait for the JSF/Ajax update to add Special Collection and Administrative Record.
    await page.wait_for_function(
        "id => { const el=document.getElementById(id); return el && el.options.length > 1; }",
        TYPE_ID,
        timeout=60_000,
    )
    type_options = await options_for(page, TYPE_ID)
    initial_controls["collection_type_options_after_region"] = type_options
    initial_controls["input_id"] = EPA_INPUT_ID
    initial_controls["submit_id"] = SUBMIT_ID
    (output / f"search_controls_{collection_kind}.json").write_text(
        json.dumps(initial_controls, indent=2), encoding="utf-8"
    )

    type_value = choose_collection_value(type_options, collection_kind)
    await collection_type.select_option(value=type_value)
    await epa_input.fill(EPA_ID)

    await submit.click(timeout=20_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=60_000)
    except Exception:
        pass
    await page.wait_for_timeout(8_000)

    html = await page.content()
    body_text = await page.locator("body").inner_text()
    anchors = await page.eval_on_selector_all(
        "a",
        "els => els.map(a => ({text:(a.innerText||a.textContent||'').trim(), href:a.href||''}))",
    )
    (output / f"search_results_{collection_kind}.html").write_text(html, encoding="utf-8")

    ids = set(re.findall(r"(?:colid=|Collection ID\s*[:#]?\s*)(\d{4,})", html + "\n" + body_text, re.I))
    for anchor in anchors:
        query = parse_qs(urlparse(anchor["href"]).query)
        ids.update(query.get("colid", []))

    return {
        "collection_kind": collection_kind,
        "selected_type_value": type_value,
        "final_url": page.url,
        "collection_ids": sorted(ids),
        "anchors": anchors,
        "body_excerpt": body_text[:50_000],
    }


async def discover(output: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/126 environmental-evidence-recovery/1.0"
        )
        for kind in ("SC", "AR"):
            page = await context.new_page()
            records.append(await submit_search(page, kind, output))
            await page.close()
        await browser.close()
    return records


def inspect_collections(search_records: list[dict[str, object]], output: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; environmental-evidence-recovery/1.0)"}
    for search in search_records:
        kind = str(search["collection_kind"])
        for collection_id in search["collection_ids"]:
            url = f"https://semspub.epa.gov/src/cachejson/{REGION}/{kind}/{collection_id}"
            record: dict[str, object] = {"kind": kind, "collection_id": collection_id, "url": url}
            try:
                response = requests.get(url, headers=headers, timeout=120)
                record["status_code"] = response.status_code
                response.raise_for_status()
                payload = response.json()
                record["meta"] = payload.get("meta", {})
                documents = payload.get("data", [])
                record["document_count"] = len(documents)
                matches: list[dict[str, object]] = []
                for document in documents:
                    text = " ".join(str(value) for value in document.values()).lower()
                    found = [term for term in TARGET_TERMS if term in text]
                    if found:
                        matches.append({"matches": found, "document": document})
                record["target_matches"] = matches
                (output / f"collection_{kind}_{collection_id}.json").write_text(
                    json.dumps(payload, indent=2), encoding="utf-8"
                )
            except Exception as exc:
                record["error"] = str(exc)
            records.append(record)
    return records


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "consolidated_iron_sems_search"
    output.mkdir(parents=True, exist_ok=True)
    searches = asyncio.run(discover(output))
    (output / "search_records.json").write_text(json.dumps(searches, indent=2), encoding="utf-8")
    collections = inspect_collections(searches, output)
    report = {
        "status": "CONSOLIDATED_IRON_FULL_SEMS_COLLECTION_SEARCH_COMPLETE",
        "epa_id": EPA_ID,
        "search_records": searches,
        "collection_records": collections,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "decision": "HOLD_UNTIL_FINAL_RAR_OR_EQUIVALENT_MEASURED_DEPTH_SURVEY_IS_RECOVERED",
    }
    (output / "search_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "SEARCH_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
