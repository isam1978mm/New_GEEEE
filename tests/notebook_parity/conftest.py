from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import pytest

from app.pipeline._base import ParityCategory, Stage


@dataclass(frozen=True, slots=True)
class ParityRegistryEntry:
    stage_module: str
    stage_class: str
    expected_category: ParityCategory


PARITY_TEST_REGISTRY: dict[str, ParityRegistryEntry] = {
    "test_alignment_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.alignment_qa",
        stage_class="AlignmentQaStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_dem_derivatives_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.dem_derivatives",
        stage_class="DemDerivativesStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_dem_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.dem",
        stage_class="DemStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_hypercube_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.hypercube",
        stage_class="HypercubeStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_objects_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.object_extract",
        stage_class="ObjectExtractStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_pca_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.pca_anomaly",
        stage_class="PcaAnomalyStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_s2_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.s2_indices",
        stage_class="S2IndicesStage",
        expected_category=ParityCategory.PARITY_CORRECTS,
    ),
    "test_sar_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.sar_rtc",
        stage_class="SarRtcStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
    "test_thermal_parity.py": ParityRegistryEntry(
        stage_module="app.pipeline.stages.thermal",
        stage_class="ThermalStage",
        expected_category=ParityCategory.PARITY_REPRODUCES,
    ),
}

CONTRACT_LEVEL_PARITY_TEST_FILES = {
    "test_reference_outputs_contract.py",
}


def load_stage_class(entry: ParityRegistryEntry) -> type[Stage]:
    module = import_module(entry.stage_module)
    stage_class = getattr(module, entry.stage_class)
    if not issubclass(stage_class, Stage):
        raise TypeError(f"{entry.stage_module}.{entry.stage_class} is not a Stage subclass.")
    return stage_class


def iter_registry_validation_errors(
    registry: dict[str, ParityRegistryEntry] | None = None,
) -> list[str]:
    active_registry = registry or PARITY_TEST_REGISTRY
    errors: list[str] = []
    for test_filename, entry in sorted(active_registry.items()):
        try:
            stage_class = load_stage_class(entry)
        except Exception as exc:  # pragma: no cover - exercised by collection failure path
            errors.append(f"{test_filename}: failed to import stage mapping: {exc}")
            continue

        actual_category = stage_class.parity_category
        if actual_category is not entry.expected_category:
            errors.append(
                f"{test_filename}: expected {entry.expected_category.value}, "
                f"found {getattr(actual_category, 'value', actual_category)!r} on "
                f"{entry.stage_module}.{entry.stage_class}"
            )
    return errors


def iter_missing_registry_entries(
    parity_files: set[str],
    *,
    registry: dict[str, ParityRegistryEntry] | None = None,
    contract_level_files: set[str] | None = None,
) -> list[str]:
    active_registry = registry or PARITY_TEST_REGISTRY
    allowed_contract_level_files = contract_level_files or CONTRACT_LEVEL_PARITY_TEST_FILES
    return sorted(
        filename
        for filename in parity_files
        if (
            filename.startswith("test_")
            and filename.endswith(".py")
            and filename not in active_registry
            and filename not in allowed_contract_level_files
        )
    )


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]) -> None:
    del session, config
    parity_root = Path(__file__).resolve().parent
    parity_files = {
        Path(str(item.fspath)).name
        for item in items
        if parity_root in Path(str(item.fspath)).resolve().parents
    }

    unknown_files = iter_missing_registry_entries(parity_files)
    errors = iter_registry_validation_errors()
    if unknown_files:
        errors.extend(f"{filename}: missing PARITY_TEST_REGISTRY entry" for filename in unknown_files)
    if errors:
        raise pytest.UsageError("Notebook parity registry validation failed:\n- " + "\n- ".join(errors))
