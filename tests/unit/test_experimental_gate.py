from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


PACKAGE_NAME = "app.pipeline.stages_experimental"


def test_experimental_package_import_requires_enable_flag(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_EXPERIMENTAL", raising=False)
    _clear_experimental_modules()

    with pytest.raises(ImportError, match="Experimental module not enabled"):
        importlib.import_module(PACKAGE_NAME)


def test_experimental_package_imports_with_flag_and_exposes_neutral_modules(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EXPERIMENTAL", "1")
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


def test_no_api_frontend_worker_or_orchestrator_refs_to_experimental_package() -> None:
    disallowed_roots = [
        Path("app/api"),
        Path("app/main.py"),
        Path("app/pipeline/orchestrator.py"),
        Path("app/workers"),
        Path("frontend"),
    ]
    checked_files = 0
    for root in disallowed_roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
        for path in paths:
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            checked_files += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "stages_experimental" not in text, f"unexpected experimental reference in {path}"
    assert checked_files > 0


def _clear_experimental_modules() -> None:
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            sys.modules.pop(name, None)
