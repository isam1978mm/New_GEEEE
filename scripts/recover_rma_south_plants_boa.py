"""Recover public Rocky Mountain Arsenal South Plants environmental records.

The search is narrowly limited to the cited South Plants Balance of Areas (BOA)
and Central Processing Area (CPA) ESD, design, construction, and as-built
records. It searches current U.S. Army public pages and archived copies of the
former public RMA website. It does not call Earth Engine, create calibration
rows, train a model, or enable app depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from collections import deque
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

CURRENT_ROOT = "https://home.army.mil/carson/rma/"
CURRENT_SEEDS = (
    "https://home.army.mil/carson/rma/documents",
    "https://home.army.mil/carson/rma/documents/Fact-Sheets",
    "https://home.army.mil/carson/rma/documents/Five-Year-Reviews",
    "https://home.army.mil/carson/rma/environmental-cleanup",
)
SEARCH_PHRASES = (
    "South Plants Balance of Areas",
    "South Plants Central Processing Area",
    "South Plants Soil Remediation Project",
    "100 Percent Design Package",
    "Explanation of Significant Differences South Plants",
    "Integrated Cover System Design South Plants",
    "South Plants remedial action completion",
    "South Plants as-built",
)
KEYWORDS = (
    "south plants",
    "balance of areas",
    "central processing area",
    "soil remediation project",
    "100 percent design",
    "explanation of significant differences",
    "integrated cover system",
    "construction completion",
    "remedial action report",
    "as-built",
    "as built",
)
URL_KEYWORDS = (
    "south",
    "plants",
    "balance",
    "boa",
    "central",
    "processing",
    "cpa",
    "soil",
    "remed",
    "design",
    "cover",
    "esd",
    "phase",
    "completion",
    "asbuilt",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "text/html,application/pdf,*/*",
}
TIMEOUT = 180
MAX_CURRENT_PAGES = 120
MAX_ARCHIVE_DOWNLOADS = 50
MAX_PDF_BYTES = 350 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return value[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def score_text(text: str) -> int:
    lower = text.lower()
    score = 0
    weights = {
        "south plants balance of areas": 100,
        "south plants central processing area": 70,
        "100 percent design": 60,
        "explanation of significant differences": 50,
        "integrated cover system": 45,
        "construction completion": 40,
        "remedial action report": 40,
        "as-built": 35,
        "as built": 35,
        "soil remediation project": 30,
    }
    for token, weight in weights.items():
        if token in lower:
            score += weight
    return score


def score_url(url: str) -> int:
    lower = url.lower()
    return sum(8 for token in URL_KEYWORDS if token in lower) + score_text(lower)


def request(session: requests.Session, url: str, *, stream: bool = False) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True, stream=stream)
    response.raise_for_status()
    return response


def extract_links(base_url: str, html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    result: list[dict[str, str]] = []
    for tag in soup.find_all("a", href=True):
        href = urljoin(base_url, tag.get("href"))
        result.append({"url": href, "anchor": clean(tag.get_text(" "))})
    return result


def current_search_urls() -> list[str]:
    urls: list[str] = []
    for phrase in SEARCH_PHRASES:
        encoded = quote_plus(phrase)
        urls.extend(
            [
                f"https://home.army.mil/carson/search?query={encoded}",
                f"https://home.army.mil/carson/search?search_paths%5B%5D=&query={encoded}&submit=Search",
            ]
        )
    return urls


def crawl_current_site(session: requests.Session, output: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    queue = deque((*CURRENT_SEEDS, *current_search_urls()))
    seen: set[str] = set()
    pages: list[dict[str, object]] = []
    document_links: dict[str, dict[str, str]] = {}

    while queue and len(seen) < MAX_CURRENT_PAGES:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            response = request(session, url)
            content_type = response.headers.get("content-type", "").lower()
            body = response.content
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            record: dict[str, object] = {
                "url": response.url,
                "status": response.status_code,
                "content_type": content_type,
                "size_bytes": len(body),
                "is_pdf": is_pdf,
            }
            if is_pdf:
                record["score"] = score_url(response.url)
                document_links[response.url] = {"url": response.url, "anchor": "direct PDF"}
            else:
                text = response.text
                visible = clean(BeautifulSoup(text, "html.parser").get_text(" "))
                record["score"] = score_text(visible) + score_url(response.url)
                record["matching_phrases"] = [token for token in KEYWORDS if token in visible.lower()]
                links = extract_links(response.url, text)
                for item in links:
                    parsed = urlparse(item["url"])
                    if parsed.scheme not in {"http", "https"}:
                        continue
                    lower = item["url"].lower()
                    if (
                        "/download_file/view/" in lower
                        or lower.endswith(".pdf")
                        or "rma.army.mil" in parsed.netloc.lower()
                    ):
                        document_links[item["url"]] = item
                    if item["url"].startswith(CURRENT_ROOT) and item["url"] not in seen:
                        queue.append(item["url"])
            pages.append(record)
        except Exception as exc:
            pages.append({"url": url, "error": repr(exc)})

    (output / "current_pages.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")
    ranked = sorted(document_links.values(), key=lambda item: (-score_text(item["anchor"]), -score_url(item["url"]), item["url"]))
    (output / "current_document_links.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    return pages, ranked


def cdx_queries() -> list[str]:
    hosts = ("rma.army.mil", "www.rma.army.mil")
    wildcards = (
        "*south*",
        "*South*",
        "*plant*",
        "*balance*",
        "*soil*remed*",
        "*cover*design*",
        "*.pdf",
    )
    urls: list[str] = []
    for host in hosts:
        for wildcard in wildcards:
            target = quote_plus(f"{host}/{wildcard}")
            urls.append(
                "https://web.archive.org/cdx/search/cdx"
                f"?url={target}&output=json&fl=timestamp,original,statuscode,mimetype,digest,length"
                "&filter=statuscode:200&collapse=digest&from=1999&to=2012"
            )
    return urls


def query_wayback(session: requests.Session, output: Path) -> list[dict[str, object]]:
    records: dict[tuple[str, str], dict[str, object]] = {}
    query_log: list[dict[str, object]] = []
    for url in cdx_queries():
        try:
            response = request(session, url)
            payload = response.json()
            rows = payload[1:] if isinstance(payload, list) and payload else []
            query_log.append({"url": url, "status": response.status_code, "row_count": len(rows)})
            for row in rows:
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
                    "score": score_url(original),
                    "archive_url": f"https://web.archive.org/web/{timestamp}id_/{original}",
                }
        except Exception as exc:
            query_log.append({"url": url, "error": repr(exc)})
        time.sleep(0.2)

    ranked = sorted(records.values(), key=lambda item: (-int(item["score"]), item["original"]))
    (output / "wayback_query_log.json").write_text(json.dumps(query_log, indent=2), encoding="utf-8")
    (output / "wayback_ranked_records.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    return ranked


def extract_pdf_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    process = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    return {
        "returncode": process.returncode,
        "stderr": process.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "score": score_text(text),
        "matching_phrases": [token for token in KEYWORDS if token in text.lower()],
    }


def download_candidate(session: requests.Session, url: str, destination: Path) -> dict[str, object]:
    response = request(session, url, stream=True)
    content_length = int(response.headers.get("content-length") or 0)
    if content_length and content_length > MAX_PDF_BYTES:
        return {"url": url, "skipped": "content_length_limit", "content_length": content_length}
    data = bytearray()
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if not chunk:
            continue
        data.extend(chunk)
        if len(data) > MAX_PDF_BYTES:
            return {"url": url, "skipped": "stream_size_limit", "size_bytes": len(data)}
    raw = bytes(data)
    content_type = response.headers.get("content-type", "").lower()
    is_pdf = raw.startswith(b"%PDF-") or "application/pdf" in content_type
    suffix = ".pdf" if is_pdf else ".html"
    path = destination.with_suffix(suffix)
    path.write_bytes(raw)
    record: dict[str, object] = {
        "url": response.url,
        "content_type": content_type,
        "size_bytes": len(raw),
        "is_pdf": is_pdf,
        "sha256": sha256(raw),
        "saved_path": str(path),
    }
    if is_pdf:
        record["text_extraction"] = extract_pdf_text(path)
    else:
        visible = clean(BeautifulSoup(raw, "html.parser").get_text(" "))
        record["score"] = score_text(visible)
        record["matching_phrases"] = [token for token in KEYWORDS if token in visible.lower()]
    return record


def recover_documents(
    session: requests.Session,
    output: Path,
    current_links: list[dict[str, str]],
    archive_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates: list[tuple[int, str, str]] = []
    for item in current_links:
        score = score_text(item["anchor"]) + score_url(item["url"])
        if score > 0:
            candidates.append((score, "current", item["url"]))
    for item in archive_records:
        score = int(item["score"])
        if score > 0:
            candidates.append((score, "archive", str(item["archive_url"])))

    unique: dict[str, tuple[int, str, str]] = {}
    for candidate in sorted(candidates, reverse=True):
        unique.setdefault(candidate[2], candidate)

    downloads: list[dict[str, object]] = []
    folder = output / "recovered"
    folder.mkdir(parents=True, exist_ok=True)
    for index, (score, source, url) in enumerate(list(unique.values())[:MAX_ARCHIVE_DOWNLOADS], start=1):
        name = safe_name(Path(urlparse(url).path).name or f"candidate_{index}")
        destination = folder / f"{index:03d}_{source}_{score}_{name}"
        try:
            record = download_candidate(session, url, destination)
            record.update({"source": source, "initial_score": score})
            downloads.append(record)
        except Exception as exc:
            downloads.append({"url": url, "source": source, "initial_score": score, "error": repr(exc)})
        time.sleep(0.3)
    (output / "downloads.json").write_text(json.dumps(downloads, indent=2), encoding="utf-8")
    return downloads


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "rma_south_plants_boa"
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "target_records": [
            "2000 Explanation of Significant Differences for South Plants Balance of Areas and Central Processing Area Soil Remediation Project",
            "2001 South Plants Balance of Areas and Central Processing Area Soil Remediation Project - Phase 2, 100 Percent Design Package, Revision 0",
            "South Plants Balance of Areas remedial action completion, construction certification, or as-built records",
        ],
        "approved_scope": {
            "full_scale_vegetated_cover_only": True,
            "required_clean_width_m": "30-40 after exclusions",
            "coordinate_tied_measured_depths_required": True,
            "matching_near_surface_construction_required": True,
            "stable_sentinel1_period_required": True,
            "plan_changed": False,
        },
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    _, current_links = crawl_current_site(session, output)
    archive_records = query_wayback(session, output)
    downloads = recover_documents(session, output, current_links, archive_records)

    successful_pdfs = [item for item in downloads if item.get("is_pdf")]
    high_score = [
        item for item in successful_pdfs
        if int((item.get("text_extraction") or {}).get("score", 0)) >= 50
    ]
    report.update(
        {
            "current_document_link_count": len(current_links),
            "wayback_record_count": len(archive_records),
            "download_attempt_count": len(downloads),
            "recovered_pdf_count": len(successful_pdfs),
            "high_relevance_pdf_count": len(high_score),
            "high_relevance_documents": high_score,
            "status": "RECOVERED_CANDIDATES" if successful_pdfs else "NO_PDF_RECOVERED",
            "decision": "MANUAL_REVIEW_REQUIRED_NO_CALIBRATION_DECISION",
        }
    )
    (output / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if successful_pdfs else 1


if __name__ == "__main__":
    raise SystemExit(main())
