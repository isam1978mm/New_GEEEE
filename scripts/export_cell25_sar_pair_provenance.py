from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ee

from app.config import get_settings
from app.pipeline.stages.grid import grid_spec_from_manifest
from app.pipeline.stages.sar_rtc import (
    DEFAULT_END,
    DEFAULT_START,
    MAX_ORBIT_DT_DAYS,
    MAX_PAIR_DT_HOURS,
    S1_COLLECTION_ID,
    SAR_SELECTION_PROFILE,
    apply_orbit_window,
    build_s1_base_collection,
    fc_time_ids,
    pick_best_track,
    select_pairs,
)
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export local-only true Cell 25 SAR pair provenance for a run grid."
    )
    parser.add_argument("--app-run-dir", type=Path, required=True, help="App run directory containing grid_manifest.json.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Local directory where QA sidecar JSON is written.")
    parser.add_argument("--run-id", type=str, default="", help="Optional run id for the sidecar filename.")
    parser.add_argument("--start-date", type=str, default=DEFAULT_START, help="SAR start date, default matches Cell 25.")
    parser.add_argument("--end-date", type=str, default=DEFAULT_END, help="SAR exclusive end date, default matches Cell 25.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grid_manifest_path = args.app_run_dir / "grid_manifest.json"
    grid_manifest = GridManifest.model_validate_json(grid_manifest_path.read_text(encoding="utf-8"))
    grid_spec = grid_spec_from_manifest(grid_manifest)

    initialize_ee_session(get_settings())
    payload = build_cell25_pair_provenance_payload(
        grid_spec=grid_spec,
        start_date=args.start_date,
        end_date=args.end_date,
        run_id=args.run_id or args.app_run_dir.name,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"QA_RADAR_CELL25_PAIR_IDS_{payload['run_id']}_pairs4_pairdt36h_orbitpm9d.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(output_path)
    return 0


def build_cell25_pair_provenance_payload(
    *,
    grid_spec,
    start_date: str,
    end_date: str,
    run_id: str,
) -> dict[str, Any]:
    base = build_s1_base_collection(grid_spec, start_date=start_date, end_date=end_date)
    asc = pick_best_track(
        base.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING")),
        pass_direction="ASCENDING",
        start_date=start_date,
        end_date=end_date,
    )
    desc = pick_best_track(
        base.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING")),
        pass_direction="DESCENDING",
        start_date=start_date,
        end_date=end_date,
    )
    asc_track = int(asc.first().get("relativeOrbitNumber_start").getInfo())
    desc_track = int(desc.first().get("relativeOrbitNumber_start").getInfo())
    asc_items = fc_time_ids(asc)
    desc_items = fc_time_ids(desc)
    pairs = select_pairs(asc_items, desc_items)
    orbit_ms = MAX_ORBIT_DT_DAYS * 24 * 60 * 60 * 1000
    asc_windowed, _ = apply_orbit_window(asc_items, orbit_ms)
    desc_windowed, _ = apply_orbit_window(desc_items, orbit_ms)
    return {
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "run_id": run_id,
        "collection_id": S1_COLLECTION_ID,
        "source_profile": SAR_SELECTION_PROFILE,
        "filename_profile": "pairs4_pairdt36h_orbitpm9d",
        "start_date": start_date,
        "end_date": end_date,
        "orbit_window_days": MAX_ORBIT_DT_DAYS,
        "pair_cap_hours": MAX_PAIR_DT_HOURS,
        "selected_asc_track": asc_track,
        "selected_desc_track": desc_track,
        "asc_windowed_count": len(asc_windowed),
        "desc_windowed_count": len(desc_windowed),
        "pair_count": len(pairs),
        "pairs": [
            {
                "asc_id": pair.asc_id,
                "desc_id": pair.desc_id,
                "asc_timestamp": _ms_to_iso(pair.asc_ms),
                "desc_timestamp": _ms_to_iso(pair.desc_ms),
                "dt_hours": round(pair.dt_ms / (60.0 * 60.0 * 1000.0), 6),
            }
            for pair in pairs
        ],
    }


def _ms_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000.0, tz=UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
