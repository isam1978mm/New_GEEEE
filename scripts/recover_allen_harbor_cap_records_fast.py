"""Fast official-record recovery for Allen Harbor Landfill.

This narrow helper reads only the EPA site profile and three official document
collections, downloads relevant EPA SEMS PDFs, and extracts cap/as-built text.
No Earth Engine, calibration, training, or app-depth changes are performed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

PAGES = {
    "EPA profile": "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0101430",
    "EPA key documents": "https://cumulis.epa.gov/supercpad/cursites/cscdocument.cfm?colid=70121&doc=Y&id=0101430",
    "EPA public documents": "https://cumulis.epa.gov/supercpad/cursites/cscdocument.cfm?colid=31799&doc=Y&id=0101430",
    "EPA five-year reviews": "https://cumulis.epa.gov/supercpad/cursites/cscdocument.cfm?colid=32764&doc=Y&id=0101430",
}
EXPLICIT = {
    "1997 Site 09 Record of Decision": "https://semspub.epa.gov/work/HQ/186166.pdf",
    "First five-year review": "https://semspub.epa.gov/work/01/42867.pdf",
    "Five-year review record": "https://semspub.epa.gov/work/HQ/179617.pdf",
}
ANCHOR_TERMS = (
    "allen harbor", "site 09", "site 9", "remedial action", "completion",
    "construction", "as-built", "as built", "final design", "landfill",
    "five-year", "five year", "monitoring", "cap", "protectiveness",
)
KEYWORDS = (
    "allen harbor landfill", "site 09", "site 9", "multimedia cap", "soil cap",
    "3-foot", "three-foot", "2-foot", "two-foot", "cover thickness",
    "cap thickness", "as-built", "as built", "survey", "surveyor", "accuracy",
    "precision", "tolerance", "certification", "common borrow", "vegetative",
    "vegetation", "settlement", "subsidence", "repair", "erosion", "inspection",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "text/html,application/pdf,*/*",
}
MAX_BYTES = 600 * 1024 * 1024


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def safe_name(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:160] or "document")


def get(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=(45, 180), allow_redirects=True)
    response.raise_for_status()
    return response


def extract(pdf_path: Path) -> dict[str, object]:
    text_path = pdf_path.with_suffix(".txt")
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],
        capture_output=True, text=True, check=False,
    )
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    pages = text.split("\f")
    matches: list[dict[str, object]] = []
    for page_no, page in enumerate(pages, start=1):
        low = page.lower()
        terms = [term for term in KEYWORDS if term in low]
        if not terms:
            continue
        lines = page.splitlines()
        selected: list[str] = []
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in KEYWORDS):
                selected.extend(lines[max(0, i - 4):min(len(lines), i + 8)])
        matches.append({"page": page_no, "terms": terms, "snippet": "\n".join(selected)[:24000]})
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr[-3000:],
        "text_path": str(text_path),
        "text_size_bytes": len(text.encode("utf-8")),
        "page_count_from_text": len(pages),
        "matches": matches,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "allen_harbor_cap_records"
    docs = out / "documents"
    pages = out / "pages"
    docs.mkdir(parents=True, exist_ok=True)
    pages.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "status": "RECOVERY_STARTED",
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
        for title, url in EXPLICIT.items()
    }
    for label, page_url in PAGES.items():
        try:
            response = get(session, page_url)
            (pages / f"{safe_name(label)}.html").write_bytes(response.content)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                anchor = clean(tag.get_text(" "))
                url = urljoin(response.url, tag["href"])
                low = f"{anchor} {url}".lower()
                if "semspub.epa.gov" not in url.lower():
                    continue
                if not (url.lower().endswith(".pdf") or "/work/" in url.lower() or "/src/document/" in url.lower()):
                    continue
                if any(term in low for term in ANCHOR_TERMS):
                    candidates.setdefault(url, {"title": anchor or url, "url": url, "source": page_url})
        except Exception as exc:
            report.setdefault("page_errors", []).append({"label": label, "url": page_url, "error": repr(exc)})

    for index, item in enumerate(candidates.values(), start=1):
        record: dict[str, object] = dict(item)
        try:
            response = get(session, item["url"])
            body = response.content
            ctype = response.headers.get("content-type", "").lower()
            if len(body) > MAX_BYTES:
                record.update({"status": response.status_code, "size_bytes": len(body), "skipped": "size_limit"})
                report["documents"].append(record)
                continue
            is_pdf = body.startswith(b"%PDF-") or "application/pdf" in ctype
            suffix = ".pdf" if is_pdf else ".html"
            raw = Path(urlparse(response.url).path).name or safe_name(item["title"])
            name = safe_name(raw)
            if not name.lower().endswith(suffix):
                name += suffix
            path = docs / f"{index:02d}_{name}"
            path.write_bytes(body)
            record.update({
                "status": response.status_code,
                "final_url": response.url,
                "content_type": ctype,
                "size_bytes": len(body),
                "is_pdf": is_pdf,
                "sha256": hashlib.sha256(body).hexdigest(),
                "saved_path": str(path),
            })
            if is_pdf:
                record["text_extraction"] = extract(path)
            else:
                record["html_preview"] = clean(BeautifulSoup(response.text, "html.parser").get_text(" "))[:12000]
        except Exception as exc:
            record["error"] = repr(exc)
        report["documents"].append(record)

    pdf_count = sum(1 for item in report["documents"] if item.get("is_pdf"))
    report["candidate_count"] = len(candidates)
    report["pdf_count"] = pdf_count
    report["status"] = "RECOVERY_COMPLETE" if pdf_count else "NO_PDF_RECOVERED"
    (out / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_count": len(candidates), "pdf_count": pdf_count}, indent=2))
    return 0 if pdf_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
