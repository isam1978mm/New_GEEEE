from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.nb_results import build_nb_results
from app.services.storage import get_run_dir


def summarize_spatial_validation(payload: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    objects = payload.get("objects")
    if not isinstance(objects, list):
        objects = []

    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for item in objects:
        if not isinstance(item, dict):
            continue
        spatial = item.get("nb_spatial_validity")
        if not isinstance(spatial, dict):
            continue
        status = str(spatial.get("status") or "UNKNOWN")
        counts[status] += 1
        rows.append(
            {
                "object_id": item.get("object_id"),
                "status": status,
                "reasons": spatial.get("reasons") or [],
                "area_px": spatial.get("area_px"),
                "bbox_height_px": spatial.get("bbox_height_px"),
                "bbox_width_px": spatial.get("bbox_width_px"),
                "edge_touch": bool(spatial.get("edge_touch", False)),
                "oversized_region": bool(spatial.get("oversized_region", False)),
                "boundary_groups": spatial.get("boundary_groups") or [],
                "boundary_group_scores": spatial.get("boundary_group_scores") or {},
                "candidate_suppressed": bool(spatial.get("candidate_suppressed", False)),
                "interpretation_suppressed": bool(spatial.get("interpretation_suppressed", False)),
                "depth_suppressed": bool(spatial.get("depth_suppressed", False)),
            }
        )

    return {
        "run_id": run_id,
        "nb_status": payload.get("status"),
        "spatial_qa_mode": (payload.get("spatial_validity") or {}).get("mode"),
        "read_only": True,
        "classifier_modified": False,
        "candidate_suppression": False,
        "interpretation_suppression": False,
        "depth_suppression": False,
        "status_counts": dict(sorted(counts.items())),
        "objects": rows,
    }


def review_existing_run(*, run_id: str, run_dir: Path | None = None) -> dict[str, Any]:
    if run_dir is None:
        settings = get_settings()
        run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory does not exist: {run_dir}")
    payload = build_nb_results(run_dir)
    return summarize_spatial_validation(payload, run_id=run_id)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read an existing completed run and print the shadow-only NB spatial-validity "
            "diagnostics. The command does not modify run files, classifier output, NB scores, "
            "interpretation, or depth."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Optional explicit run directory. If omitted, DATA_DIR/runs/<run-id> is used.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = review_existing_run(run_id=args.run_id, run_dir=args.run_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
