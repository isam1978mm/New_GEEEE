from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.pipeline.depth.package import load_local_depth_package
from app.pipeline.depth.schema import CandidateDepthInput
from app.pipeline.stages.depth_estimation import (
    DEPTH_CANDIDATES_SCHEMA,
    DEPTH_INPUT_RELATIVE_PATH,
    write_depth_outputs,
)


def _load_candidate_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("candidate input file does not exist")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("candidate input is not readable JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("candidate input must be a JSON object")
    if payload.get("schema_version") != DEPTH_CANDIDATES_SCHEMA:
        raise ValueError("unsupported candidate input schema")

    raw_candidates = payload.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ValueError("candidate input must contain at least one candidate")

    canonical_candidates: list[dict[str, str]] = []
    seen_candidate_ids: set[str] = set()
    for raw_candidate in raw_candidates:
        if not isinstance(raw_candidate, dict):
            raise ValueError("candidate entry must be a JSON object")
        candidate = CandidateDepthInput.from_mapping(raw_candidate)
        if candidate.candidate_id in seen_candidate_ids:
            raise ValueError(f"duplicate candidate_id: {candidate.candidate_id}")
        seen_candidate_ids.add(candidate.candidate_id)
        canonical_candidates.append(
            {
                "candidate_id": candidate.candidate_id,
                "zone_id": candidate.zone_id,
            }
        )

    return {
        "schema_version": DEPTH_CANDIDATES_SCHEMA,
        "candidates": canonical_candidates,
    }


def run_local_depth_for_existing_run(
    *,
    run_dir: Path,
    package_dir: Path,
    candidate_input: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Write private local depth outputs for an already completed local run.

    This function does not call Earth Engine, change the run database, alter the
    classifier result, or expose the filesystem-only depth artifacts through HTTP.
    """

    run_dir = Path(run_dir)
    package_dir = Path(package_dir)
    candidate_input = Path(candidate_input)

    if not run_dir.is_dir():
        raise FileNotFoundError("run directory does not exist")

    package = load_local_depth_package(package_dir)
    candidate_payload = _load_candidate_payload(candidate_input)

    destination = run_dir / DEPTH_INPUT_RELATIVE_PATH
    if destination.exists() and not force:
        raise FileExistsError("run already has local depth candidate input; use --force to replace it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(candidate_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    return {
        "status": summary["status"],
        "candidate_count": summary["candidate_count"],
        "estimated_count": summary["estimated_count"],
        "insufficient_data_count": summary["insufficient_data_count"],
        "not_available_count": summary["not_available_count"],
        "method_version": package.method_version,
        "calibration_dataset_version": package.calibration_dataset_version,
        "run_quality_status": summary["run_quality_status"],
        "outputs": [
            paths.estimates_csv.relative_to(run_dir).as_posix(),
            paths.summary_json.relative_to(run_dir).as_posix(),
            paths.method_manifest_json.relative_to(run_dir).as_posix(),
        ],
        "warnings": summary["warnings"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run private local depth on an existing completed run directory.",
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--package-dir", required=True, type=Path)
    parser.add_argument("--candidate-input", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing depth_inputs/candidates.json file.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = run_local_depth_for_existing_run(
        run_dir=args.run_dir,
        package_dir=args.package_dir,
        candidate_input=args.candidate_input,
        force=args.force,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
