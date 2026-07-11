from __future__ import annotations

import csv
import json
from pathlib import Path

from app.config import Settings
from app.services.v6_app_flow import (
    V6_PRIVATE_INPUT_RELATIVE_PATH,
    V6PrivatePackageAccessContext,
    generate_private_v6_package,
    load_v6_real_package_inputs,
)


def _settings(root: Path, run_id: str = "run-local") -> Settings:
    return Settings(
        data_dir=root,
        database_path=root / "test.db",
        v6_package_flow_enabled=True,
        operator_auth_trusted_proxy_enabled=True,
        operator_auth_oidc_enabled=False,
        allow_network_bind=False,
        operator_run_authorizations={"operator-1": [run_id]},
    )


def _access(run_id: str = "run-local") -> V6PrivatePackageAccessContext:
    return V6PrivatePackageAccessContext(
        actor_id="operator-1",
        is_authenticated=True,
        roles=("operator",),
        authorized_run_ids=(run_id,),
        request_id="req_paid_imagery_export_test",
    )


def test_paid_imagery_package_generate_creates_local_private_input_when_missing(tmp_path: Path) -> None:
    run_id = "run-local"
    settings = _settings(tmp_path, run_id=run_id)
    run_dir = _write_local_paid_imagery_sources(settings=settings, run_id=run_id)
    input_path = run_dir / V6_PRIVATE_INPUT_RELATIVE_PATH
    assert not input_path.exists()

    result = generate_private_v6_package(settings=settings, run_id=run_id, access_context=_access(run_id))

    assert result.status_code == 200
    assert result.body["outcome"] == "generated"
    assert result.body["package_ready"] is True
    assert input_path.is_file()
    package_inputs = load_v6_real_package_inputs(input_path)
    assert package_inputs.source_mode == "local_existing_run_outputs"
    assert package_inputs.package_provenance == "local_loopback_generated_from_private_run_outputs"
    assert package_inputs.fallback_geometry_used is True


def test_paid_imagery_loader_preserves_private_input_provenance(tmp_path: Path) -> None:
    path = tmp_path / "real_package_inputs.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "run-provenance",
                "timestamp": "20260103T010203Z",
                "source_mode": "local_existing_run_outputs",
                "score_basis": "source_columns:v6_review_priority_score",
                "geometry_basis": "aoi_bounds_split_evenly_across_ranked_candidates",
                "package_provenance": "local_loopback_generated_from_private_run_outputs",
                "fallback_score_used": False,
                "fallback_geometry_used": True,
                "placeholder_map_label": "visual_inspection_map_is_placeholder_no_imagery",
                "frozen_notebook_parity_claimed": False,
                "scored_candidates": [
                    _candidate_row("V6_CELL_R001_C001", rank=1, score=0.91),
                ],
                "request_zones": [
                    _zone_row("V6_RZ_001", "V6_CELL_R001_C001", rank=1, score=0.91),
                ],
            }
        ),
        encoding="utf-8",
    )

    package_inputs = load_v6_real_package_inputs(path)

    assert package_inputs.score_basis == "source_columns:v6_review_priority_score"
    assert package_inputs.geometry_basis == "aoi_bounds_split_evenly_across_ranked_candidates"
    assert package_inputs.package_provenance == "local_loopback_generated_from_private_run_outputs"
    assert package_inputs.fallback_score_used is False
    assert package_inputs.fallback_geometry_used is True
    assert package_inputs.frozen_notebook_parity_claimed is False


def _write_local_paid_imagery_sources(*, settings: Settings, run_id: str) -> Path:
    run_dir = settings.data_dir / "runs" / run_id
    location_dir = run_dir / "full_job" / "location"
    location_dir.mkdir(parents=True, exist_ok=True)
    location_dir.joinpath("site_location.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"export_role": "site_point"},
                        "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with (run_dir / "objects_index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["object_id", "v6_review_priority_score"])
        writer.writeheader()
        writer.writerow({"object_id": "object_a", "v6_review_priority_score": "0.9"})
        writer.writerow({"object_id": "object_b", "v6_review_priority_score": "0.7"})
    return run_dir


def _candidate_row(cell_id: str, *, rank: int, score: float) -> dict[str, object]:
    return {
        "cell_id": cell_id,
        "candidate_score": score,
        "remote_sensing_contrast": score,
        "s2_confidence": 1.0,
        "builtup_warning": 0,
        "cropland_heavy_warning": 0,
        "water_edge_warning": 0,
        "modern_linear_edge_warning": 0,
        "v6_building_warning": 0,
        "v6_road_like_warning": 0,
        "false_positive_warning_count": 0,
        "v6_false_positive_warning_count": 0,
        "v6_false_positive_penalty": 0.0,
        "v6_quality_adjusted_score": score,
        "v6_no_warning_bonus": 1.0,
        "v6_review_priority_score": score,
        "final_priority_rank_v6": rank,
    }


def _zone_row(zone_id: str, cell_id: str, *, rank: int, score: float) -> dict[str, object]:
    return {
        "request_zone_id": zone_id,
        "source_cell_id": cell_id,
        "quote_id": f"V6_QUOTE_{rank:03d}",
        "final_priority_rank_v6": rank,
        "v6_review_priority_score": score,
        "v6_false_positive_warning_count": 0,
        "bounds": {"west": 10.0, "south": 20.0, "east": 10.01, "north": 20.01},
    }
