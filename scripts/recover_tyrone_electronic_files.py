"""Recover and inspect the official Tyrone Attachment I electronic-file record.

Temporary public-record recovery helper. It downloads only official EMNRD files,
extracts PDF text/annotations/attachments, follows same-domain electronic-file
links, and writes a machine-readable inventory. It does not call Earth Engine,
create depth rows, train a model, or enable app depth output.
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
from pypdf import PdfReader

PAGE_URL = (
    "https://www.emnrd.nm.gov/mmd/mining-act-reclamation-program/"
    "pending-and-approved-mine-applications/mining-applications-regular-existing/"
    "gr010retyrone-mine/"
)
ATTACHMENT_I_URL = (
    "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
    "GR010RE_20081223_FAReduction-AttachmentI.pdf"
)
OFFICIAL_HOSTS = {"www.emnrd.nm.gov", "emnrd.nm.gov"}
ELECTRONIC_EXTENSIONS = {
    ".dwg",
    ".dxf",
    ".zip",
    ".7z",
    ".rar",
    ".kml",
    ".kmz",
    ".shp",
    ".shx",
    ".dbf",
    ".prj",
    ".csv",
    ".txt",
    ".xls",
    ".xlsx",
    ".xml",
    ".json",
    ".geojson",
    ".pdf",
}
MAX_DOWNLOAD_BYTES = 750 * 1024 * 1024
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,application/zip,*/*",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return name[:200] or "file"


def run_command(command: list[str], output_path: Path | None = None) -> dict[str, object]:
    process = subprocess.run(command, capture_output=True, check=False)
    if output_path is not None:
        output_path.write_bytes(process.stdout)
    return {
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout.decode("utf-8", errors="replace")[-20000:],
        "stderr": process.stderr.decode("utf-8", errors="replace")[-20000:],
    }


def request(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, headers=HEADERS, timeout=300, allow_redirects=True)
    response.raise_for_status()
    return response


def same_official_host(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in OFFICIAL_HOSTS


def collect_pdf_annotations(pdf_path: Path) -> dict[str, object]:
    reader = PdfReader(str(pdf_path))
    uris: list[str] = []
    annotation_rows: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        annotations = page.get("/Annots") or []
        for annotation_ref in annotations:
            try:
                annotation = annotation_ref.get_object()
                action = annotation.get("/A")
                uri = None
                if action is not None:
                    action = action.get_object()
                    uri = action.get("/URI")
                row = {
                    "page": page_number,
                    "subtype": str(annotation.get("/Subtype", "")),
                    "rect": [float(value) for value in (annotation.get("/Rect") or [])],
                    "uri": str(uri) if uri else None,
                    "contents": str(annotation.get("/Contents", "")) or None,
                }
                annotation_rows.append(row)
                if uri:
                    uris.append(urljoin(ATTACHMENT_I_URL, str(uri)))
            except Exception as exc:  # pragma: no cover - defensive against malformed public PDFs
                annotation_rows.append({"page": page_number, "error": repr(exc)})

    embedded: list[str] = []
    try:
        attachments = reader.attachments
    except Exception:
        attachments = {}
    if isinstance(attachments, dict):
        for name, bodies in attachments.items():
            embedded.append(str(name))
            if not isinstance(bodies, list):
                bodies = [bodies]
            for index, body in enumerate(bodies, start=1):
                if isinstance(body, bytes):
                    target = pdf_path.parent / "embedded" / safe_name(f"{index}_{name}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(body)

    return {
        "page_count": len(reader.pages),
        "metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
        "annotations": annotation_rows,
        "uris": sorted(set(uris)),
        "embedded_attachment_names": embedded,
    }


def filename_candidates(text: str) -> list[str]:
    pattern = re.compile(
        r"(?i)(?:[A-Za-z]:\\[^\r\n<>\"]+|[A-Za-z0-9_./ -]+)"
        r"\.(?:dwg|dxf|zip|7z|rar|kml|kmz|shp|shx|dbf|prj|csv|txt|xls|xlsx|xml|json|geojson|pdf)"
    )
    candidates = []
    for match in pattern.findall(text):
        value = " ".join(match.strip().split())
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def main() -> int:
    root = Path("artifacts/tyrone_electronic_files_recovery")
    downloads = root / "downloads"
    root.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "status": "recovery_started",
        "page_url": PAGE_URL,
        "attachment_i_url": ATTACHMENT_I_URL,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "downloads": [],
    }

    session = requests.Session()

    page_response = request(session, PAGE_URL)
    (root / "mine_page.html").write_bytes(page_response.content)
    soup = BeautifulSoup(page_response.text, "html.parser")
    page_links: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        url = urljoin(page_response.url, anchor["href"])
        page_links.append({"label": label, "url": url})
    (root / "page_links.json").write_text(json.dumps(page_links, indent=2), encoding="utf-8")

    attachment_response = request(session, ATTACHMENT_I_URL)
    attachment_body = attachment_response.content
    if not attachment_body.startswith(b"%PDF-"):
        raise RuntimeError(
            f"Attachment I is not a PDF: {attachment_response.headers.get('content-type')}"
        )
    attachment_path = downloads / "GR010RE_20081223_FAReduction-AttachmentI.pdf"
    attachment_path.write_bytes(attachment_body)
    report["attachment_i"] = {
        "final_url": attachment_response.url,
        "content_type": attachment_response.headers.get("content-type"),
        "size_bytes": len(attachment_body),
        "sha256": sha256_bytes(attachment_body),
    }

    command_reports = {
        "pdfinfo": run_command(["pdfinfo", str(attachment_path)]),
        "pdftotext": run_command(
            ["pdftotext", "-layout", str(attachment_path), str(root / "attachment_i.txt")]
        ),
        "pdftohtml_xml": run_command(
            ["pdftohtml", "-xml", "-hidden", str(attachment_path), str(root / "attachment_i.xml")]
        ),
        "pdfdetach_list": run_command(["pdfdetach", "-list", str(attachment_path)]),
        "qpdf_check": run_command(["qpdf", "--check", str(attachment_path)]),
        "strings": run_command(["strings", "-a", str(attachment_path)], root / "attachment_i.strings.txt"),
    }
    report["commands"] = command_reports

    annotation_report = collect_pdf_annotations(attachment_path)
    report["pdf_structure"] = annotation_report

    extracted_text = ""
    for candidate in (root / "attachment_i.txt", root / "attachment_i.strings.txt"):
        if candidate.is_file():
            extracted_text += "\n" + candidate.read_text(encoding="utf-8", errors="replace")
    report["filename_candidates"] = filename_candidates(extracted_text)

    candidate_urls: set[str] = set(annotation_report.get("uris", []))
    for link in page_links:
        url = link["url"]
        suffix = Path(urlparse(url).path).suffix.lower()
        label = link["label"].lower()
        if suffix in ELECTRONIC_EXTENSIONS and (
            "electronic" in label
            or "attachment i" in label
            or suffix not in {".pdf"}
        ):
            candidate_urls.add(url)

    followed: list[dict[str, object]] = []
    for index, url in enumerate(sorted(candidate_urls), start=1):
        row: dict[str, object] = {"url": url}
        try:
            if not same_official_host(url):
                row["skipped"] = "non_official_host"
                followed.append(row)
                continue
            response = request(session, url)
            body = response.content
            row.update(
                {
                    "final_url": response.url,
                    "content_type": response.headers.get("content-type"),
                    "size_bytes": len(body),
                    "sha256": sha256_bytes(body),
                }
            )
            if len(body) > MAX_DOWNLOAD_BYTES:
                row["skipped"] = "size_limit"
                followed.append(row)
                continue
            name = Path(urlparse(response.url).path).name or f"linked_{index}"
            target = downloads / safe_name(f"{index:02d}_{name}")
            target.write_bytes(body)
            row["saved_path"] = str(target)
        except Exception as exc:
            row["error"] = repr(exc)
        followed.append(row)
    report["followed_links"] = followed

    inventory_lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            inventory_lines.append(f"{path.relative_to(root)}\t{path.stat().st_size} bytes")
    (root / "INVENTORY.txt").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")

    report["status"] = "recovery_complete"
    (root / "recovery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "attachment_size_bytes": len(attachment_body),
                "annotation_uri_count": len(annotation_report.get("uris", [])),
                "embedded_attachment_count": len(
                    annotation_report.get("embedded_attachment_names", [])
                ),
                "followed_link_count": len(followed),
                "filename_candidate_count": len(report["filename_candidates"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
