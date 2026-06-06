from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.pipeline.parity import ParityPathError
from app.services.redaction import verify_redacted


FORBIDDEN_WORDING = {
    "confirmed",
    "found",
    "proven",
    "dig target",
    "definitely",
    "discovery",
    "burial proven",
    "tomb confirmed",
    "target confirmed",
    "excavation recommendation",
    "field action recommendation",
}

FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
}

ALLOWED_SCORE_FIELDS = {
    "class_id",
    "class_label",
    "score",
    "probability",
    "normalized_score",
    "uncertainty",
    "rank",
    "input_family",
    "method",
    "warnings",
    "runtime_output_verified",
    "notebook_value_parity_verified",
}


def _write_input_manifest(run_dir: Path) -> Path:
    manifest_path = run_dir / "inputs" / "private_classifier_inputs.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase_f_private_classifier_inputs_v1",
                "items": [
                    {"input_family": "phase_c_semantic_feature_writers", "score": 0.8},
                    {"input_family": "phase_d_private_geojson_writer", "score": 0.2},
                    {"input_family": "phase_e_private_verifier", "score": 0.0},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def test_classifier_is_disabled_when_experimental_flag_is_absent(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-disabled",
    )

    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert result.status == "disabled"
    assert payload["status"] == "disabled"
    assert payload["enabled"] is False
    assert payload["items"] == []
    assert payload["runtime_output_verified"] is False
    assert payload["notebook_value_parity_verified"] is False


def test_classifier_runs_only_with_explicit_experimental_flag(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-enabled",
        enable_experimental_classifier=True,
    )

    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert result.status == "scored"
    assert payload["enabled"] is True
    assert payload["runtime_output_verified"] is True
    assert payload["notebook_value_parity_verified"] is False
    assert [item["class_id"] for item in payload["items"]] == [
        "Class_A",
        "Class_B",
        "Class_C",
    ]
    assert [item["rank"] for item in payload["items"]] == [1, 2, 3]


def test_cli_option_enables_private_classifier(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import main

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    exit_code = main(
        [
            "--run-dir",
            str(run_dir),
            "--input-manifest",
            str(manifest_path),
            "--run-id",
            "phase-f-cli",
            "--enable-experimental-classifier",
        ]
    )

    assert exit_code == 0
    report_path = run_dir / "manifests" / "private_neutral_classifier_report.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "scored"


def test_environment_flag_enables_private_classifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)
    monkeypatch.setenv("ENABLE_EXPERIMENTAL_CLASSIFIER", "1")

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-env",
    )

    assert result.status == "scored"


def test_invalid_input_path_and_path_traversal_are_rejected(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    outside_manifest = tmp_path / "outside.json"
    outside_manifest.write_text("{}", encoding="utf-8")

    with pytest.raises(ParityPathError):
        run_private_cli_classifier(
            run_dir=run_dir,
            input_manifest=outside_manifest,
            run_id="phase-f-outside",
            enable_experimental_classifier=True,
        )

    with pytest.raises(ParityPathError):
        run_private_cli_classifier(
            run_dir=run_dir,
            input_manifest="../outside.json",
            run_id="phase-f-traversal",
            enable_experimental_classifier=True,
        )


def test_output_path_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-path",
        enable_experimental_classifier=True,
    )

    assert result.report_path.resolve().is_relative_to(run_dir.resolve())


def test_output_schema_uses_neutral_labels_and_probability_fields_only(
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-schema",
        enable_experimental_classifier=True,
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    for item in payload["items"]:
        assert set(item) <= ALLOWED_SCORE_FIELDS
        assert item["class_id"].startswith("Class_")
        assert item["class_label"] == item["class_id"]
        assert 0.0 <= item["score"] <= 1.0
        assert 0.0 <= item["probability"] <= 1.0
        assert 0.0 <= item["normalized_score"] <= 1.0
        assert 0.0 <= item["uncertainty"] <= 1.0


def test_output_contains_no_forbidden_wording_paths_or_coordinates(
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    result = run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-redaction",
        enable_experimental_classifier=True,
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    verify_redacted(payload["redacted_summary"])
    serialized_report = json.dumps(payload, sort_keys=True).lower()
    serialized_summary = json.dumps(payload["redacted_summary"], sort_keys=True).lower()
    assert all(term not in serialized_report for term in FORBIDDEN_WORDING)
    assert str(tmp_path).lower() not in serialized_summary
    assert "coordinates" not in serialized_summary
    assert "geometry" not in serialized_summary
    assert "latitude" not in serialized_summary
    assert "longitude" not in serialized_summary


def test_no_non_json_artifact_files_are_created_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.private_cli_classifier import run_private_cli_classifier

    run_dir = tmp_path / "run"
    manifest_path = _write_input_manifest(run_dir)

    run_private_cli_classifier(
        run_dir=run_dir,
        input_manifest=manifest_path,
        run_id="phase-f-no-artifacts",
        enable_experimental_classifier=True,
    )

    forbidden = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert forbidden == []


def test_module_adds_no_public_runtime_earth_engine_or_model_hooks() -> None:
    import app.pipeline.parity.private_cli_classifier as module

    source = inspect.getsource(module)

    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "BackgroundTasks" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "torch" not in source
    assert "tensorflow" not in source
    assert "onnx" not in source.lower()
    assert "joblib" not in source.lower()
    assert "fit(" not in source
    assert "predict(" not in source
