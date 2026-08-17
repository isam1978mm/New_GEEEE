from __future__ import annotations

from scripts.review_nb_spatial_validity_for_existing_run import summarize_spatial_validation


def test_summary_is_read_only_and_preserves_shadow_statuses() -> None:
    payload = {
        "status": "available",
        "spatial_validity": {"mode": "shadow"},
        "objects": [
            {
                "object_id": 4,
                "nb_spatial_validity": {
                    "status": "FAIL",
                    "reasons": ["oversized_region", "grid_edge_touch"],
                    "area_px": 3943,
                    "bbox_height_px": 103,
                    "bbox_width_px": 83,
                    "edge_touch": True,
                    "oversized_region": True,
                    "boundary_groups": ["radar", "thermal"],
                    "boundary_group_scores": {"radar": 0.8, "thermal": 0.7},
                    "candidate_suppressed": False,
                    "interpretation_suppressed": False,
                    "depth_suppressed": False,
                },
            },
            {
                "object_id": 7,
                "nb_spatial_validity": {
                    "status": "PASS",
                    "reasons": [],
                    "area_px": 9,
                    "bbox_height_px": 3,
                    "bbox_width_px": 5,
                    "edge_touch": False,
                    "oversized_region": False,
                    "boundary_groups": [],
                    "boundary_group_scores": {},
                    "candidate_suppressed": False,
                    "interpretation_suppressed": False,
                    "depth_suppressed": False,
                },
            },
        ],
    }

    result = summarize_spatial_validation(payload, run_id="run-1")

    assert result["read_only"] is True
    assert result["classifier_modified"] is False
    assert result["candidate_suppression"] is False
    assert result["interpretation_suppression"] is False
    assert result["depth_suppression"] is False
    assert result["status_counts"] == {"FAIL": 1, "PASS": 1}
    assert [row["object_id"] for row in result["objects"]] == [4, 7]
    assert result["objects"][0]["reasons"] == ["oversized_region", "grid_edge_touch"]


def test_summary_handles_missing_spatial_metadata_without_inventing_status() -> None:
    payload = {
        "status": "partial",
        "spatial_validity": {"mode": "shadow"},
        "objects": [{"object_id": 1}, {"object_id": 2, "nb_spatial_validity": None}],
    }

    result = summarize_spatial_validation(payload, run_id="run-2")

    assert result["status_counts"] == {}
    assert result["objects"] == []
