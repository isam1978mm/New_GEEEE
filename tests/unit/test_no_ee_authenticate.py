from __future__ import annotations

from pathlib import Path

from scripts.check_no_ee_authenticate import find_violations


def test_app_and_tests_do_not_reference_ee_authenticate() -> None:
    violations = find_violations(Path("app"), Path("tests"))
    assert violations == []
