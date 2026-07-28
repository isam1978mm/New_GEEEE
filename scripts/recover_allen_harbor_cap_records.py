"""Recover official Allen Harbor Landfill cap and as-built records.

Temporary public-record recovery for the locked numerical-depth evidence search.
The helper downloads only official EPA and Navy pages/documents, follows relevant
record links, extracts searchable PDF text, and records passages concerning the
multimedia-cap and soil-cap boundaries, final measured thicknesses, as-built
surveys, numerical accuracy, common vegetated surface, repairs, settlement and
long-term stability.

It does not call Earth Engine, create calibration rows, train a model, or enable
numerical depth output.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SEED_URLS = {
    "EPA cleanup profile": (
        "https://cumulis.epa.gov/supercpad/SiteProfiles/"
        "index.cfm?fuseaction=second.cleanup&id=0101430"
    ),
    "EPA document profile": (
        "https://cumulis.epa.gov/supercpad/SiteProfiles/"
        "index.cfm?fuseaction=second.docdata&id=0101430"
    ),
    "EPA record collections profile": (
        "https://cumulis.epa.gov/supercpad/cursites/"
        "cscdocument.cfm?id=0101430"
    ),
    "EPA climate adaptation profile": (
        "https://www.epa.gov/superfund/"
        "climate-adaptation-profile-allen-harbor-landfill"
    ),
    "Navy Davisville page": (
        "https://www.bracpmo.navy.mil/BRAC-Bases/Northeast/"
        "Former-Naval-Construction-Battalion-Davisville/"
    ),
}

EXPLICIT_DOCUMENTS = {
    "1997 Site 09 Record of Decision": "https://semspub.epa.gov/work/HQ/186166.pdf",
    "First five-year review": "https://semspub.epa.gov/work/01/42867.pdf",
    "Five-year review record": "https://semspub.epa.gov/work/HQ/179617.pdf",
}

ANCHOR_TERMS = (
    "allen harbor",
    "site 09",
    "site 9",
    "remedial action",
    "construction completion",
    "completion report",
    "as-built",
    "as built",
    "final design",
    "cap",
    "landfill",
    "five-year review",
    "five year review",
    "long-term monitoring",
    "long term monitoring",
    "protectiveness",
)

KEYWORDS = (
    "allen harbor landfill",
    "site 09",
    "site 9",
    "multimedia cap",
    "soil cap",
    "three-foot",
    "3-foot",
    "two-foot",
    "2-foot",
    "final cover",
    "cover thickness",
    "cap thickness",
    "as-built",
    "as built",
    "survey",
    "surveyor",
    "accuracy",
    "precision",
    "tolerance",
    "certification",
    "common borrow",
    "vegetative",
    "vegetation",
    "settlement",
    "subsidence",
    "repair",
    "erosion",
    "inspection",
    "protective",
)

ALLOWED_HOST_SUFFIXES = (
    "epa.gov",
    "semspub.epa.gov",
    "navy.mil",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024
MAX_DOCUMENTS = 80


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)


def request(session: requests.Session, url: str) -> requests.Response:
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=(60, 600),
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc!r}")
            time.sleep(attempt * 3)
    raise RuntimeError("; ".join(errors))


def extract_pdf_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    process = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        terms = [term for term in KEYWORDS if term in lower]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in KEYWORDS):
                start = max(0, index - 5)
                end = min(len(lines), index + 9)
                selected.extend(lines[start:end])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:28000],
            }
        )
    return {
        "returncode": process.returncode,
        "stderr": process.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def relevant_link(anchor: str, url: str) -> bool:
    lower = f"{anchor} {url}".lower()
    return (
        url.lower().endswith(".pdf")
        or "semspub.epa.gov" in url.lower()
        or any(term in lower for term in ANCHOR_TERMS)
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "allen_harbor_cap_records"
    documents_dir = output / "documents"
    pages_dir = output / "pages"
    documents_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "seed_urls": SEED_URLS,
        "documents": [],
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "plan_changed": False,
    }

    session = requests.Session()
    candidates: dict[str, dict[str, str]] = {
        url: {"title": title, "url": url, "source": "explicit"}
        for title, url in EXPLICIT_DOCUMENTS.items()
    }

    # Crawl the official profile pages and one level of relevant official links.
    page_queue = list(SEED_URLS.items())
    visited_pages: set[str] = set()
    while page_queue and len(visited_pages) < 30:
        source_title, page_url = page_queue.pop(0)
        if page_url in visited_pages or not allowed(page_url):
            continue
        visited_pages.add(page_url)
        try:
            response = request(session, page_url)
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
            if body.startswith(b"%PDF-") or "application/pdf" in content_type:
                candidates.setdefault(
                    response.url,
                    {"title": source_title, "url": response.url, "source": page_url},
                )
                continue
            page_name = safe_name(source_title) + ".html"
            (pages_dir / page_name).write_bytes(body)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                anchor = clean(tag.get_text(" "))
                url = urljoin(response.url, tag["href"])
                if not allowed(url) or not relevant_link(anchor, url):
                    continue
                candidates.setdefault(
                    url,
                    {"title": anchor or url, "url": url, "source": page_url},
                )
                if not url.lower().endswith(".pdf") and url not in visited_pages:
                    page_queue.append((anchor or "linked page", url))
        except Exception as exc:
            report.setdefault("page_errors", []).append(
                {"title": source_title, "url": page_url, "error": repr(exc)}
            )

    for index, item in enumerate(list(candidates.values())[:MAX_DOCUMENTS], start=1):
        record: dict[str, object] = dict(item)
        try:
            response = request(session, item["url"])
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
            if len(body) > MAX_BYTES:
                record.update(
                    {
                        "status": response.status_code,
                        "size_bytes": len(body),
                        "skipped": "size_limit",
                    }
                )
                report["documents"].append(record)
                continue
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            suffix = ".pdf" if is_pdf else ".html"
            parsed = urlparse(response.url)
            raw_name = Path(parsed.path).name or safe_name(item["title"])
            filename = safe_name(raw_name)
            if not filename.lower().endswith(suffix):
                filename += suffix
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)
            record.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": content_type,
                    "size_bytes": len(body),
                    "is_pdf": is_pdf,
                    "sha256": sha256(body),
                    "saved_path": str(path),
                }
            )
            if is_pdf:
                record["text_extraction"] = extract_pdf_text(path)
            else:
                record["html_preview"] = clean(
                    BeautifulSoup(response.text, "html.parser").get_text(" ")
                )[:15000]
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    report["candidate_count"] = len(candidates)
    report["pdf_count"] = pdf_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (output / "recovery_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_count": len(candidates),
                "pdf_count": pdf_count,
            },
            indent=2,
        )
    )
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
