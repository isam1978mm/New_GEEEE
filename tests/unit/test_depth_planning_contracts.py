from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ACTIVE_DEPTH_DOCS = (
    ROOT / "docs" / "DEPTH_ESTIMATION_EXECUTION_PLAN_2026-07-17.md",
    ROOT / "docs" / "DEPTH_CALIBRATION_DATASET_CONTRACT.md",
    ROOT / "docs" / "DEPTH_RELATIVE_BASELINE_SPEC.md",
    ROOT / "docs" / "DEPTH_NUMERICAL_RANGE_SPEC.md",
    ROOT / "docs" / "DEPTH_CONFOUNDER_CONTROL_SPEC.md",
    ROOT / "docs" / "DEPTH_APP_ARCHITECTURE_SPEC.md",
    ROOT / "docs" / "DEPTH_EASY_ENGLISH_PRESENTATION_SPEC.md",
    ROOT / "docs" / "DEPTH_VALIDATION_GATES_SPEC.md",
    ROOT / "docs" / "DEPTH_ROLLOUT_AND_COMPLETION_PLAN.md",
)


def test_active_depth_docs_use_neutral_reference_wording() -> None:
    for path in ACTIVE_DEPTH_DOCS:
        text = path.read_text(encoding="utf-8").casefold()
        assert "lawful" not in text, path


def test_execution_plan_separates_candidate_routing_from_depth_evidence() -> None:
    text = (ROOT / "docs" / "DEPTH_ESTIMATION_EXECUTION_PLAN_2026-07-17.md").read_text(encoding="utf-8")

    assert "used for routing only" in text
    assert "not as depth evidence" in text
    assert "classifier score and finding family" not in text
    assert "connected-component masks\n- approved independent sensor features" not in text


def test_calibration_manifest_template_preserves_private_local_boundary() -> None:
    payload = json.loads(
        (ROOT / "templates" / "depth_calibration" / "calibration_manifest.json").read_text(encoding="utf-8")
    )

    assert payload["artifact_class"] == "FILESYSTEM_ONLY"
    assert payload["filesystem_only"] is True
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False
    for key in (
        "dataset_id",
        "dataset_version",
        "records_sha256",
        "source_index_sha256",
        "exclusions_sha256",
        "content_hash",
        "manifest_hash",
    ):
        assert key in payload


def test_calibration_readme_documents_complete_private_workflow() -> None:
    text = (ROOT / "templates" / "depth_calibration" / "README.md").read_text(encoding="utf-8")

    assert "init_depth_calibration_pack.py" in text
    assert "validate_depth_calibration_pack.py" in text
    assert "finalize_depth_calibration_manifest.py" in text
    assert "Scientific holdout validation remains a later phase." in text
