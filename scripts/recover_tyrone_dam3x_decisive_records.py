#!/usr/bin/env python3
"""Recover only the decisive public Tyrone Dam 3X records.

This temporary research script is intentionally narrow. It downloads the official
2012 financial-assurance release package and the 2009 partial-release package,
then checks for:

* Test Plot 5 / Test Plot 6 geometry;
* northing/easting, GPS, CAES, GIS, CAD, or surveyed vertices;
* the June 2008 3X Construction Quality Assurance Report;
* plot-specific repairs, disturbance, or stability evidence.

It does not change production code and must not be merged.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

OUT = Path("artifacts/tyrone_dam3x_decisive_records")
DOCS = OUT / "documents"
TEXT = OUT / "text"
RENDERS = OUT / "renders"

SOURCES = {
    "2012_financial_assurance_release_application": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "2012-12-17_Mod12-3Application_GR010RE.pdf"
    ),
    "2009_partial_financial_assurance_release": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20091223_Tyrone_Mod09-03_Finanial_Assurance_Reduction.pdf"
    ),
    "2008_electronic_files_placeholder": (
        "https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/"
        "GR010RE_20081223_FAReduction-AttachmentI.pdf"
    ),
}

KEYWORDS = [
    "test plot 5",
    "test plot 6",
    "plot 5",
    "plot 6",
    "3x tailing",
    "3x reclamation",
    "construction quality assurance",
    "cqa report",
    "m3, 2008",
    "northing",
    "easting",
    "coordinate",
    "surveyed vertices",
    "gps",
    "caes",
    "gis",
    "shapefile",
    "cad",
    "as-built",
    "subsidence",
    "repair",
    "regrade",
    "disturbance",
    "financial assurance release",
]


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def download_pdf(name: str, url: str) -> tuple[Path | None, dict[str, Any]]:
    target = DOCS / f"{name}.pdf"
    report: dict[str, Any] = {"url": url, "path": str(target)}
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/126 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*;q=0.8",
        }
    )
    try:
        response = session.get(url, timeout=180, allow_redirects=True)
        body = response.content
        report.update(
            {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content_length": len(body),
                "final_url": response.url,
                "pdf_header": body[:5] == b"%PDF-",
            }
        )
        # Some government servers return unusual status handling. The PDF
        # signature is the decisive transport check.
        if body[:5] != b"%PDF-":
            report["error"] = "response did not begin with %PDF-"
            (OUT / f"{name}_response.bin").write_bytes(body[:200000])
            return None, report
        target.write_bytes(body)
        return target, report
    except Exception as exc:  # noqa: BLE001 - preserve transport diagnosis
        report["error"] = f"{type(exc).__name__}: {exc}"
        return None, report


def inspect_pdf(path: Path) -> dict[str, Any]:
    info = run(["pdfinfo", str(path)]).stdout
    attachments = run(["pdfdetach", "-list", str(path)]).stdout
    text_path = TEXT / f"{path.stem}.txt"
    extract = run(["pdftotext", "-layout", str(path), str(text_path)])

    result: dict[str, Any] = {
        "pdfinfo": info,
        "attachments": attachments,
        "text_extract_output": extract.stdout,
        "text_path": str(text_path),
        "keyword_pages": [],
        "geospatial_markers": [],
    }

    if not text_path.exists():
        return result

    pages = text_path.read_text(errors="replace").split("\f")
    for page_number, page in enumerate(pages, start=1):
        lower = page.lower()
        hits = sorted({term for term in KEYWORDS if term in lower})
        if not hits:
            continue
        snippet = " ".join(page.split())[:1000]
        result["keyword_pages"].append(
            {"page": page_number, "hits": hits, "snippet": snippet}
        )

    # Check raw PDF structure for embedded geospatial dictionaries. These
    # markers alone do not prove a coordinate-tied drawing, but their absence
    # is useful and their presence identifies pages for manual review.
    raw = path.read_bytes()
    for marker in [b"/LGIDict", b"/GPTS", b"/LPTS", b"/GCS", b"/Measure", b"GeoPDF"]:
        if marker in raw:
            result["geospatial_markers"].append(marker.decode("ascii"))

    decisive_pages = []
    for item in result["keyword_pages"]:
        hits = set(item["hits"])
        if hits.intersection(
            {
                "test plot 5",
                "test plot 6",
                "construction quality assurance",
                "cqa report",
                "northing",
                "easting",
                "coordinate",
                "gps",
                "caes",
                "gis",
                "shapefile",
                "cad",
                "subsidence",
                "repair",
            }
        ):
            decisive_pages.append(int(item["page"]))

    # Keep rendering bounded. Include at most 18 unique decisive pages per PDF.
    for page_number in sorted(set(decisive_pages))[:18]:
        prefix = RENDERS / f"{path.stem}_p{page_number:04d}"
        render = run(
            [
                "pdftoppm",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-r",
                "130",
                "-png",
                "-singlefile",
                str(path),
                str(prefix),
            ]
        )
        if render.stdout:
            (RENDERS / f"{path.stem}_p{page_number:04d}.log").write_text(
                render.stdout
            )

    return result


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    DOCS.mkdir(parents=True)
    TEXT.mkdir(parents=True)
    RENDERS.mkdir(parents=True)

    report: dict[str, Any] = {
        "scope": "Option 3 bounded Tyrone Dam 3X decisive-record recovery",
        "sources": {},
        "documents": {},
        "decision_questions": {
            "coordinate_tied_test_plot_5_and_6_geometry_found": False,
            "plot_specific_unchanged_sentinel1_period_found": False,
            "june_2008_cqa_report_found": False,
        },
    }

    for name, url in SOURCES.items():
        path, transport = download_pdf(name, url)
        report["sources"][name] = transport
        if path is None:
            continue
        inspected = inspect_pdf(path)
        report["documents"][name] = inspected

        all_text = ""
        text_path = Path(inspected["text_path"])
        if text_path.exists():
            all_text = text_path.read_text(errors="replace").lower()

        if "construction quality assurance report" in all_text and "3x" in all_text:
            report["decision_questions"]["june_2008_cqa_report_found"] = True

        geometry_terms = ["northing", "easting", "shapefile", "surveyed vertices"]
        plot_terms = ["test plot 5", "test plot 6", "plot 5", "plot 6"]
        if any(term in all_text for term in geometry_terms) and all(
            any(term in all_text for term in group)
            for group in (["test plot 5", "plot 5"], ["test plot 6", "plot 6"])
        ):
            report["decision_questions"][
                "coordinate_tied_test_plot_5_and_6_geometry_found"
            ] = True

        stability_terms = ["unchanged", "no disturbance", "no repairs", "stable"]
        if any(term in all_text for term in stability_terms) and any(
            term in all_text for term in plot_terms
        ):
            report["decision_questions"][
                "plot_specific_unchanged_sentinel1_period_found"
            ] = True

    (OUT / "recovery_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Tyrone Dam 3X decisive-record recovery",
        "",
        "This is transport and document triage only. Final scientific decisions require manual review of the rendered decisive pages.",
        "",
    ]
    for key, value in report["decision_questions"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    for name, source in report["sources"].items():
        lines.append(f"## {name}")
        lines.append(f"- status: {source.get('status_code')}")
        lines.append(f"- bytes: {source.get('content_length')}")
        lines.append(f"- PDF signature: {source.get('pdf_header')}")
        if source.get("error"):
            lines.append(f"- error: {source['error']}")
        lines.append("")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(report["decision_questions"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
