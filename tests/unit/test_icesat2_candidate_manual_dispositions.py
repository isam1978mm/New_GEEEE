from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SCRIPT_PATH = SCRIPTS_DIR / "apply_icesat2_candidate_manual_dispositions.py"
SPEC = importlib.util.spec_from_file_location(
    "apply_icesat2_candidate_manual_dispositions", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write_campaign(tmp_path: Path) -> Path:
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()
    finalized = {
        "schema": "icesat2_broad_track_campaign_finalized_v3",
        "status": "finalized_context_review_candidates_found",
        "campaign_id": "campaign_a",
        "context_review_candidate_count": 1,
        "surviving_candidate_count": 1,
        "context_review_priority": [
            {
                "campaign_rank": 9,
                "source_campaign_rank": 9,
                "context_priority_rank": 1,
                "latitude": 32.769,
                "longitude": -115.413,
                "median_step_m": 0.808,
                "segment_count": 5,
            }
        ],
        "record_lookup_priority": [],
        "records_research_ready": False,
        "interpretation": {
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
    }
    dispositions = {
        "schema": "icesat2_candidate_manual_dispositions_v1",
        "campaign_id": "campaign_a",
        "dispositions": [
            {
                "campaign_rank": 9,
                "status": "closed_after_parcel_context",
                "reason": "The support line crosses multiple large agricultural parcels.",
                "decision": {
                    "context_review_recommended": False,
                    "records_research_recommended": False,
                    "candidate_is_depth_anchor": False,
                },
            }
        ],
    }
    (campaign_dir / "campaign_finalized_summary.json").write_text(
        json.dumps(finalized), encoding="utf-8"
    )
    (campaign_dir / "candidate_manual_dispositions.json").write_text(
        json.dumps(dispositions), encoding="utf-8"
    )
    return campaign_dir


def test_manual_parcel_closure_removes_last_context_candidate(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path)

    result = MODULE.apply_manual_dispositions(campaign_dir=campaign_dir)

    assert result["schema"] == "icesat2_broad_track_campaign_decision_v1"
    assert result["status"] == (
        "all_context_review_candidates_closed_by_manual_review"
    )
    assert result["automated_context_review_candidate_count"] == 1
    assert result["manual_context_closed_count"] == 1
    assert result["context_review_candidate_count"] == 0
    assert result["surviving_candidate_count"] == 0
    assert result["context_review_priority"] == []
    assert result["record_lookup_priority"] == []
    assert result["records_research_ready"] is False
    closure = result["manual_context_closures"][0]
    assert closure["campaign_rank"] == 9
    assert closure["manual_context_disposition"]["status"] == (
        "closed_after_parcel_context"
    )
    assert (campaign_dir / "campaign_decision_summary.json").is_file()


def test_unknown_manual_candidate_rank_is_rejected(tmp_path: Path):
    campaign_dir = _write_campaign(tmp_path)
    path = campaign_dir / "candidate_manual_dispositions.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["dispositions"][0]["campaign_rank"] = 10
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        MODULE.apply_manual_dispositions(campaign_dir=campaign_dir)
    except ValueError as exc:
        assert "not in the context-review queue" in str(exc)
    else:
        raise AssertionError("unknown manual candidate rank should fail")
