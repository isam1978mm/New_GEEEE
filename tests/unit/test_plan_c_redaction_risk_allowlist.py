from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = REPO_ROOT / "tests" / "fixtures" / "plan_c_c1_redaction_risk_allowlist.json"

SCAN_ROOTS = ("docs", "app", "scripts")
SCAN_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".ps1"}

RISK_PATTERNS = {
    "possible_coordinate_pair": re.compile(r"[-+]?\d{1,2}\.\d{4,}\s*,\s*[-+]?\d{1,3}\.\d{4,}"),
    "possible_windows_private_path": re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
    "possible_absolute_private_root": re.compile(r"C:\\Dev\\New_GEE_PRIVATE", re.IGNORECASE),
}


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _scan_current_risks() -> dict[str, dict[str, int]]:
    observed: dict[str, dict[str, int]] = {}

    for root_name in SCAN_ROOTS:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue

            text = _read_text(path)
            counts = {
                name: len(pattern.findall(text))
                for name, pattern in RISK_PATTERNS.items()
            }
            counts = {name: count for name, count in counts.items() if count > 0}
            if counts:
                observed[_rel(path)] = dict(sorted(counts.items()))

    return observed


def _load_allowlist() -> dict[str, dict[str, int]]:
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    assert payload["schema"] == "plan_c_c1_redaction_risk_allowlist_v1"
    return payload["allowed_risks"]


def test_plan_c_c1_no_new_unapproved_redaction_risk_files_or_types() -> None:
    allowed = _load_allowlist()
    observed = _scan_current_risks()

    new_files = sorted(set(observed) - set(allowed))

    new_types: dict[str, list[str]] = {}
    for path, current_counts in observed.items():
        approved_counts = allowed.get(path, {})
        added_types = sorted(set(current_counts) - set(approved_counts))
        if added_types:
            new_types[path] = added_types

    assert not new_files, (
        "New unapproved docs/app/scripts redaction-risk files were found. "
        "Either remove/redact the risky content or update the C1 allowlist with a documented reason: "
        f"{new_files}"
    )
    assert not new_types, (
        "Existing docs/app/scripts files introduced new redaction-risk types. "
        "Either remove/redact the risky content or update the C1 allowlist with a documented reason: "
        f"{new_types}"
    )


def test_plan_c_c1_no_increased_redaction_risk_counts() -> None:
    allowed = _load_allowlist()
    observed = _scan_current_risks()

    increased: dict[str, dict[str, dict[str, int]]] = {}

    for path, current_counts in observed.items():
        approved_counts = allowed.get(path, {})
        for risk_name, current_count in current_counts.items():
            approved_count = int(approved_counts.get(risk_name, 0))
            if current_count > approved_count:
                increased.setdefault(path, {})[risk_name] = {
                    "approved": approved_count,
                    "current": current_count,
                }

    assert not increased, (
        "Docs/app/scripts redaction-risk counts increased above the approved C1 baseline. "
        "Either remove/redact the added risky content or update the C1 allowlist with a documented reason: "
        f"{increased}"
    )


def test_plan_c_c1_allowlist_scope_excludes_tests_as_fixtures() -> None:
    allowed = _load_allowlist()

    assert allowed
    assert all(
        path.startswith(("docs/", "app/", "scripts/")) for path in allowed
    )
    assert all(not path.startswith("tests/") for path in allowed)
