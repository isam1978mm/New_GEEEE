"""Inspect the 2008 Tyrone FA-reduction application for an electronic-file manifest.

Temporary public-record recovery helper. It downloads the official application,
extracts its text and PDF structure, searches for references to Attachment I or
missing electronic media, and renders only relevant pages (or all pages when no
text layer exists). It does not call Earth Engine or change app depth state.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import requests
from pypdf import PdfReader

APPLICATION_URL = (
    "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
    "GR010RE_20081223_FAReduction-Application.pdf"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}
TERMS = (
    "attachment i",
    "electronic files",
    "electronic file",
    "compact disc",
    "cd-rom",
    "cd rom",
    "cd",
    "autocad",
    "dwg",
    "dxf",
    "gis",
    "shapefile",
    "kml",
    "kmz",
    "coordinate system",
    "state plane",
    "mine grid",
    "survey grid",
    "easting",
    "northing",
)
FILENAME_PATTERN = re.compile(
    r"(?i)(?:[A-Za-z]:\\[^\r\n<>\"]+|[A-Za-z0-9_./ -]+)"
    r"\.(?:dwg|dxf|zip|7z|rar|kml|kmz|shp|shx|dbf|prj|csv|txt|xls|xlsx|xml|json|geojson|pdf)"
)


def run(command: list[str]) -> dict[str, object]:
    process = subprocess.run(command, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout.decode("utf-8", errors="replace")[-20000:],
        "stderr": process.stderr.decode("utf-8", errors="replace")[-20000:],
    }


def targeted_extracts(text: str) -> tuple[list[int], str]:
    pages = text.split("\f")
    matching_pages: list[int] = []
    output: list[str] = []
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        matched = [term for term in TERMS if term in lower]
        if not matched:
            continue
        matching_pages.append(page_number)
        lines = page.splitlines()
        selected: list[str] = []
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in TERMS):
                start = max(0, index - 6)
                end = min(len(lines), index + 10)
                selected.extend(lines[start:end])
        output.extend(
            [
                f"================ PAGE {page_number} ================",
                f"matched_terms: {', '.join(matched)}",
                *selected,
                "",
            ]
        )
    return sorted(set(matching_pages)), "\n".join(output)


def main() -> int:
    root = Path("artifacts/tyrone_electronic_files_recovery")
    downloads = root / "downloads"
    render_dir = root / "application_pages"
    downloads.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        APPLICATION_URL,
        headers=HEADERS,
        timeout=600,
        allow_redirects=True,
    )
    response.raise_for_status()
    body = response.content
    if not body.startswith(b"%PDF-"):
        raise RuntimeError(f"Application is not a PDF: {response.headers.get('content-type')}")

    pdf_path = downloads / "GR010RE_20081223_FAReduction-Application.pdf"
    pdf_path.write_bytes(body)
    text_path = root / "application.txt"
    text_command = run(["pdftotext", "-layout", str(pdf_path), str(text_path)])
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    matching_pages, extracts = targeted_extracts(text)
    (root / "application_targeted_extracts.txt").write_text(extracts, encoding="utf-8")

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    annotation_uris: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for annotation_ref in page.get("/Annots") or []:
            try:
                annotation = annotation_ref.get_object()
                action = annotation.get("/A")
                if action is not None:
                    action = action.get_object()
                    uri = action.get("/URI")
                    if uri:
                        annotation_uris.append({"page": page_number, "uri": str(uri)})
            except Exception as exc:  # pragma: no cover
                annotation_uris.append({"page": page_number, "error": repr(exc)})

    filenames: list[str] = []
    for match in FILENAME_PATTERN.findall(text):
        value = " ".join(match.strip().split())
        if value and value not in filenames:
            filenames.append(value)

    meaningful_text_chars = len(re.sub(r"\s+", "", text))
    pages_to_render = matching_pages
    render_reason = "matching_text_pages"
    if meaningful_text_chars < 200:
        pages_to_render = list(range(1, page_count + 1))
        render_reason = "no_usable_text_layer_all_pages"
    elif not pages_to_render:
        pages_to_render = [1, page_count] if page_count > 1 else [1]
        render_reason = "no_term_match_first_and_last_pages"

    render_reports: list[dict[str, object]] = []
    for page_number in sorted(set(pages_to_render)):
        output_prefix = render_dir / f"page_{page_number:03d}"
        report = run(
            [
                "pdftoppm",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-singlefile",
                "-png",
                "-r",
                "140",
                str(pdf_path),
                str(output_prefix),
            ]
        )
        report["page"] = page_number
        render_reports.append(report)

    report = {
        "status": "application_manifest_inspection_complete",
        "application_url": APPLICATION_URL,
        "final_url": response.url,
        "content_type": response.headers.get("content-type"),
        "size_bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "page_count": page_count,
        "meaningful_text_chars": meaningful_text_chars,
        "matching_pages": matching_pages,
        "filename_candidates": filenames,
        "annotation_uris": annotation_uris,
        "render_reason": render_reason,
        "rendered_pages": sorted(set(pages_to_render)),
        "commands": {
            "pdfinfo": run(["pdfinfo", str(pdf_path)]),
            "pdftotext": text_command,
            "pdfdetach_list": run(["pdfdetach", "-list", str(pdf_path)]),
            "qpdf_check": run(["qpdf", "--check", str(pdf_path)]),
            "renders": render_reports,
        },
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    (root / "application_manifest_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "page_count": page_count,
                "meaningful_text_chars": meaningful_text_chars,
                "matching_pages": matching_pages,
                "filename_candidate_count": len(filenames),
                "annotation_uri_count": len(annotation_uris),
                "rendered_pages": report["rendered_pages"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
