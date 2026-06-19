"""Locate private D1C REPORT_640 reference roots outside Git.

Default behavior is dry-run only and writes nothing.

The script scans a private root for the three required REPORT_640 reference TIF
filenames and groups matches by their nearest common candidate root. It does not
read raster pixels, copy files, generate rasters, call Earth Engine, change
API/frontend/runtime code, or expose private file contents.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path(r"C:\Dev\New_GEE_PRIVATE")
DEFAULT_OUTPUT = PRIVATE_ROOT / "R1_REPORT_640" / "r1_report640_reference_locator.private.json"
REQUIRED_REPORT_640_FILES = (
    "REPORT_640_Pottery_Report.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
)


class R1ReferenceLocatorError(ValueError):
    """Raised when private locator inputs are invalid."""


def main() -> int:
    args = _parse_args()
    search_root = Path(args.search_root)
    output_path = Path(args.output)
    _validate_private_path_not_inside_repo(search_root, "search root")
    _validate_private_path_not_inside_repo(output_path, "output path")

    result = locate_report640_reference_roots(search_root=search_root, max_files=args.max_files)
    if args.write:
        if result["status"] not in {"complete_reference_root_found", "partial_reference_matches_found"}:
            raise SystemExit("R1 reference locator write refused: no REPORT_640 matches found.")
        result = dict(result)
        result.update({"mode": "write", "inventory_written": True})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(output_path, result)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["match_file_count"] > 0 else 1


def locate_report640_reference_roots(*, search_root: Path, max_files: int = 200_000) -> dict[str, Any]:
    if not search_root.exists():
        return _empty_result(search_root=search_root, status="search_root_missing")
    if not search_root.is_dir():
        return _empty_result(search_root=search_root, status="search_root_not_directory")

    files_scanned = 0
    matches_by_name: dict[str, list[Path]] = {name: [] for name in REQUIRED_REPORT_640_FILES}
    required_names = set(REQUIRED_REPORT_640_FILES)

    for path in search_root.rglob("*"):
        if path.is_file():
            files_scanned += 1
            if files_scanned > max_files:
                break
            if path.name in required_names:
                matches_by_name[path.name].append(path)

    candidates = _candidate_roots(matches_by_name)
    complete_candidates = [candidate for candidate in candidates if candidate["missing_required_count"] == 0]
    match_file_count = sum(len(paths) for paths in matches_by_name.values())

    if complete_candidates:
        status = "complete_reference_root_found"
        readiness_decision = "ready_for_r1_reference_root_review"
    elif match_file_count:
        status = "partial_reference_matches_found"
        readiness_decision = "not_ready_missing_required_reference_files"
    elif files_scanned > max_files:
        status = "scan_limit_reached_no_matches"
        readiness_decision = "not_ready_scan_limit_reached"
    else:
        status = "no_reference_matches_found"
        readiness_decision = "not_ready_no_reference_matches"

    return {
        "status": status,
        "mode": "dry_run",
        "readiness_decision": readiness_decision,
        "search_root_present": True,
        "search_root_is_repo_local": _is_inside_repo(search_root),
        "files_scanned": files_scanned,
        "scan_limit": max_files,
        "scan_limit_reached": files_scanned > max_files,
        "required_files": list(REQUIRED_REPORT_640_FILES),
        "match_file_count": match_file_count,
        "matches_by_required_file": {
            name: len(paths) for name, paths in matches_by_name.items()
        },
        "complete_candidate_count": len(complete_candidates),
        "candidate_roots": candidates,
        "inventory_written": False,
        "raster_pixels_read": False,
        "rasters_copied": False,
        "app_outputs_generated": False,
        "api_frontend_changed": False,
        "earth_engine_called": False,
    }


def _candidate_roots(matches_by_name: dict[str, list[Path]]) -> list[dict[str, Any]]:
    grouped: dict[Path, dict[str, list[Path]]] = defaultdict(lambda: {name: [] for name in REQUIRED_REPORT_640_FILES})
    for name, paths in matches_by_name.items():
        for path in paths:
            grouped[path.parent][name].append(path)

    candidates: list[dict[str, Any]] = []
    for root, by_name in sorted(grouped.items(), key=lambda item: str(item[0])):
        present = [name for name in REQUIRED_REPORT_640_FILES if by_name[name]]
        missing = [name for name in REQUIRED_REPORT_640_FILES if not by_name[name]]
        candidates.append(
            {
                "candidate_root": str(root),
                "present_required_files": present,
                "missing_required_files": missing,
                "present_required_count": len(present),
                "missing_required_count": len(missing),
                "is_complete": len(missing) == 0,
            }
        )
    candidates.sort(key=lambda item: (item["missing_required_count"], item["candidate_root"]))
    return candidates


def _empty_result(*, search_root: Path, status: str) -> dict[str, Any]:
    return {
        "status": status,
        "mode": "dry_run",
        "readiness_decision": "not_ready_search_root_unavailable",
        "search_root_present": search_root.exists(),
        "search_root_is_repo_local": _is_inside_repo(search_root),
        "files_scanned": 0,
        "scan_limit": 0,
        "scan_limit_reached": False,
        "required_files": list(REQUIRED_REPORT_640_FILES),
        "match_file_count": 0,
        "matches_by_required_file": {name: 0 for name in REQUIRED_REPORT_640_FILES},
        "complete_candidate_count": 0,
        "candidate_roots": [],
        "inventory_written": False,
        "raster_pixels_read": False,
        "rasters_copied": False,
        "app_outputs_generated": False,
        "api_frontend_changed": False,
        "earth_engine_called": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Locate private D1C REPORT_640 reference roots outside Git.")
    parser.add_argument("--search-root", default=str(PRIVATE_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-files", type=int, default=200_000)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return False
    return True


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    if _is_inside_repo(path):
        raise R1ReferenceLocatorError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
