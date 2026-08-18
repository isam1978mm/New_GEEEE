from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import numpy as np

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages import candidate_focus
from app.pipeline.stages.candidate_focus import CandidateFocusStage, build_candidate_focus_mask, select_candidate_focuses
from app.pipeline.stages.focus_mask import FOCUS_ANALYSIS_BANDS, FOCUS_RADIUS_M
from app.pipeline.stages.grid import grid_spec_from_manifest
from app.services.grid import GridManifest


def _grid_spec():
    manifest = GridManifest(
        epsg=32637,
        utm_zone=37,
        hemisphere="north",
        scale_m=10,
        size_px=9,
        crs_transform=[10.0, 0.0, 500000.0, 0.0, -10.0, 3600090.0],
        bounds_m={"xmin": 500000.0, "ymin": 3600000.0, "xmax": 500090.0, "ymax": 3600090.0},
    )
    return grid_spec_from_manifest(manifest)


def _write_classifier_rows(run_dir: Path) -> None:
    path = run_dir / "classifier" / "classifications.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "object_id",
        "cluster_id",
        "row_min",
        "row_max",
        "col_min",
        "col_max",
        "class_id",
        "class_score",
        "finding_label",
        "finding_score",
        "review_order",
    ]
    rows = [
        {"object_id": 11, "cluster_id": 1, "row_min": 4, "row_max": 4, "col_min": 4, "col_max": 4, "class_id": "a", "class_score": 0.20, "finding_label": "low", "finding_score": 0.20, "review_order": 4},
        {"object_id": 22, "cluster_id": 2, "row_min": 2, "row_max": 2, "col_min": 2, "col_max": 2, "class_id": "b", "class_score": 0.95, "finding_label": "first", "finding_score": 0.95, "review_order": 1},
        {"object_id": 33, "cluster_id": 3, "row_min": 6, "row_max": 6, "col_min": 6, "col_max": 6, "class_id": "c", "class_score": 0.85, "finding_label": "second", "finding_score": 0.85, "review_order": 2},
        {"object_id": 44, "cluster_id": 4, "row_min": 2, "row_max": 2, "col_min": 6, "col_max": 6, "class_id": "d", "class_score": 0.75, "finding_label": "third", "finding_score": 0.75, "review_order": 3},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _analysis_bands(size: int) -> dict[str, np.ndarray]:
    rows, cols = np.indices((size, size), dtype=np.float32)
    return {
        name: (rows * np.float32(0.07) + cols * np.float32(0.11) + np.float32(index + 1)).astype(np.float32)
        for index, name in enumerate(FOCUS_ANALYSIS_BANDS)
    }


def _settings(run_dir: Path, *, top_n: int = 3) -> Settings:
    data_dir = run_dir / "data"
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "db.sqlite",
        candidate_focus_top_n=top_n,
    )


def test_candidate_selection_uses_existing_classifier_scores_only(tmp_path: Path) -> None:
    _write_classifier_rows(tmp_path)

    selected = select_candidate_focuses(tmp_path, top_n=3)

    assert [item.candidate_id for item in selected] == ["object_22", "object_33", "object_44"]
    assert [item.source_score for item in selected] == [0.95, 0.85, 0.75]
    assert [item.review_order for item in selected] == [1, 2, 3]


def test_candidate_focus_uses_same_explicit_17m_radius_contract_as_user_focus() -> None:
    grid_spec = _grid_spec()
    mask = build_candidate_focus_mask(grid_spec=grid_spec, center_row=4.0, center_col=4.0)

    assert FOCUS_RADIUS_M == 17.0
    assert int(mask.sum()) == 9
    assert mask[4, 4]
    assert not mask[0, 0]


def test_candidate_focus_stage_writes_ranked_traceable_outputs_without_classifier_changes(tmp_path: Path, monkeypatch) -> None:
    grid_spec = _grid_spec()
    (tmp_path / "grid_manifest.json").write_text(
        json.dumps(grid_spec.manifest.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_classifier_rows(tmp_path)

    bands = _analysis_bands(grid_spec.size)
    support_stack = np.stack([bands[name] for name in list(FOCUS_ANALYSIS_BANDS)[:3]], axis=-1).astype(np.float32)
    monkeypatch.setattr(candidate_focus, "load_focus_analysis_bands", lambda run_dir, grid_spec: bands)
    monkeypatch.setattr(candidate_focus, "load_ai_ready_support_stack", lambda run_dir: support_stack)

    context = StageContext(run_id="run-1", settings=_settings(tmp_path, top_n=3), run_dir=tmp_path)
    result = asyncio.run(CandidateFocusStage().run(context))

    index_path = tmp_path / "full_job" / "candidate_focus" / "candidate_focus_index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload["selected_count"] == 3
    assert index_payload["requested_top_n"] == 3
    assert index_payload["user_focus_unchanged"] is True
    assert index_payload["classifier_behavior_changed"] is False
    assert [item["candidate_id"] for item in index_payload["candidates"]] == ["object_22", "object_33", "object_44"]
    assert "screening evidence only" in index_payload["scientific_warning"]

    first_dir = tmp_path / index_payload["candidates"][0]["relative_dir"]
    first_summary = json.loads((first_dir / "candidate_focus_summary.json").read_text(encoding="utf-8"))
    assert first_summary["focus_kind"] == "candidate_focus"
    assert first_summary["candidate_id"] == "object_22"
    assert first_summary["candidate_rank"] == 1
    assert first_summary["source_object_id"] == 22
    assert first_summary["source_score"] == 0.95
    assert first_summary["focus_radius_m"] == 17.0
    assert first_summary["focus_diameter_m"] == 34.0
    assert first_summary["source_classifier_contract"] == "existing_classifier_outputs_read_only"
    assert set(first_summary["center_wgs84"]) == {"lat", "lon"}
    assert (first_dir / "candidate_focus_pixel_report.csv").is_file()
    assert (first_dir / "candidate_focus_targets.csv").is_file()
    assert (first_dir / "candidate_focus_targets.geojson").is_file()
    assert (first_dir / "candidate_focus_hard_classifier.json").is_file()
    assert (first_dir / "candidate_focus_core_ring_scene.json").is_file()

    assert result.metadata["candidate_focus_selected_count"] == 3
    assert result.metadata["classifier_behavior_changed"] is False
    assert result.artifacts
    assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
    assert all(artifact.http_servable is False for artifact in result.artifacts)


def test_candidate_focus_top_n_is_configurable(tmp_path: Path, monkeypatch) -> None:
    grid_spec = _grid_spec()
    (tmp_path / "grid_manifest.json").write_text(json.dumps(grid_spec.manifest.model_dump()), encoding="utf-8")
    _write_classifier_rows(tmp_path)
    bands = _analysis_bands(grid_spec.size)
    support_stack = np.stack([bands[name] for name in list(FOCUS_ANALYSIS_BANDS)[:3]], axis=-1).astype(np.float32)
    monkeypatch.setattr(candidate_focus, "load_focus_analysis_bands", lambda run_dir, grid_spec: bands)
    monkeypatch.setattr(candidate_focus, "load_ai_ready_support_stack", lambda run_dir: support_stack)

    context = StageContext(run_id="run-2", settings=_settings(tmp_path, top_n=2), run_dir=tmp_path)
    asyncio.run(CandidateFocusStage().run(context))

    payload = json.loads(
        (tmp_path / "full_job" / "candidate_focus" / "candidate_focus_index.json").read_text(encoding="utf-8")
    )
    assert payload["requested_top_n"] == 2
    assert payload["selected_count"] == 2
    assert [item["candidate_id"] for item in payload["candidates"]] == ["object_22", "object_33"]
