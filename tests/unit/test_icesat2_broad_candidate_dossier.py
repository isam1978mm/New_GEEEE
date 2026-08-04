from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "extract_icesat2_broad_candidate_dossier.py"
)
SPEC = importlib.util.spec_from_file_location(
    "extract_icesat2_broad_candidate_dossier", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _segment(segment_id: str, longitude: float, step_m: float):
    return {
        "rgt": 844,
        "spot": 3,
        "segment_id": segment_id,
        "longitude": longitude,
        "latitude": 35.68,
        "pre_cycle": 15,
        "post_cycle": 16,
        "event_start": "2022-05-17T00:00:00+00:00",
        "event_end": "2022-08-16T00:00:00+00:00",
        "step_m": step_m,
        "timeline": [
            {"cycle": 14, "height_m": 100.0},
            {"cycle": 15, "height_m": 100.0},
            {"cycle": 16, "height_m": 100.5},
            {"cycle": 17, "height_m": 100.5},
        ],
    }


def _summary():
    return {
        "campaign_id": "campaign",
        "record_lookup_priority": [
            {
                "campaign_rank": 1,
                "global_rank": 1,
                "region_id": "region_a",
                "region_local_rank": 1,
                "longitude": -114.97,
                "latitude": 35.68,
            }
        ],
    }


def _region():
    return {
        "region_id": "region_a",
        "surviving_step_clusters": [
            {
                "centroid_longitude": -114.97,
                "centroid_latitude": 35.68,
                "segment_count": 3,
                "median_step_m": 0.5,
                "step_nmad_m": 0.05,
                "cross_spot_supported": False,
                "segments": [
                    _segment("003", -114.969, 0.55),
                    _segment("001", -114.971, 0.45),
                    _segment("002", -114.970, 0.50),
                ],
            }
        ],
    }


def test_build_dossier_preserves_and_sorts_segments():
    result = MODULE.build_dossier(
        campaign_summary=_summary(),
        region_result=_region(),
        candidate_rank=1,
    )

    assert result["schema"] == "icesat2_broad_candidate_dossier_v1"
    assert result["candidate_id"] == "campaign_rank_001"
    assert [item["segment_id"] for item in result["segments"]] == [
        "001",
        "002",
        "003",
    ]
    assert result["quality_checks"]["cluster_segment_count_matches"] is True
    assert result["quality_checks"]["all_segments_share_one_event_key"] is True
    assert result["quality_checks"]["segment_step_range_m"] == pytest.approx(0.10)
    assert result["interpretation"]["candidate_is_depth_anchor"] is False


def test_build_dossier_rejects_region_mismatch():
    region = _region()
    region["region_id"] = "other"
    try:
        MODULE.build_dossier(
            campaign_summary=_summary(),
            region_result=region,
            candidate_rank=1,
        )
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("mismatched region should fail")


def test_candidate_rank_must_exist():
    try:
        MODULE.build_dossier(
            campaign_summary=_summary(),
            region_result=_region(),
            candidate_rank=2,
        )
    except ValueError as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("missing rank should fail")


def test_geojson_contains_supporting_segments_and_centroid():
    dossier = MODULE.build_dossier(
        campaign_summary=_summary(),
        region_result=_region(),
        candidate_rank=1,
    )
    geojson = MODULE._geojson(dossier)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 4
    roles = [item["properties"]["feature_role"] for item in geojson["features"]]
    assert roles.count("supporting_atl08_segment") == 3
    assert roles.count("cluster_centroid") == 1


def test_extract_reads_local_results_and_writes_outputs(tmp_path: Path):
    campaign_dir = tmp_path / "campaign"
    region_dir = campaign_dir / "region_a"
    region_dir.mkdir(parents=True)
    (campaign_dir / "campaign_summary.json").write_text(
        json.dumps(_summary()),
        encoding="utf-8",
    )
    (region_dir / "region_scan.json").write_text(
        json.dumps(_region()),
        encoding="utf-8",
    )
    output_json = campaign_dir / "candidate.json"
    output_geojson = campaign_dir / "candidate.geojson"

    result = MODULE.extract(
        campaign_dir=campaign_dir,
        candidate_rank=1,
        output_json=output_json,
        output_geojson=output_geojson,
    )

    assert result["segment_count"] == 3
    assert output_json.is_file()
    assert output_geojson.is_file()
    written = json.loads(output_json.read_text(encoding="utf-8"))
    assert written["candidate_id"] == "campaign_rank_001"
