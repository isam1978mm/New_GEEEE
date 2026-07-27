"""Search Ohio EPA eDocument for full-scale vegetated cap certification records.

One-off public-record scout. It uses a browser because the Ohio EPA portal is a
JavaScript-backed search form. It records portal structure, submits bounded
full-text searches for final-cap certification evidence, and saves result rows
and links for manual review.

It does not call Earth Engine, create calibration rows, train a model, or enable
numeric depth output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

PORTAL = "https://edocpub.epa.ohio.gov/publicportal/"
SEARCH_TERMS = (
    '"cap protection layer"',
    '"construction certification report" "composite cap"',
    '"final closure certification" landfill',
    '"as-built" "cap protection layer"',
)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def element_inventory(page: Page) -> list[dict[str, Any]]:
    return page.locator("input, select, textarea, button, a").evaluate_all(
        """els => els.map((el, i) => ({
          index: i,
          tag: el.tagName,
          type: el.getAttribute('type'),
          id: el.id || null,
          name: el.getAttribute('name'),
          value: el.getAttribute('value'),
          text: (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim(),
          placeholder: el.getAttribute('placeholder'),
          href: el.href || null,
          ariaLabel: el.getAttribute('aria-label'),
          title: el.getAttribute('title'),
          outerHTML: el.outerHTML.slice(0, 1200)
        }))"""
    )


def locate_full_text_input(page: Page):
    # Prefer an input associated with the visible "Search For This" label.
    label = page.get_by_text("Search For This", exact=False).first
    if label.count():
        candidate = label.locator("xpath=following::input[not(@type='hidden')][1]")
        if candidate.count():
            return candidate

    # Fallback: score visible text inputs by nearby parent text.
    candidates = page.locator("input:not([type='hidden']):not([type='submit']):not([type='button'])")
    best = None
    best_score = -1
    for i in range(candidates.count()):
        item = candidates.nth(i)
        if not item.is_visible():
            continue
        nearby = clean(item.locator("xpath=ancestor::*[self::td or self::div or self::form][1]").inner_text())
        attrs = " ".join(
            filter(
                None,
                [
                    item.get_attribute("id"),
                    item.get_attribute("name"),
                    item.get_attribute("placeholder"),
                    item.get_attribute("title"),
                    nearby,
                ],
            )
        ).lower()
        score = 0
        for token, weight in (("full text", 12), ("search for this", 12), ("search", 5), ("text", 2)):
            if token in attrs:
                score += weight
        if score > best_score:
            best_score = score
            best = item
    if best is None:
        raise RuntimeError("Could not identify the full-text search input")
    return best


def click_search(page: Page) -> None:
    for pattern in (re.compile(r"^search$", re.I), re.compile(r"search", re.I)):
        buttons = page.get_by_role("button", name=pattern)
        if buttons.count():
            buttons.first.click()
            return
    for selector in (
        "input[type='submit'][value*='Search' i]",
        "input[type='button'][value*='Search' i]",
        "button:has-text('Search')",
    ):
        item = page.locator(selector)
        if item.count():
            item.first.click()
            return
    raise RuntimeError("Could not identify the portal Search button")


def extract_results(page: Page) -> dict[str, Any]:
    rows = page.locator("table tr")
    row_texts: list[str] = []
    for i in range(rows.count()):
        text = clean(rows.nth(i).inner_text())
        if text:
            row_texts.append(text)

    links = page.locator("a[href]").evaluate_all(
        """els => els.map(el => ({
          text: (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim(),
          href: el.href
        }))"""
    )
    relevant_links = [
        link
        for link in links
        if any(
            token in f"{link.get('text', '')} {link.get('href', '')}".lower()
            for token in ("document", "download", "view", "pdf", "edoc")
        )
    ]
    return {
        "url": page.url,
        "title": page.title(),
        "body_text": clean(page.locator("body").inner_text())[:100000],
        "table_rows": row_texts[:1000],
        "relevant_links": relevant_links[:1000],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "ohio_full_scale_cap_records"
    output.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "status": "OHIO_PORTAL_SCOUT_STARTED",
        "portal": PORTAL,
        "search_terms": list(SEARCH_TERMS),
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "results": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5000)
        (output / "portal_initial.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=output / "portal_initial.png", full_page=True)
        (output / "element_inventory.json").write_text(
            json.dumps(element_inventory(page), indent=2), encoding="utf-8"
        )

        for index, term in enumerate(SEARCH_TERMS, start=1):
            try:
                page.goto(PORTAL, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(3500)
                search_input = locate_full_text_input(page)
                search_input.fill(term)
                click_search(page)
                page.wait_for_timeout(10000)
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass
                result = extract_results(page)
                result["term"] = term
                result["status"] = "SEARCH_COMPLETED"
                report["results"].append(result)
                (output / f"search_{index:02d}.html").write_text(page.content(), encoding="utf-8")
                page.screenshot(path=output / f"search_{index:02d}.png", full_page=True)
            except Exception as exc:
                report["results"].append(
                    {"term": term, "status": "SEARCH_FAILED", "error": repr(exc), "url": page.url}
                )
                page.screenshot(path=output / f"search_{index:02d}_failure.png", full_page=True)

        browser.close()

    completed = sum(item.get("status") == "SEARCH_COMPLETED" for item in report["results"])
    report["status"] = "OHIO_PORTAL_SCOUT_COMPLETE" if completed else "OHIO_PORTAL_SCOUT_FAILED"
    report["completed_search_count"] = completed
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "scout_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
