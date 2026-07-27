"""Targeted public-record recovery for RMA South Plants BOA environmental designs.

This fast pass searches archived public URL patterns and follows only links whose
text or URL matches the cited South Plants environmental design records. It does
not call Earth Engine, create calibration rows, train a model, or enable app
numeric depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "text/html,application/pdf,*/*",
}
TIMEOUT = 45
MAX_ARCHIVE_ROWS = 120
MAX_HTML_PAGES = 50
MAX_DOCUMENTS = 24
MAX_BYTES = 220 * 1024 * 1024

PATTERNS = (
    "*south*",
    "*South*",
    "*SPBOA*",
    "*spboa*",
    "*SPBA*",
    "*spba*",
    "*balance*",
    "*Balance*",
    "*central*processing*",
    "*Central*Processing*",
    "*FWENC*",
    "*fwenc*",
)
PHRASES = (
    "south plants balance of areas",
    "south plants central processing area",
    "south plants soil remediation project",
    "phase 2",
    "100 percent design package",
    "explanation of significant differences",
    "integrated cover system design",
    "remedial action report",
    "construction completion",
    "as-built",
    "as built",
)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def score(value: str) -> int:
    lower = value.lower()
    weights = {
        "south plants balance of areas": 120,
        "south plants central processing area": 90,
        "south plants soil remediation project": 80,
        "100 percent design package": 70,
        "explanation of significant differences": 65,
        "integrated cover system design": 55,
        "remedial action report": 50,
        "construction completion": 45,
        "as-built": 40,
        "as built": 40,
        "spboa": 35,
        "spba": 25,
        "fwenc": 20,
        "phase 2": 15,
    }
    return sum(weight for token, weight in weights.items() if token in lower)


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:170] or "document")


def get(session: requests.Session, url: str, *, stream: bool = False) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True, stream=stream)
    response.raise_for_status()
    return response


def cdx_urls() -> list[str]:
    result: list[str] = []
    for host in ("rma.army.mil", "www.rma.army.mil"):
        for pattern in PATTERNS:
            target = quote(f"{host}/{pattern}", safe="")
            result.append(
                "https://web.archive.org/cdx/search/cdx"
                f"?url={target}&output=json&fl=timestamp,original,statuscode,mimetype,digest,length"
                "&filter=statuscode:200&collapse=digest&from=1999&to=2012"
            )
    return result


def query_cdx(session: requests.Session, output: Path) -> list[dict[str, object]]:
    records: dict[tuple[str, str], dict[str, object]] = {}
    log: list[dict[str, object]] = []
    for url in cdx_urls():
        try:
            response = get(session, url)
            payload = response.json()
            rows = payload[1:] if isinstance(payload, list) and payload else []
            log.append({"url": url, "row_count": len(rows)})
            for row in rows[:MAX_ARCHIVE_ROWS]:
                if len(row) < 6:
                    continue
                timestamp, original, status, mimetype, digest, length = row[:6]
                key = (original, digest)
                records[key] = {
                    "timestamp": timestamp,
                    "original": original,
                    "statuscode": status,
                    "mimetype": mimetype,
                    "digest": digest,
                    "length": length,
                    "score": score(original),
                    "archive_url": f"https://web.archive.org/web/{timestamp}id_/{original}",
                }
        except Exception as exc:
            log.append({"url": url, "error": repr(exc)})
    ranked = sorted(records.values(), key=lambda item: (-int(item["score"]), str(item["original"])))
    (output / "cdx_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    (output / "cdx_records.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    return ranked


def extract_links(base_url: str, html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    visible = clean(soup.get_text(" "))
    result: list[dict[str, object]] = []
    for tag in soup.find_all("a", href=True):
        url = urljoin(base_url, tag.get("href"))
        anchor = clean(tag.get_text(" "))
        combined = f"{anchor} {url}"
        relevance = score(combined)
        if relevance > 0 or any(token in combined.lower() for token in ("south", "spboa", "spba", "fwenc")):
            result.append({"url": url, "anchor": anchor, "score": relevance})
    return [{"page_score": score(visible), **item} for item in result]


def inspect_archived_pages(session: requests.Session, output: Path, records: list[dict[str, object]]) -> list[dict[str, object]]:
    pages = [item for item in records if "html" in str(item.get("mimetype", "")).lower()]
    pages = sorted(pages, key=lambda item: (-int(item["score"]), str(item["original"])))[:MAX_HTML_PAGES]
    findings: list[dict[str, object]] = []
    for item in pages:
        try:
            response = get(session, str(item["archive_url"]))
            links = extract_links(response.url, response.text)
            findings.append({**item, "final_url": response.url, "links": links})
        except Exception as exc:
            findings.append({**item, "error": repr(exc)})
    (output / "archived_page_links.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    return findings


def pdf_text(path: Path) -> dict[str, object]:
    txt = path.with_suffix(".txt")
    process = subprocess.run(
        ["pdftotext", "-layout", str(path), str(txt)],
        capture_output=True,
        text=True,
        check=False,
    )
    text = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
    return {
        "returncode": process.returncode,
        "stderr": process.stderr[-3000:],
        "text_path": str(txt),
        "text_size_bytes": len(text.encode("utf-8")),
        "score": score(text),
        "matching_phrases": [phrase for phrase in PHRASES if phrase in text.lower()],
    }


def download(session: requests.Session, url: str, path: Path) -> dict[str, object]:
    response = get(session, url, stream=True)
    expected = int(response.headers.get("content-length") or 0)
    if expected and expected > MAX_BYTES:
        return {"url": url, "skipped": "content_length_limit", "content_length": expected}
    data = bytearray()
    for chunk in response.iter_content(1024 * 1024):
        if chunk:
            data.extend(chunk)
        if len(data) > MAX_BYTES:
            return {"url": url, "skipped": "stream_size_limit", "size_bytes": len(data)}
    raw = bytes(data)
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = raw.startswith(b"%PDF-") or "application/pdf" in content_type
    suffix = ".pdf" if is_pdf else ".html"
    saved = path.with_suffix(suffix)
    saved.write_bytes(raw)
    item: dict[str, object] = {
        "url": response.url,
        "content_type": content_type,
        "size_bytes": len(raw),
        "is_pdf": is_pdf,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "saved_path": str(saved),
    }
    if is_pdf:
        item["text_extraction"] = pdf_text(saved)
    else:
        text = clean(BeautifulSoup(raw, "html.parser").get_text(" "))
        item["score"] = score(text)
    return item


def recover(session: requests.Session, output: Path, records: list[dict[str, object]], pages: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[tuple[int, str]] = []
    for item in records:
        original = str(item["original"])
        if "pdf" in str(item.get("mimetype", "")).lower() or original.lower().endswith(".pdf"):
            candidates.append((int(item["score"]), str(item["archive_url"])))
    for page in pages:
        for link in page.get("links", []):
            candidates.append((int(link.get("score", 0)) + int(link.get("page_score", 0)), str(link["url"])))

    unique: dict[str, int] = {}
    for relevance, url in sorted(candidates, reverse=True):
        unique[url] = max(relevance, unique.get(url, -1))

    folder = output / "recovered"
    folder.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for index, (url, relevance) in enumerate(sorted(unique.items(), key=lambda item: (-item[1], item[0]))[:MAX_DOCUMENTS], start=1):
        name = safe_name(Path(urlparse(url).path).name or f"candidate_{index}")
        try:
            item = download(session, url, folder / f"{index:03d}_{relevance}_{name}")
            item["initial_score"] = relevance
            results.append(item)
        except Exception as exc:
            results.append({"url": url, "initial_score": relevance, "error": repr(exc)})
    (output / "downloads.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "rma_south_plants_boa_fast"
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    records = query_cdx(session, output)
    pages = inspect_archived_pages(session, output, records)
    downloads = recover(session, output, records, pages)
    pdfs = [item for item in downloads if item.get("is_pdf")]
    relevant = [item for item in pdfs if int((item.get("text_extraction") or {}).get("score", 0)) >= 60]
    report = {
        "status": "RECOVERED_CANDIDATES" if pdfs else "NO_PDF_RECOVERED",
        "target_records": [
            "2000 South Plants BOA/CPA Explanation of Significant Differences",
            "2001 South Plants BOA/CPA Phase 2 100 Percent Design Package",
            "South Plants BOA construction completion or as-built records",
        ],
        "cdx_record_count": len(records),
        "archived_page_count": len(pages),
        "download_count": len(downloads),
        "recovered_pdf_count": len(pdfs),
        "high_relevance_pdf_count": len(relevant),
        "high_relevance_documents": relevant,
        "decision": "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION",
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if pdfs else 1


if __name__ == "__main__":
    raise SystemExit(main())
