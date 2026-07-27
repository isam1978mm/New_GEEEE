"""Recover public IDEM VFC records for Hoosier #1 Landfill.

The search is narrowly limited to SW Program ID 43-01 and environmental closure
records: final-cover plans, closure certification, CQA, as-built surveys, and
post-closure reports. It does not call Earth Engine, create calibration rows,
train a model, or enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

START_URLS = (
    "https://vfc.idem.in.gov/",
    "https://www.in.gov/idem/legal/public-records/virtual-file-cabinet/",
)
SEARCH_VALUES = (
    "43-01",
    "Hoosier #1 Landfill",
    "Hoosier 1 Landfill",
    "2710 E. 800 South",
)
RELEVANT_TERMS = (
    "closure certification",
    "final closure",
    "final cover",
    "construction quality assurance",
    "cqa",
    "as-built",
    "as built",
    "survey",
    "composite cover",
    "soil cover",
    "post-closure",
    "post closure",
    "closure approval",
)
MAX_DOWNLOADS = 50
MAX_BYTES = 350 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def relevance(text: str) -> int:
    lower = text.lower()
    weights = {
        "closure certification": 100,
        "final closure": 80,
        "construction quality assurance": 75,
        "as-built": 70,
        "as built": 70,
        "final cover": 60,
        "closure approval": 55,
        "composite cover": 45,
        "soil cover": 40,
        "survey": 35,
        "cqa": 30,
        "post-closure": 20,
        "post closure": 20,
        "43-01": 10,
        "hoosier": 10,
    }
    return sum(weight for token, weight in weights.items() if token in lower)


def page_snapshot(page) -> dict[str, object]:
    return page.evaluate(
        """() => ({
          url: location.href,
          title: document.title,
          bodyText: (document.body?.innerText || '').replace(/\s+/g, ' ').slice(0, 300000),
          selects: Array.from(document.querySelectorAll('select')).map((el, i) => ({
            index: i,
            name: el.name || '',
            id: el.id || '',
            aria: el.getAttribute('aria-label') || '',
            options: Array.from(el.options).map(o => ({text: (o.textContent || '').trim(), value: o.value}))
          })),
          inputs: Array.from(document.querySelectorAll('input')).map((el, i) => ({
            index: i,
            type: el.type || '',
            name: el.name || '',
            id: el.id || '',
            placeholder: el.placeholder || '',
            aria: el.getAttribute('aria-label') || ''
          })),
          buttons: Array.from(document.querySelectorAll('button,input[type=submit],input[type=button]')).map((el, i) => ({
            index: i,
            text: (el.innerText || el.value || el.title || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(),
            id: el.id || '',
            name: el.name || ''
          })),
          rows: Array.from(document.querySelectorAll('table tbody tr, [role=row]')).slice(0, 5000).map(row => ({
            text: (row.innerText || '').replace(/\s+/g, ' ').trim(),
            links: Array.from(row.querySelectorAll('a')).map(a => ({
              text: (a.innerText || '').replace(/\s+/g, ' ').trim(),
              href: a.href || a.getAttribute('href') || '',
              onclick: a.getAttribute('onclick') || ''
            }))
          })).filter(row => row.text)
        })"""
    )


def choose_program_select(page) -> bool:
    selects = page.locator("select")
    for index in range(selects.count()):
        select = selects.nth(index)
        try:
            options = select.locator("option").all_text_contents()
        except Exception:
            continue
        for option_index, text in enumerate(options):
            normalized = clean(text).lower()
            if "sw program" in normalized or ("solid waste" in normalized and "id" in normalized):
                select.select_option(index=option_index)
                return True
    return False


def fill_best_input(page, value: str) -> bool:
    inputs = page.locator("input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio])")
    preferred: list[int] = []
    fallback: list[int] = []
    for index in range(inputs.count()):
        field = inputs.nth(index)
        metadata = " ".join(
            filter(
                None,
                [
                    field.get_attribute("name"),
                    field.get_attribute("id"),
                    field.get_attribute("placeholder"),
                    field.get_attribute("aria-label"),
                ],
            )
        ).lower()
        if any(token in metadata for token in ("quick", "search", "value", "program", "id")):
            preferred.append(index)
        else:
            fallback.append(index)
    for index in preferred + fallback:
        field = inputs.nth(index)
        try:
            if field.is_visible() and field.is_enabled():
                field.fill(value, timeout=8000)
                return True
        except Exception:
            continue
    return False


def click_search(page) -> bool:
    candidates = (
        "button:has-text('Search')",
        "input[type=submit][value*='Search' i]",
        "input[type=button][value*='Search' i]",
        "button[aria-label*='Search' i]",
        "button[title*='Search' i]",
        "[role=button][aria-label*='Search' i]",
    )
    for selector in candidates:
        locator = page.locator(selector)
        for index in range(locator.count()):
            button = locator.nth(index)
            try:
                if button.is_visible() and button.is_enabled():
                    button.click(timeout=10000)
                    return True
            except Exception:
                continue
    return False


def clear_visible_inputs(page) -> None:
    fields = page.locator("input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio])")
    for index in range(fields.count()):
        field = fields.nth(index)
        try:
            if field.is_visible() and field.is_enabled():
                field.fill("")
        except Exception:
            pass


def open_vfc(page) -> None:
    last_error: Exception | None = None
    for url in START_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(6000)
            if "in.gov/idem/legal" in page.url:
                links = page.locator("a:has-text('Virtual File Cabinet')")
                if links.count():
                    links.first.click(timeout=15000)
                    page.wait_for_timeout(8000)
            return
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error


def extract_urls(base_url: str, link: dict[str, str]) -> list[str]:
    combined = f"{link.get('href', '')} {link.get('onclick', '')}"
    values: list[str] = []
    if link.get("href"):
        values.append(urljoin(base_url, link["href"]))
    for pattern in (
        r"https?://[^\s'\"<>]+",
        r"['\"]([^'\"]+(?:GET_FILE|GetFile|download|document|\.pdf)[^'\"]*)['\"]",
    ):
        for match in re.finditer(pattern, combined, re.I):
            values.append(urljoin(base_url, match.group(1) if match.lastindex else match.group(0)))
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def download(context, url: str, destination: Path) -> dict[str, object]:
    response = context.request.get(
        url,
        headers={"Referer": "https://vfc.idem.in.gov/", "Accept": "application/pdf,text/html,*/*"},
        timeout=180000,
        fail_on_status_code=False,
    )
    body = response.body()
    if len(body) > MAX_BYTES:
        return {"url": response.url, "status": response.status, "skipped": "size_limit", "size_bytes": len(body)}
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(body)
    return {
        "url": response.url,
        "status": response.status,
        "content_type": content_type,
        "size_bytes": len(body),
        "is_pdf": is_pdf,
        "sha256": hashlib.sha256(body).hexdigest(),
        "saved_path": str(path),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "hoosier1_vfc"
    output.mkdir(parents=True, exist_ok=True)
    downloads_dir = output / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "queries": [],
        "ranked_rows": [],
        "candidate_urls": [],
        "download_attempts": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            accept_downloads=True,
        )
        page = context.new_page()
        network: list[dict[str, object]] = []

        def on_response(response) -> None:
            content_type = response.headers.get("content-type", "").lower()
            lower = response.url.lower()
            if any(token in lower for token in ("search", "query", "ecm.idem", "idcplg", "document", "vfc")) or "json" in content_type or "pdf" in content_type:
                network.append({"url": response.url, "status": response.status, "content_type": content_type})

        page.on("response", on_response)
        open_vfc(page)
        page.wait_for_timeout(5000)
        report["initial_snapshot"] = page_snapshot(page)
        page.screenshot(path=str(output / "initial.png"), full_page=True)
        (output / "initial.html").write_text(page.content(), encoding="utf-8")

        all_rows: dict[str, dict[str, object]] = {}
        for value in SEARCH_VALUES:
            clear_visible_inputs(page)
            selected_program = choose_program_select(page)
            filled = fill_best_input(page, value)
            clicked = click_search(page)
            if not clicked and filled:
                try:
                    page.keyboard.press("Enter")
                    clicked = True
                except Exception:
                    pass
            page.wait_for_timeout(6000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass
            snap = page_snapshot(page)
            rows = snap.get("rows", [])
            report["queries"].append(
                {
                    "value": value,
                    "selected_sw_program_id": selected_program,
                    "input_filled": filled,
                    "search_triggered": clicked,
                    "page_url": page.url,
                    "row_count": len(rows),
                    "snapshot": snap,
                }
            )
            for row in rows:
                text = str(row.get("text", ""))
                row_score = relevance(text)
                if row_score <= 0 and "43-01" not in text and "hoosier" not in text.lower():
                    continue
                key = text + json.dumps(row.get("links", []), sort_keys=True)
                existing = all_rows.get(key)
                if not existing or row_score > int(existing["score"]):
                    all_rows[key] = {**row, "score": row_score, "query": value, "page_url": page.url}

        ranked = sorted(all_rows.values(), key=lambda item: (-int(item["score"]), str(item["text"])))
        report["ranked_rows"] = ranked
        urls: list[dict[str, object]] = []
        seen_urls: set[str] = set()
        for row in ranked:
            for link in row.get("links", []):
                for url in extract_urls(str(row.get("page_url") or page.url), link):
                    if url not in seen_urls:
                        seen_urls.add(url)
                        urls.append({"url": url, "row_text": row.get("text"), "score": row.get("score")})
        for item in network:
            url = str(item.get("url", ""))
            if ("pdf" in str(item.get("content_type", "")).lower() or "get_file" in url.lower()) and url not in seen_urls:
                seen_urls.add(url)
                urls.append({"url": url, "row_text": "captured network response", "score": 0})
        report["candidate_urls"] = urls

        for index, item in enumerate(urls[:MAX_DOWNLOADS], start=1):
            try:
                record = download(context, str(item["url"]), downloads_dir / f"{index:03d}_{safe_name(Path(urlparse(str(item['url'])).path).name or 'document')}")
                record.update({"row_text": item.get("row_text"), "score": item.get("score")})
                report["download_attempts"].append(record)
            except Exception as exc:
                report["download_attempts"].append({**item, "error": repr(exc)})
        report["network_responses"] = network
        browser.close()

    pdf_count = sum(bool(item.get("is_pdf")) for item in report["download_attempts"])
    report["recovered_pdf_count"] = pdf_count
    report["status"] = "RECOVERED" if pdf_count else "NO_PUBLIC_PDF_RECOVERED"
    report["decision"] = "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION"
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
