from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = ROOT / "config" / "tyrone_3x_depth_known_geometry_blocked.json"


def test_tyrone_depth_pair_is_recorded_but_not_calibration_ready():
    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert payload["schema"] == "tyrone_3x_depth_evidence_v1"
    assert payload["status"] == "depth_known_geometry_blocked"
    assert payload["permit_id"] == "GR010RE"
    assert payload["nmed_discharge_permit_id"] == "DP-1341"

    anchors = {item["plot_id"]: item for item in payload["anchors"]}
    assert anchors["tyrone_tp5"]["measured_inches"] == [28.0, 26.0, 26.0, 28.0, 26.0]
    assert anchors["tyrone_tp5"]["mean_m"] == 0.68072
    assert anchors["tyrone_tp5"]["confidence_interval_95_m"] == [0.65532, 0.70612]
    assert anchors["tyrone_tp6"]["measured_inches"] == [40.0, 35.0, 42.0, 36.0, 34.0]
    assert anchors["tyrone_tp6"]["mean_m"] == 0.94996
    assert anchors["tyrone_tp6"]["confidence_interval_95_m"] == [0.8509, 1.04902]

    assert all(item["calibration_ready"] is False for item in anchors.values())
    assert all(
        item["geometry_status"] == "missing_coordinate_tied_polygon"
        for item in anchors.values()
    )

    decision = payload["decision"]
    assert decision["measured_depth_pair_proven"] is True
    assert decision["coordinate_tied_geometry_proven"] is False
    assert decision["stable_sentinel1_interval_proven"] is False
    assert decision["earth_engine_query_allowed"] is False
    assert decision["calibration_record_allowed"] is False
    assert decision["numerical_depth_ready"] is False
    assert decision["app_depth_enabled"] is False
    assert decision["campaign_004_status"] == "paused_fallback"
