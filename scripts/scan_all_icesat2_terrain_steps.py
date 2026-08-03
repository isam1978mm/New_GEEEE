"""Scan all existing completed run AOIs for persistent ICESat-2 terrain steps.

This is a read-only, scan-first batch wrapper around
``scan_icesat2_terrain_steps.audit``.  It discovers completed run directories,
scans them sequentially, writes private run-local results, and produces one
ranked summary.  A failed remote query for one run does not stop the remaining
runs.

The script does not research records, create depth anchors, invoke the depth
engine, register app artifacts, or modify the frontend.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_icesat2_repeat_points import DEFAULT_END, DEFAULT_START, Icesat2AuditError
from scan_icesat2_terrain_steps import _geojson, audit

RUN_RESULT_FILENAME = "icesat2_step_scan.json"
RUN_GEOJSON_FILENAME = "icesat2_step_candidates.geojson"
DEFAULT_SUMMARY_FILENAME = "icesat2_step_scan_all_runs.json"
COMPLETED_MARKERS = (
    "logRatio_dB.tif",
    "objects_index.csv",
)


@dataclass(frozen=True, slots=True)
class RunSelection:
    run_dir: Path
    completion_markers: tuple[str, ...]


def discover_completed_runs(
    runs_dir: Path,
    *,
    include_grid_only: bool = False,
) -> tuple[list[RunSelection], list[dict[str, object]]]:
    """Discover run directories without reading or changing the app database.

    A normal completed app run has a grid manifest and at least one canonical
    terminal artifact.  ``include_grid_only`` is an explicit escape hatch for
    older run layouts, but it is off by default so partial directories are not
    queried accidentally.
    """

    selected: list[RunSelection] = []
    skipped: list[dict[str, object]] = []
    if not runs_dir.is_dir():
        return selected, [
            {
                "run": None,
                "reason": "runs_directory_missing",
                "path": str(runs_dir),
            }
        ]

    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        grid_path = run_dir / "grid_manifest.json"
        if not grid_path.is_file():
            skipped.append(
                {
                    "run": run_dir.name,
                    "reason": "missing_grid_manifest",
                }
            )
            continue
        markers = tuple(
            marker for marker in COMPLETED_MARKERS if (run_dir / marker).is_file()
        )
        if not markers and not include_grid_only:
            skipped.append(
                {
                    "run": run_dir.name,
                    "reason": "no_completed_run_marker",
                    "required_any_of": list(COMPLETED_MARKERS),
                }
            )
            continue
        selected.append(RunSelection(run_dir=run_dir, completion_markers=markers))
    return selected, skipped


def _read_cached_result(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema") != "icesat2_terrain_step_scan_v1":
        return None
    return payload


def _candidate_rows(
    run_result: dict[str, object],
    *,
    run_name: str,
) -> list[dict[str, object]]:
    clusters = run_result.get("surviving_step_clusters", [])
    if not isinstance(clusters, list):
        return []
    rows: list[dict[str, object]] = []
    for local_rank, item in enumerate(clusters, start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "run": run_name,
                "run_local_rank": local_rank,
                "longitude": item.get("centroid_longitude"),
                "latitude": item.get("centroid_latitude"),
                "event_start": item.get("event_start"),
                "event_end": item.get("event_end"),
                "median_step_m": item.get("median_step_m"),
                "step_nmad_m": item.get("step_nmad_m"),
                "segment_count": item.get("segment_count"),
                "cross_spot_supported": bool(item.get("cross_spot_supported")),
                "rgt": item.get("rgt"),
                "spot": item.get("spot"),
                "pre_cycle": item.get("pre_cycle"),
                "post_cycle": item.get("post_cycle"),
            }
        )
    return rows


def rank_candidates(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Rank survivors without turning the ranking into a depth or cause claim."""

    ranked = list(rows)

    def _number(item: dict[str, object], key: str, default: float) -> float:
        value = item.get(key)
        return float(value) if isinstance(value, (int, float)) else default

    ranked.sort(
        key=lambda item: (
            not bool(item.get("cross_spot_supported")),
            -_number(item, "segment_count", 0.0),
            _number(item, "step_nmad_m", float("inf")),
            -_number(item, "median_step_m", 0.0),
            str(item.get("run", "")),
            int(item.get("run_local_rank", 0) or 0),
        )
    )
    return [dict(item, global_rank=index) for index, item in enumerate(ranked, start=1)]


def _compact_run_result(
    result: dict[str, object],
    *,
    completion_markers: tuple[str, ...],
    result_source: str,
) -> dict[str, object]:
    return {
        "run": result.get("run"),
        "status": result.get("status"),
        "result_source": result_source,
        "completion_markers": list(completion_markers),
        "quality_segment_count": result.get("quality_segment_count"),
        "exact_segment_series_count": result.get("exact_segment_series_count"),
        "classification_counts": result.get("classification_counts", {}),
        "raw_step_up_segment_count": result.get("raw_step_up_segment_count", 0),
        "surviving_step_cluster_count": result.get(
            "surviving_step_cluster_count", 0
        ),
    }


def scan_all_runs(
    *,
    runs_dir: Path,
    summary_path: Path,
    start: str,
    end: str,
    include_grid_only: bool,
    force: bool,
    continue_on_error: bool,
    audit_callable: Callable[..., dict[str, object]] = audit,
    minimum_ground_photons: int = 3,
    maximum_uncertainty_m: float | None = None,
    minimum_epochs: int = 4,
    minimum_side_epochs: int = 2,
    minimum_step_m: float = 0.3,
    maximum_plateau_nmad_m: float = 0.25,
    minimum_step_dominance: float = 0.6,
    neighbor_distance_m: float = 250.0,
    minimum_neighbor_segments: int = 3,
    maximum_cluster_step_nmad_m: float = 0.25,
    cross_spot_distance_m: float = 500.0,
    candidate_limit_per_run: int = 20,
) -> dict[str, object]:
    selections, skipped = discover_completed_runs(
        runs_dir,
        include_grid_only=include_grid_only,
    )
    run_summaries: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    all_candidates: list[dict[str, object]] = []

    for position, selection in enumerate(selections, start=1):
        run_dir = selection.run_dir
        print(
            f"[{position}/{len(selections)}] scanning {run_dir.name}",
            file=sys.stderr,
            flush=True,
        )
        result_path = run_dir / RUN_RESULT_FILENAME
        geojson_path = run_dir / RUN_GEOJSON_FILENAME
        result = None if force else _read_cached_result(result_path)
        result_source = "cached"

        if result is None:
            result_source = "live_query"
            try:
                result = audit_callable(
                    run_dir=run_dir,
                    start=start,
                    end=end,
                    minimum_ground_photons=minimum_ground_photons,
                    maximum_uncertainty_m=maximum_uncertainty_m,
                    minimum_epochs=minimum_epochs,
                    minimum_side_epochs=minimum_side_epochs,
                    minimum_step_m=minimum_step_m,
                    maximum_plateau_nmad_m=maximum_plateau_nmad_m,
                    minimum_step_dominance=minimum_step_dominance,
                    neighbor_distance_m=neighbor_distance_m,
                    minimum_neighbor_segments=minimum_neighbor_segments,
                    maximum_cluster_step_nmad_m=maximum_cluster_step_nmad_m,
                    cross_spot_distance_m=cross_spot_distance_m,
                    candidate_limit=candidate_limit_per_run,
                )
            except Exception as exc:  # noqa: BLE001 - batch must isolate one run
                failure = {
                    "run": run_dir.name,
                    "status": "scan_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                failures.append(failure)
                print(
                    f"[{position}/{len(selections)}] failed {run_dir.name}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                if not continue_on_error:
                    raise
                continue

            payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
            result_path.write_text(payload, encoding="utf-8")
            geojson_path.write_text(
                json.dumps(_geojson(result), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        run_summaries.append(
            _compact_run_result(
                result,
                completion_markers=selection.completion_markers,
                result_source=result_source,
            )
        )
        all_candidates.extend(_candidate_rows(result, run_name=run_dir.name))

    ranked_candidates = rank_candidates(all_candidates)
    status = (
        "surviving_candidates_found"
        if ranked_candidates
        else "no_surviving_candidates_in_scanned_runs"
    )
    result = {
        "schema": "icesat2_all_runs_step_scan_v1",
        "status": status,
        "runs_directory": str(runs_dir),
        "selected_run_count": len(selections),
        "completed_run_count_scanned": len(run_summaries),
        "failed_run_count": len(failures),
        "skipped_directory_count": len(skipped),
        "surviving_candidate_count": len(ranked_candidates),
        "record_lookup_priority": ranked_candidates,
        "run_summaries": run_summaries,
        "failures": failures,
        "skipped_directories": skipped,
        "scan_parameters": {
            "query_start": start,
            "query_end": end,
            "include_grid_only": include_grid_only,
            "force": force,
            "minimum_ground_photons": minimum_ground_photons,
            "maximum_uncertainty_m": maximum_uncertainty_m,
            "minimum_epochs": minimum_epochs,
            "minimum_side_epochs": minimum_side_epochs,
            "minimum_step_m": minimum_step_m,
            "maximum_plateau_nmad_m": maximum_plateau_nmad_m,
            "minimum_step_dominance": minimum_step_dominance,
            "neighbor_distance_m": neighbor_distance_m,
            "minimum_neighbor_segments": minimum_neighbor_segments,
            "maximum_cluster_step_nmad_m": maximum_cluster_step_nmad_m,
            "cross_spot_distance_m": cross_spot_distance_m,
        },
        "interpretation": {
            "records_needed_only_for_ranked_survivors": True,
            "zero_candidates_means_no_record_lookup": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan every completed run AOI for ICESat-2 terrain steps."
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("./data/runs"))
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument(
        "--include-grid-only",
        action="store_true",
        help="Also scan grid-manifest directories without completed-run markers.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore valid cached per-run scan results and query every run again.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop after the first failed run instead of continuing.",
    )
    parser.add_argument("--minimum-ground-photons", type=int, default=3)
    parser.add_argument("--maximum-uncertainty-m", type=float, default=None)
    parser.add_argument("--minimum-epochs", type=int, default=4)
    parser.add_argument("--minimum-side-epochs", type=int, default=2)
    parser.add_argument("--minimum-step-m", type=float, default=0.3)
    parser.add_argument("--maximum-plateau-nmad-m", type=float, default=0.25)
    parser.add_argument("--minimum-step-dominance", type=float, default=0.6)
    parser.add_argument("--neighbor-distance-m", type=float, default=250.0)
    parser.add_argument("--minimum-neighbor-segments", type=int, default=3)
    parser.add_argument("--maximum-cluster-step-nmad-m", type=float, default=0.25)
    parser.add_argument("--cross-spot-distance-m", type=float, default=500.0)
    parser.add_argument("--candidate-limit-per-run", type=int, default=20)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    summary_path = args.summary_json or args.runs_dir / DEFAULT_SUMMARY_FILENAME
    try:
        result = scan_all_runs(
            runs_dir=args.runs_dir,
            summary_path=summary_path,
            start=args.start,
            end=args.end,
            include_grid_only=args.include_grid_only,
            force=args.force,
            continue_on_error=not args.stop_on_error,
            minimum_ground_photons=args.minimum_ground_photons,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            minimum_epochs=args.minimum_epochs,
            minimum_side_epochs=args.minimum_side_epochs,
            minimum_step_m=args.minimum_step_m,
            maximum_plateau_nmad_m=args.maximum_plateau_nmad_m,
            minimum_step_dominance=args.minimum_step_dominance,
            neighbor_distance_m=args.neighbor_distance_m,
            minimum_neighbor_segments=args.minimum_neighbor_segments,
            maximum_cluster_step_nmad_m=args.maximum_cluster_step_nmad_m,
            cross_spot_distance_m=args.cross_spot_distance_m,
            candidate_limit_per_run=args.candidate_limit_per_run,
        )
    except (Icesat2AuditError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "batch_scan_failed",
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed_run_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
