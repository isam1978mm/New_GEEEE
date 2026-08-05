from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit_campaign006_fdep_footprints.py"
SPEC = importlib.util.spec_from_file_location("campaign006_fdep_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _dossier(rank: int = 3) -> dict:
    return {
        "candidate_id": f"candidate_{rank:03d}",
        "campaign_rank": rank,
        "candidate_summary": {
            "longitude": -81.61,
            "latitude": 27.36,
            "median_step_m": 1.5,
        },
        "segment_count": 2,
        "segments": [
            {"segment_id": "a", "longitude": -81.6100, "latitude": 27.3600},
            {"segment_id": "b", "longitude": -81.6101, "latitude": 27.3601},
        ],
    }


def test_decode_attributes_uses_coded_domain_labels():
    decoded = MODULE._decode_attributes(
        {"MINE_NAME": 11, "REC_STATUS": "WC"},
        {
            "MINE_NAME": {11: "Fort Meade", "11": "Fort Meade"},
            "REC_STATUS": {"WC": "Work Complete"},
        },
    )
    assert decoded["MINE_NAME"] == "Fort Meade"
    assert decoded["REC_STATUS"] == "Work Complete"


def test_shared_identities_requires_one_feature_at_every_point():
    rows = [
        {"feature_identities": ["Mine A", "Mine B"]},
        {"feature_identities": ["Mine A"]},
    ]
    assert MODULE._shared_identities(rows) == ["Mine A"]
    assert MODULE._shared_identities(
        [{"feature_identities": ["Mine A"]}, {"feature_identities": []}]
    ) == []


def test_candidate_decision_prefers_exact_reclamation_unit():
    decision = MODULE._candidate_decision(
        [
            {
                "layer_key": "active_mine_2021",
                "all_supporting_points_share_one_feature": True,
            },
            {
                "layer_key": "released_mine_2024",
                "all_supporting_points_share_one_feature": False,
            },
            {
                "layer_key": "released_reclamation_units",
                "all_supporting_points_share_one_feature": True,
            },
        ]
    )
    assert decision["status"] == (
        "single_official_reclamation_unit_covers_all_segments"
    )
    assert decision["manual_footprint_review_survives"] is True
    assert decision["records_research_ready"] is False
    assert decision["candidate_is_depth_anchor"] is False


def test_audit_layer_checks_every_supporting_point():
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        calls.append((url, params))
        if not url.endswith("/query"):
            return {
                "fields": [
                    {
                        "name": "MINE_NAME",
                        "domain": {
                            "codedValues": [{"code": 11, "name": "Fort Meade"}]
                        },
                    }
                ]
            }
        return {
            "features": [
                {
                    "attributes": {
                        "OBJECTID": 9,
                        "MINE_NAME": 11,
                        "SITE_ID": 123,
                    }
                }
            ]
        }

    result = MODULE.audit_layer(
        _dossier(),
        layer={"key": "active_mine_2021", "layer_id": 13, "label": "Active"},
        timeout_seconds=5.0,
        fetch_json=fake_fetch,
    )
    query_calls = [item for item in calls if item[0].endswith("/query")]
    assert len(query_calls) == 2
    assert result["matched_point_count"] == 2
    assert result["all_supporting_points_matched"] is True
    assert result["all_supporting_points_share_one_feature"] is True
    assert "Fort Meade" in result["shared_features"][0]


def test_run_audit_keeps_depth_and_records_flags_closed(tmp_path: Path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()
    (campaign_dir / "candidate_003_dossier.json").write_text(
        __import__("json").dumps(_dossier()), encoding="utf-8"
    )

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        if not url.endswith("/query"):
            return {"fields": []}
        return {"features": []}

    result = MODULE.run_audit(
        campaign_dir=campaign_dir,
        ranks=[3],
        timeout_seconds=5.0,
        fetch_json=fake_fetch,
    )
    assert result["status"] == "no_official_fdep_footprint_survivors"
    assert result["footprint_survivor_count"] == 0
    assert result["record_lookup_priority"] == []
    assert result["records_research_ready"] is False
    assert result["numerical_depth_unlocked"] is False
    assert result["interpretation"]["candidate_is_depth_anchor"] is False
