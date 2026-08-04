from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SCRIPT_PATH = SCRIPTS_DIR / "finalize_icesat2_broad_track_candidates.py"
SPEC = importlib.util.spec_from_file_location(
    "finalize_icesat2_broad_track_candidates", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _segment(segment_id: str, *, pattern: str) -> dict[str, object]:
    if pattern == "recovery":
        heights = [100.5, 100.0, 100.0, 100.55, 100.5, 100.52]
    elif pattern == "stable":
        heights = [100.0, 100.0, 100.0, 100.55, 100.5, 100.52]
    elif pattern == "late_reversal":
        heights = [100.0, 100.0, 100.0, 100.55, 100.5, 100.05]
    elif pattern == "immediate_reversal":
        heights = [100.0, 100.0, 100.0, 100.55, 100.1, 100.5]
    else:
        raise ValueError(f"unknown pattern: {pattern}")
    cycles = [12, 14, 15, 16, 17, 24]
    return {
        "classification": "step_up_candidate",
        "segment_id": segment_id,
        "rgt": 844,
        "spot": 3,
        "pre_cycle": 15,
        "post_cycle": 16,
        "event_start": "2022-05-17T00:00:00+00:00",
        "event_end": "2022-08-16T00:00:00+00:00",
        "longitude": -114.97,
        "latitude": 35.68,
        "step_m": 0.5,
        "pre_median_m": 100.0,
        "post_median_m": 100.5,
        "timeline": [
            {
                "cycle": cycle,
                "height_m": height,
                "observed_at": f"202{index}-01-01T00:00:00+00:00",
            }
            for index, (cycle, height) in enumerate(zip(cycles, heights), start=1)
        ],
    }


def _write_campaign(
    tmp_path: Path,
    *,
    pattern: str,
    median_step_m: float = 0.5,
    segment_count: int = 4,
) -> Path:
    campaign_dir = tmp_path / "campaign"
    region_dir = campaign_dir / "region_a"
    region_dir.mkdir(parents=True)
    summary = {
        "campaign_id": "campaign",
        "failed_tile_count": 0,
        "record_lookup_priority": [
            {
                "campaign_rank": 1,
                "global_rank": 1,
                "region_id": "region_a",
                "region_local_rank": 1,
                "longitude": -114.97,
                "latitude": 35.68,
                "median_step_m": median_step_m,
                "segment_count": segment_count,
                "event_start": "2022-05-17T00:00:00+00:00",
                "event_end": "2022-08-16T00:00:00+00:00",
            }
        ],
    }
    segments = [
        _segment(f"{index:03d}", pattern=pattern)
        for index in range(1, segment_count + 1)
    ]
    cluster = {
        "centroid_longitude": -114.97,
        "centroid_latitude": 35.68,
        "segment_count": segment_count,
        "median_step_m": median_step_m,
        "step_nmad_m": 0.01,
        "event_start": "2022-05-17T00:00:00+00:00",
        "event_end": "2022-08-16T00:00:00+00:00",
        "cross_spot_supported": False,
        "segments": segments,
    }
    region = {
        "region_id": "region_a",
        "surviving_step_clusters": [cluster],
    }
    (campaign_dir / "campaign_summary.json").write_text(
        json.dumps(summary), encoding="utf-8"
    )
    (region_dir / "region_scan.json").write_text(
        json.dumps(region), encoding="utf-8"
    )
    return campaign_dir


def test_recovery_candidate_is_removed_from_context_queue(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path, pattern="recovery")

    result = MODULE.finalize_campaign(campaign_dir=campaign_dir)

    assert result["status"] == "all_spatial_candidates_rejected_by_temporal_recovery"
    assert result["schema"] == "icesat2_broad_track_campaign_finalized_v3"
    assert result["source_spatial_candidate_count"] == 1
    assert result["temporal_recovery_rejected_count"] == 1
    assert result["terminal_stability_rejected_count"] == 0
    assert result["context_priority_deferred_count"] == 0
    assert result["context_review_candidate_count"] == 0
    assert result["context_review_priority"] == []
    assert result["record_lookup_priority"] == []
    assert result["records_research_ready"] is False
    assert (campaign_dir / "candidate_001_context_priority_audit.json").is_file()


def test_stable_plausible_rise_enters_context_review_only(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path, pattern="stable")

    result = MODULE.finalize_campaign(campaign_dir=campaign_dir)

    assert result["status"] == "finalized_context_review_candidates_found"
    assert result["temporal_recovery_rejected_count"] == 0
    assert result["terminal_stability_rejected_count"] == 0
    assert result["context_priority_deferred_count"] == 0
    assert result["context_review_candidate_count"] == 1
    assert result["record_lookup_priority"] == []
    candidate = result["context_review_priority"][0]
    assert candidate["context_priority_rank"] == 1
    assert candidate["terminal_stability_audit"]["status"] == (
        "terminal_stability_not_disproved"
    )
    assert candidate["context_priority_audit"]["status"] == (
        "context_review_priority"
    )
    assert candidate["context_priority_audit"]["records_research_recommended"] is False


def test_late_epoch_reversal_is_removed_from_context_queue(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path, pattern="late_reversal")

    result = MODULE.finalize_campaign(campaign_dir=campaign_dir)

    assert result["status"] == (
        "all_spatial_candidates_rejected_by_temporal_or_terminal_stability"
    )
    assert result["terminal_stability_rejected_count"] == 1
    assert result["context_review_candidate_count"] == 0
    rejected = result["terminal_stability_rejections"][0]
    assert rejected["terminal_stability_audit"]["status"] == (
        "late_epoch_reversal_pattern"
    )


def test_immediate_reversal_is_removed_from_context_queue(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path, pattern="immediate_reversal")

    result = MODULE.finalize_campaign(campaign_dir=campaign_dir)

    assert result["terminal_stability_rejected_count"] == 1
    assert result["context_review_candidate_count"] == 0
    rejected = result["terminal_stability_rejections"][0]
    assert rejected["terminal_stability_audit"]["status"] == (
        "immediate_post_step_reversal_pattern"
    )


def test_extreme_magnitude_is_deferred_before_context_review(tmp_path: Path):
    campaign_dir = _write_campaign(
        tmp_path,
        pattern="stable",
        median_step_m=12.0,
    )

    result = MODULE.finalize_campaign(campaign_dir=campaign_dir)

    assert result["status"] == "all_temporal_survivors_deferred_by_context_priority"
    assert result["context_priority_deferred_count"] == 1
    assert result["context_review_candidate_count"] == 0
    deferred = result["context_priority_deferrals"][0]
    assert deferred["context_priority_audit"]["status"] == (
        "deferred_direct_thickness_magnitude"
    )
