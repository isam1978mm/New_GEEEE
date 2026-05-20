from __future__ import annotations

from app.pipeline._base import ParityCategory
from tests.notebook_parity.conftest import (
    CONTRACT_LEVEL_PARITY_TEST_FILES,
    PARITY_TEST_REGISTRY,
    iter_missing_registry_entries,
    iter_registry_validation_errors,
)


def test_notebook_parity_registry_matches_stage_metadata() -> None:
    assert iter_registry_validation_errors() == []


def test_notebook_parity_registry_covers_reproduce_and_corrects() -> None:
    categories = {entry.expected_category for entry in PARITY_TEST_REGISTRY.values()}

    assert ParityCategory.PARITY_REPRODUCES in categories
    assert ParityCategory.PARITY_CORRECTS in categories
    assert ParityCategory.PARITY_REPLACES not in categories


def test_parity_replaces_exists_as_metadata_category_but_not_notebook_fixture_category() -> None:
    all_categories = {member for member in ParityCategory}

    assert ParityCategory.PARITY_REPLACES in all_categories


def test_contract_level_parity_files_do_not_require_stage_registry_entries() -> None:
    missing = iter_missing_registry_entries(set(CONTRACT_LEVEL_PARITY_TEST_FILES))

    assert missing == []


def test_unknown_notebook_parity_files_still_require_registry_entries() -> None:
    missing = iter_missing_registry_entries({"test_unknown_parity.py"})

    assert missing == ["test_unknown_parity.py"]
