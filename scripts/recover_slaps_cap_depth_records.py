"""Recover official SLAPS completion and excavation-depth records.

Temporary public-record recovery for the locked numerical-depth evidence search.
The helper downloads only official U.S. Army Corps of Engineers FUSRAP records,
extracts searchable text, and records passages relevant to completed excavation
surfaces, backfill depths, final grading, common topsoil/vegetation, coordinate
control, survey accuracy, infrastructure exclusions, and post-remediation
stability.

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

READING_ROOM = "https://www.mvs.usace.army.mil/Missions/FUSRAP/Reading-Room/"
SITE_PAGE = "https://www.mvs.usace.army.mil/Missions/FUSRAP/SLAPS/"
BASE = "https://www.mvs.usace.army.mil/Portals/54/docs/fusrap/Admin_Records/NORCO/"

EXPLICIT_DOCUMENTS = {
    "Phase 1 work description": BASE + "NCountySites_02.04_0030_a.PDF",
    "Site grading and drainage plan": BASE + "NCountySites_02.04_0041_a.PDF",
    "Phases 4 and 5 work description": BASE + "NCountySites_02.04_0042_a.PDF",
    "Phase 6 work description": BASE + "NCountySites_02.04_0050_a.PDF",
    "Final radiological final status survey plan": BASE + "NCountySites_02.04_0075_a.PDF",
    "SLAPS implementation report": BASE + "NCountySites_03.10_0009_a.PDF",
    "Phases 4 5 6 pre-design investigation": BASE + "NCountySites_02.13_0004_a.PDF",
}

ANCHOR_TERMS = (
    "st. louis airport site",
    "slaps",
    "post-remedial action",
    "post remedial action",
    "final status survey",
    "site grading",
    "phase 1",
    "phase 2",
    "phase 3",
    "phase 4",
    "phase 5",
    "phase 6",
    "work description",
    "implementation report",
)

KEYWORDS = (
    "post-remedial action report",
    "post remedial action report",
    "final status survey evaluation",
    "excavation depth",
    "depth of excavation",
    "as-built excavation",
    "as built excavation",
    "as-built survey",
    "as built survey",
    "final grade",
    "final grading",
    "backfill thickness",
    "backfill depth",
    "clean backfill",
    "survey unit",
    "survey coordinates",
    "northing",
    "easting",
    "vertical accuracy",
    "horizontal accuracy",
    "survey tolerance",
    "precision",
    "uncertainty",
    "topsoil",
    "vegetative soil",
    "vegetation",
    "hydroseed",
    "seeded",
    "rail spur",
    "sedimentation basin",
    "monitoring well",
    "restoration",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 950 * 1024 * 1024
MAX_DOCUMENTS = 55


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:180] or "document"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(session: requests.Session, url: str) -> requests.Response:
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=(45, 420),
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc!r}")
            time.sleep(attempt * 2)
    raise RuntimeError("; ".join(errors))


def extract_pdf_text(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    proc = subprocess.run(
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
                selected.extend(lines[max(0, index - 6):min(len(lines), index + 10)])
        matches.append(
            {
                "page": page_number,
                "terms": terms,
                "snippet": "\n".join(selected)[:32000],
            }
        )
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr[-4000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def official_pdf(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return (
        host.endswith("usace.army.mil")
        and (url.lower().endswith(".pdf") or "/portals/54/docs/fusrap/" in url.lower())
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "slaps_cap_depth_records"
    documents_dir = output / "documents"
    pages_dir = output / "pages"
    documents_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
        "source_pages": [READING_ROOM, SITE_PAGE],
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

    for label, page_url in (("reading_room", READING_ROOM), ("site_page", SITE_PAGE)):
        try:
            response = request(session, page_url)
            (pages_dir / f"{label}.html").write_bytes(response.content)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                title = clean(tag.get_text(" "))
                url = urljoin(response.url, tag["href"])
                lower = f"{title} {url}".lower()
                if official_pdf(url) and any(term in lower for term in ANCHOR_TERMS):
                    candidates.setdefault(
                        url,
                        {"title": title or url, "url": url, "source": page_url},
                    )
        except Exception as exc:
            report.setdefault("page_errors", []).append(
                {"page": page_url, "error": repr(exc)}
            )

    # The public index stops before the cited May 2009 final report. Probe only
    # nearby official NORCO administrative-record identifiers; non-existent URLs
    # are recorded as misses and never leave the USACE domain.
    for number in range(5, 21):
        url = BASE + f"NCountySites_02.13_{number:04d}_a.PDF"
        candidates.setdefault(
            url,
            {"title": f"Removal response report probe {number:04d}", "url": url, "source": "official_id_probe"},
        )
    for number in range(495, 526):
        url = BASE + f"NCountySites_01.06_{number:04d}_a.PDF"
        candidates.setdefault(
            url,
            {"title": f"Site management report probe {number:04d}", "url": url, "source": "official_id_probe"},
        )

    for index, item in enumerate(list(candidates.values())[:MAX_DOCUMENTS], start=1):
        record: dict[str, object] = dict(item)
        try:
            response = request(session, item["url"])
            body = response.content
            content_type = response.headers.get("content-type", "").lower()
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in content_type
            if not is_pdf:
                record.update(
                    {
                        "status": response.status_code,
                        "content_type": content_type,
                        "size_bytes": len(body),
                        "skipped": "not_pdf",
                    }
                )
                report["documents"].append(record)
                continue
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
            parsed = urlparse(response.url)
            raw_name = Path(parsed.path).name or safe_name(item["title"])
            filename = safe_name(raw_name)
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            path = documents_dir / f"{index:02d}_{filename}"
            path.write_bytes(body)
            record.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": content_type,
                    "size_bytes": len(body),
                    "is_pdf": True,
                    "sha256": sha256(body),
                    "saved_path": str(path),
                    "text_extraction": extract_pdf_text(path),
                }
            )
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    match_count = sum(
        len(item.get("text_extraction", {}).get("matches", []))
        for item in report["documents"]
        if isinstance(item.get("text_extraction"), dict)
    )
    report["candidate_count"] = len(candidates)
    report["pdf_count"] = pdf_count
    report["match_page_count"] = match_count
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
                "match_page_count": match_count,
            },
            indent=2,
        )
    )
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
