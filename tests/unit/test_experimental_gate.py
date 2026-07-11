from __future__ import annotations

import importlib
import sys


PACKAGE_NAME = "app.pipeline.stages_experimental"


def test_experimental_package_imports_without_enable_flag(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_EXPERIMENTAL", raising=False)
    _clear_experimental_modules()

    package = importlib.import_module(PACKAGE_NAME)

    assert package.__all__ == ["classes", "classifier"]


def test_experimental_package_exposes_neutral_modules_without_env(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_EXPERIMENTAL", raising=False)
    _clear_experimental_modules()

    package = importlib.import_module(PACKAGE_NAME)
    classes_module = importlib.import_module(f"{PACKAGE_NAME}.classes")
    classifier_module = importlib.import_module(f"{PACKAGE_NAME}.classifier")

    assert package.__all__ == ["classes", "classifier"]
    assert classes_module.ClassId.Class_A.value == "Class_A"
    result = classifier_module.classify_feature_vector(
        classifier_module.NeutralFeatureVector(signal_mean=0.9, signal_peak=0.95, signal_spread=0.8)
    )
    assert result.class_id.value.startswith("Class_")
    assert result.class_family.startswith("family_")


def test_normal_classifier_stage_is_integration_wrapper() -> None:
    from app.pipeline.stages.classifier import ClassifierStage

    stage = ClassifierStage()
    assert stage.name == "classifier"
    assert stage.parity_reason == "Runs the core neutral classifier as a normal pipeline stage."


def _clear_experimental_modules() -> None:
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            sys.modules.pop(name, None)
