"""Discover all SEMS public collections for Consolidated Iron and Metal.

The site profile exposes only four key documents. This one-off utility submits
EPA's full Records Collections search for Region 2 by EPA ID, captures Special
Collection and Administrative Record results, and inspects discovered collection
JSON for the Final Remedial Action Report, Site Management Plan, as-built
surveys, and related construction records. It does not call Earth Engine or
create calibration records.
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


def option_for(options: list[dict[str, str]], needles: tuple[str, ...]) -> str | None:
    for option in options:
        text = option.get("text", "").lower()
        value = option.get("value", "")
        if all(needle.lower() in text for needle in needles):
            return value
    return None


async def submit_search(page, collection_kind: str, output: Path) -> dict[str, object]:  # noqa: ANN001
    await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=120_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=45_000)
    except Exception:
        pass
    await page.wait_for_timeout(3_000)

    controls = await page.evaluate(
        """() => ({
          selects: [...document.querySelectorAll('select')].map(s => ({
            id:s.id, name:s.name,
            options:[...s.options].map(o => ({text:(o.textContent||'').trim(), value:o.value}))
          })),
          inputs: [...document.querySelectorAll('input')].map(i => ({
            id:i.id, name:i.name, type:i.type, value:i.value,
            placeholder:i.placeholder||'', aria:i.getAttribute('aria-label')||''
          })),
          buttons: [...document.querySelectorAll('button,input[type=submit],input[type=button]')].map(b => ({
            id:b.id, name:b.name, type:b.type, value:b.value||'', text:(b.innerText||b.textContent||'').trim()
          })),
          labels: [...document.querySelectorAll('label')].map(l => ({for:l.htmlFor, text:(l.innerText||l.textContent||'').trim()}))
        })"""
    )
    (output / f"search_controls_{collection_kind}.json").write_text(
        json.dumps(controls, indent=2), encoding="utf-8"
    )

    region_select = None
    type_select = None
    for select in controls["selects"]:
        texts = " ".join(option["text"].lower() for option in select["options"])
        if "region 2" in texts or "region ii" in texts:
            region_select = select
        if "special collection" in texts and "administrative record" in texts:
            type_select = select
    if not region_select or not type_select:
        raise RuntimeError("Could not identify SEMS region and collection-type controls")

    region_value = option_for(region_select["options"], ("region", "2"))
    if region_value is None:
        # Fallback to a value or text containing 02.
        for option in region_select["options"]:
            if option["value"] in {"2", "02"} or " 2" in option["text"]:
                region_value = option["value"]
                break
    kind_needles = ("special",) if collection_kind == "SC" else ("administrative",)
    type_value = option_for(type_select["options"], kind_needles)
    if region_value is None or type_value is None:
        raise RuntimeError(f"Could not resolve search options for {collection_kind}")

    await page.select_option(f"select#{region_select['id']}", value=region_value)
    await page.select_option(f"select#{type_select['id']}", value=type_value)
    await page.wait_for_timeout(1_000)

    # Locate the EPA-ID input by associated label/row text, then robust fallbacks.
    epa_input_id = None
    for label in controls["labels"]:
        if "epa id" in label["text"].lower() and label.get("for"):
            epa_input_id = label["for"]
            break
    if not epa_input_id:
        candidates = await page.locator("text=/EPA ID/i").all()
        for candidate in candidates:
            try:
                row = candidate.locator("xpath=ancestor::*[self::tr or self::div][1]")
                inp = row.locator("input[type=text]").first
                if await inp.count():
                    epa_input_id = await inp.get_attribute("id")
                    break
            except Exception:
                continue
    if not epa_input_id:
        for item in controls["inputs"]:
            blob = " ".join(str(item.get(key, "")) for key in ("id", "name", "placeholder", "aria")).lower()
            if item.get("type") in {"text", "search", ""} and "epa" in blob:
                epa_input_id = item["id"]
                break
    if not epa_input_id:
        # Last fallback: use the last visible text input, which is the EPA-ID field on this form.
        visible = page.locator("input[type=text]:visible")
        count = await visible.count()
        if count:
            epa_input_id = await visible.nth(count - 1).get_attribute("id")
    if not epa_input_id:
        raise RuntimeError("Could not identify EPA-ID input")
    await page.fill(f"#{epa_input_id}", EPA_ID)

    # Prefer a visible Search/Submit button, otherwise submit the enclosing form.
    submitted = False
    for selector in ("button:has-text('Search')", "input[type=submit][value*='Search' i]", "input[type=submit]:visible"):
        locator = page.locator(selector).first
        if await locator.count():
            try:
                await locator.click(timeout=10_000)
                submitted = True
                break
            except Exception:
                pass
    if not submitted:
        await page.evaluate(
            "id => { const el=document.getElementById(id); if(!el||!el.form) throw new Error('No form'); el.form.submit(); }",
            epa_input_id,
        )

    try:
        await page.wait_for_load_state("networkidle", timeout=60_000)
    except Exception:
        pass
    await page.wait_for_timeout(8_000)
    html = await page.content()
    (output / f"search_results_{collection_kind}.html").write_text(html, encoding="utf-8")
    anchors = await page.eval_on_selector_all(
        "a",
        "els => els.map(a => ({text:(a.innerText||a.textContent||'').trim(), href:a.href||''}))",
    )
    body_text = await page.locator("body").inner_text()
    ids = sorted(set(re.findall(r"(?:colid=|Collection ID\s*[:#]?\s*)(\d{4,})", html + "\n" + body_text, re.I)))
    for anchor in anchors:
        query = parse_qs(urlparse(anchor["href"]).query)
        ids.extend(query.get("colid", []))
    ids = sorted(set(ids))
    return {
        "collection_kind": collection_kind,
        "final_url": page.url,
        "collection_ids": ids,
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
