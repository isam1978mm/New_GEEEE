from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.run_quality import RunQualityStage, build_run_quality_summary, write_run_quality_summary


def test_run_quality_summary_unknown_when_no_upstream_qa_exists() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "UNKNOWN"
        assert summary["is_usable"] is False
        assert summary["unknowns"] == ["no_upstream_qa_summaries_found"]
        assert summary["blocking_reasons"] == []


def test_run_quality_summary_passes_when_required_gates_pass() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "PASS"
        assert summary["is_usable"] is True
        assert summary["blocking_reasons"] == []
        assert summary["warnings"] == []
        assert {check["name"] for check in summary["checks"]} == {
            "s2_indices",
            "s2_masks",
            "zero_shift",
            "alignment_qa",
            "classifier",
        }


def test_run_quality_summary_blocks_when_required_summary_is_missing_after_other_qa_exists() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_json(
            run_dir / "QA" / "grid_dem" / "zero_shift_summary.json",
            {"stage": "zero_shift", "status": "grid_locked", "failing_artifacts": []},
        )

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "BLOCKED"
        assert summary["is_usable"] is False
        assert "missing_s2_indices_summary" in summary["blocking_reasons"]
        assert "missing_alignment_qa_summary" in summary["blocking_reasons"]
        assert "missing_classifier_summary" in summary["blocking_reasons"]


def test_run_quality_summary_blocks_failed_alignment_and_zero_shift() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)
        _write_json(
            run_dir / "QA" / "grid_dem" / "zero_shift_summary.json",
            {"stage": "zero_shift", "status": "grid_drift_detected", "failing_artifacts": ["dem.tif"]},
        )
        _write_json(
            run_dir / "alignment_qa.json",
            {"pass": False, "checked_raster_count": 2, "failing_artifacts": ["dem.tif"]},
        )

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "BLOCKED"
        assert "zero_shift_not_grid_locked" in summary["blocking_reasons"]
        assert "alignment_qa_failed" in summary["blocking_reasons"]


def test_run_quality_summary_blocks_non_core_classifier_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)
        _write_json(
            run_dir / "classifier" / "summary.json",
            {
                "classifier_stage": "experimental",
                "classifier_quality": "unchecked",
                "classifier_version": "experimental_v1",
                "input_contract": "legacy",
                "object_count": 2,
            },
        )

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "BLOCKED"
        assert "classifier_not_core_stage" in summary["blocking_reasons"]
        assert "classifier_input_contract_not_validated" in summary["blocking_reasons"]


def test_run_quality_summary_warns_when_classifier_has_no_objects() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)
        _write_json(
            run_dir / "classifier" / "summary.json",
            {
                "classifier_stage": "core",
                "classifier_quality": "input_contract_validated",
                "classifier_version": "core_v1",
                "input_contract": "classifier_inputs_v1",
                "object_count": 0,
            },
        )

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "WARNING"
        assert summary["is_usable"] is True
        assert "classifier_no_objects_classified" in summary["warnings"]


def test_run_quality_summary_warns_for_low_but_above_minimum_s2_coverage() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir, source_valid_fraction=0.02, minimum_valid_fraction=0.001)

        summary = build_run_quality_summary(run_dir)

        assert summary["status"] == "WARNING"
        assert summary["is_usable"] is True
        assert summary["blocking_reasons"] == []
        assert "s2_source_valid_fraction_low_valid_fraction" in summary["warnings"]


def test_run_quality_stage_writes_redacted_public_artifact() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(RunQualityStage().run(context))

        assert result.metadata["status"] == "PASS"
        assert [artifact.name for artifact in result.artifacts] == ["run_quality_summary"]
        assert result.artifacts[0].artifact_class == ArtifactClass.REDACTED_PUBLIC
        summary_path = run_dir / "QA" / "run_quality" / "run_quality_summary.json"
        assert summary_path.is_file()
        assert json.loads(summary_path.read_text(encoding="utf-8"))["status"] == "PASS"


def test_write_run_quality_summary_persists_status_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _write_required_quality_inputs(run_dir)

        path = write_run_quality_summary(run_dir)

        assert path == run_dir / "QA" / "run_quality" / "run_quality_summary.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema"] == "run_quality_summary_v1"
        assert payload["status"] in {"PASS", "WARNING", "BLOCKED", "UNKNOWN"}


def _write_required_quality_inputs(
    run_dir: Path,
    *,
    source_valid_fraction: float = 0.95,
    minimum_valid_fraction: float = 0.001,
) -> None:
    _write_json(
        run_dir / "QA" / "stacks" / "s2_indices_summary.json",
        {
            "stage": "s2_indices",
            "minimum_valid_fraction": minimum_valid_fraction,
            "source_valid_fraction": source_valid_fraction,
            "index_summaries": {
                "NDVI": {"valid_fraction": source_valid_fraction},
                "NDWI": {"valid_fraction": source_valid_fraction},
            },
        },
    )
    _write_json(
        run_dir / "S2_MASKS" / "S2_DEM_MATCHED_MASKS_manifest.json",
        {
            "stage": "s2_indices",
            "masks": {
                "raw_valid_mask": {"valid_fraction": source_valid_fraction},
                "index_valid_mask": {"valid_fraction": source_valid_fraction},
            },
        },
    )
    _write_json(
        run_dir / "QA" / "grid_dem" / "zero_shift_summary.json",
        {"stage": "zero_shift", "status": "grid_locked", "failing_artifacts": []},
    )
    _write_json(
        run_dir / "alignment_qa.json",
        {"pass": True, "checked_raster_count": 3, "failing_artifacts": []},
    )
    _write_json(
        run_dir / "classifier" / "summary.json",
        {
            "classifier_stage": "core",
            "classifier_quality": "input_contract_validated",
            "classifier_version": "core_v1",
            "input_contract": "classifier_inputs_v1",
            "object_count": 2,
        },
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _settings(run_dir: Path) -> Settings:
    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
