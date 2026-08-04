from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_FILES = (
    "GR010RE_2007_Plate02_Tailing_Area.pdf",
    "GR010RE_Tyrone_2020_CCP_Text_Figures_Plates_Tables.pdf",
    "GR010RE_3X_Tailing_AsBuilt_Report.pdf",
)

KEYWORDS = (
    "3x",
    "no. 3x",
    "reclaimed 3x",
    "mangas valley",
    "tailing area",
    "tailings area",
    "plate 2",
    "test plot 5",
    "test plot 6",
    "northing",
    "easting",
    "coordinate",
    "state plane",
    "nad27",
    "nad83",
    "utm",
    "survey grid",
    "grid",
)

STRONG_KEYWORDS = {
    "3x": 5,
    "no. 3x": 7,
    "reclaimed 3x": 10,
    "mangas valley": 8,
    "test plot 5": 10,
    "test plot 6": 10,
    "northing": 8,
    "easting": 8,
    "coordinate": 6,
    "state plane": 10,
    "nad27": 10,
    "nad83": 10,
    "utm": 8,
    "survey grid": 8,
}

# Known decisive drawing pages from the 2006 as-built report, using PDF-page
# numbering from the forensic read. These are included even if text extraction
# from the drawing itself is sparse.
KNOWN_AS_BUILT_PAGES_1_BASED = (39, 40, 45)


@dataclass(frozen=True)
class PageCandidate:
    pdf_name: str
    page_number: int
    score: int
    hits: tuple[str, ...]
    text_preview: str
    forced_reason: str | None = None


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def score_page_text(text: str) -> tuple[int, tuple[str, ...]]:
    normalized = normalize_text(text)
    hits: list[str] = []
    score = 0
    for keyword in KEYWORDS:
        if keyword in normalized:
            hits.append(keyword)
            score += STRONG_KEYWORDS.get(keyword, 2)
    return score, tuple(hits)


def select_candidates(
    candidates: Iterable[PageCandidate],
    *,
    maximum_scored_pages_per_pdf: int,
) -> list[PageCandidate]:
    grouped: dict[str, list[PageCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.pdf_name, []).append(candidate)

    selected: list[PageCandidate] = []
    for pdf_name in sorted(grouped):
        group = grouped[pdf_name]
        forced = [item for item in group if item.forced_reason]
        scored = [item for item in group if not item.forced_reason and item.score > 0]
        scored.sort(key=lambda item: (-item.score, item.page_number))

        seen_pages: set[int] = set()
        for item in forced + scored[:maximum_scored_pages_per_pdf]:
            if item.page_number in seen_pages:
                continue
            seen_pages.add(item.page_number)
            selected.append(item)

    return selected


def _load_dependencies():
    try:
        import fitz  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised by operator environment
        raise SystemExit(
            "PyMuPDF is required for this extractor. Install it in the project "
            "virtual environment with:\n"
            ".\\.venv\\Scripts\\python.exe -m pip install pymupdf"
        ) from exc

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Pillow is required but is missing from the environment.") from exc

    return fitz, Image, ImageDraw


def _preview(text: str, limit: int = 300) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def collect_candidates(records_dir: Path) -> tuple[list[PageCandidate], dict[str, int]]:
    fitz, _, _ = _load_dependencies()
    candidates: list[PageCandidate] = []
    page_counts: dict[str, int] = {}

    for pdf_name in DEFAULT_FILES:
        pdf_path = records_dir / pdf_name
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Required PDF is missing: {pdf_path}")

        document = fitz.open(pdf_path)
        page_counts[pdf_name] = document.page_count
        try:
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                text = page.get_text("text") or ""
                score, hits = score_page_text(text)
                page_number = page_index + 1
                forced_reason: str | None = None

                if pdf_name == "GR010RE_2007_Plate02_Tailing_Area.pdf":
                    forced_reason = "complete official 2007 tailing-area plate"
                elif (
                    pdf_name == "GR010RE_3X_Tailing_AsBuilt_Report.pdf"
                    and page_number in KNOWN_AS_BUILT_PAGES_1_BASED
                ):
                    forced_reason = "known TP5/TP6 drawing page"

                if score > 0 or forced_reason:
                    candidates.append(
                        PageCandidate(
                            pdf_name=pdf_name,
                            page_number=page_number,
                            score=score,
                            hits=hits,
                            text_preview=_preview(text),
                            forced_reason=forced_reason,
                        )
                    )
        finally:
            document.close()

    return candidates, page_counts


def render_selected_pages(
    records_dir: Path,
    output_dir: Path,
    selected: list[PageCandidate],
    *,
    dpi: int,
) -> list[dict[str, object]]:
    fitz, _, _ = _load_dependencies()
    output_dir.mkdir(parents=True, exist_ok=True)
    document_cache: dict[str, object] = {}
    manifest_rows: list[dict[str, object]] = []

    try:
        for candidate in selected:
            document = document_cache.get(candidate.pdf_name)
            if document is None:
                document = fitz.open(records_dir / candidate.pdf_name)
                document_cache[candidate.pdf_name] = document

            page = document.load_page(candidate.page_number - 1)
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)
            stem = Path(candidate.pdf_name).stem
            image_name = f"{stem}__page_{candidate.page_number:04d}.png"
            image_path = output_dir / image_name
            pixmap.save(image_path)

            manifest_rows.append(
                {
                    "pdf_name": candidate.pdf_name,
                    "page_number": candidate.page_number,
                    "score": candidate.score,
                    "keyword_hits": list(candidate.hits),
                    "forced_reason": candidate.forced_reason,
                    "text_preview": candidate.text_preview,
                    "rendered_image": str(image_path),
                }
            )
    finally:
        for document in document_cache.values():
            document.close()

    return manifest_rows


def build_contact_sheet(
    output_dir: Path,
    rows: list[dict[str, object]],
    *,
    thumbnail_width: int = 420,
) -> Path:
    _, Image, ImageDraw = _load_dependencies()
    if not rows:
        raise ValueError("Cannot build a contact sheet without rendered pages.")

    margin = 24
    caption_height = 72
    prepared: list[tuple[object, str]] = []
    maximum_height = 0

    for row in rows:
        image_path = Path(str(row["rendered_image"]))
        image = Image.open(image_path).convert("RGB")
        scale = thumbnail_width / image.width
        thumbnail = image.resize((thumbnail_width, max(1, int(image.height * scale))))
        caption = f"{row['pdf_name']} | PDF page {row['page_number']} | score {row['score']}"
        prepared.append((thumbnail, caption))
        maximum_height = max(maximum_height, thumbnail.height)

    columns = 2
    rows_count = (len(prepared) + columns - 1) // columns
    cell_width = thumbnail_width + margin * 2
    cell_height = maximum_height + caption_height + margin * 2
    sheet = Image.new("RGB", (columns * cell_width, rows_count * cell_height), "white")
    draw = ImageDraw.Draw(sheet)

    for index, (thumbnail, caption) in enumerate(prepared):
        row_index = index // columns
        column_index = index % columns
        x = column_index * cell_width + margin
        y = row_index * cell_height + margin
        sheet.paste(thumbnail, (x, y))
        draw.text((x, y + maximum_height + 12), caption, fill="black")

    contact_sheet_path = output_dir / "route_b_contact_sheet.png"
    sheet.save(contact_sheet_path)
    return contact_sheet_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract and render Tyrone Route B map pages from the official PDFs. "
            "This script does not georeference or create calibration polygons."
        )
    )
    parser.add_argument("--records-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--maximum-scored-pages-per-pdf", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    records_dir = args.records_dir.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else records_dir / "route_b_map_pages"
    )

    candidates, page_counts = collect_candidates(records_dir)
    selected = select_candidates(
        candidates,
        maximum_scored_pages_per_pdf=args.maximum_scored_pages_per_pdf,
    )
    rows = render_selected_pages(
        records_dir,
        output_dir,
        selected,
        dpi=args.dpi,
    )
    contact_sheet = build_contact_sheet(output_dir, rows)

    manifest = {
        "schema": "tyrone_3x_route_b_map_page_manifest_v1",
        "records_dir": str(records_dir),
        "output_dir": str(output_dir),
        "page_counts": page_counts,
        "rendered_page_count": len(rows),
        "contact_sheet": str(contact_sheet),
        "pages": rows,
        "does_not_prove": [
            "coordinate-tied TP5 or TP6 geometry",
            "acceptable georeference accuracy",
            "stable Sentinel-1 calibration interval",
            "numerical depth readiness",
        ],
        "next_gate": (
            "Inspect the rendered pages for at least six persistent fit-control "
            "features and two independent check features visible on both the "
            "2006 TP5/TP6 drawing and a coordinate-controlled later map."
        ),
    }
    manifest_path = output_dir / "route_b_page_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "route_b_candidate_pages_rendered",
        "page_counts": page_counts,
        "rendered_page_count": len(rows),
        "manifest": str(manifest_path),
        "contact_sheet": str(contact_sheet),
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
