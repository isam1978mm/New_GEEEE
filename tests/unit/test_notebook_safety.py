from __future__ import annotations

import json
from pathlib import Path

from scripts.check_notebook_safety import collect_notebook_paths, main, scan_notebooks


CLASS_MAPPING = """# Class Mapping

| Source Notebook Identifier | Neutral ID |
|---|---|
| `Notebook_Source_Term_A` | `Class_A` |
| `Notebook_Source_Term_B` | `Class_B` |
"""


def test_notebook_safety_scanner_reports_required_violations(tmp_path: Path) -> None:
    mapping_path = tmp_path / "CLASS_MAPPING.md"
    mapping_path.write_text(CLASS_MAPPING, encoding="utf-8")

    notebook_path = tmp_path / "unsafe.ipynb"
    forbidden_ee_auth = "ee." + "Authenticate("
    write_notebook(
        notebook_path,
        cells=[
            code_cell(f"{forbidden_ee_auth})\n"),
            code_cell('service_key = "C:/Users/alice/keys/service-account-key.json"\n'),
            code_cell("lat = 29.12345\nlon = 35.67891\n"),
            code_cell("model = 'Notebook_Source_Term_A'\n"),
            code_cell("result = 1\n", outputs=[stream_output("29.12345, 35.67891")]),
        ],
    )

    violations = scan_notebooks([notebook_path], mapping_path)
    expected_ee_auth_message = "forbidden ee." + "Authenticate()"

    assert any(expected_ee_auth_message in item for item in violations)
    assert any("hardcoded absolute local path" in item for item in violations)
    assert any("service-account key path" in item for item in violations)
    assert any("coordinate-like content requires allowlist marker or metadata" in item for item in violations)
    assert any("forbidden classifier term `Notebook_Source_Term_A`" in item for item in violations)


def test_notebook_safety_scanner_accepts_allowlisted_coordinate_examples_with_reason(tmp_path: Path) -> None:
    mapping_path = tmp_path / "CLASS_MAPPING.md"
    mapping_path.write_text(CLASS_MAPPING, encoding="utf-8")

    source_allowlisted = tmp_path / "source_allowlisted.ipynb"
    write_notebook(
        source_allowlisted,
        cells=[
            code_cell(
                "# parity: allow-coord Example coordinate pair kept for explanatory migration notes\n"
                "lat = 29.12345\n"
                "lon = 35.67891\n"
            )
        ],
    )

    metadata_allowlisted = tmp_path / "metadata_allowlisted.ipynb"
    write_notebook(
        metadata_allowlisted,
        cells=[
            code_cell(
                "print('roi sample')\n",
                outputs=[stream_output("29.12345, 35.67891")],
                metadata={
                    "parity_allow_coord": True,
                    "parity_allow_coord_reason": "Recorded example output for notebook migration notes.",
                },
            )
        ],
    )

    parity_corrects_notebook = tmp_path / "iron_swir_note.ipynb"
    write_notebook(
        parity_corrects_notebook,
        cells=[
            markdown_cell(
                "IRON_SWIR is PARITY_CORRECTS and uses the corrected denominator B11+B12 in the app."
            )
        ],
    )

    violations = scan_notebooks(
        [source_allowlisted, metadata_allowlisted, parity_corrects_notebook],
        mapping_path,
    )

    assert violations == []


def test_notebook_safety_scanner_requires_allowlist_reason(tmp_path: Path) -> None:
    mapping_path = tmp_path / "CLASS_MAPPING.md"
    mapping_path.write_text(CLASS_MAPPING, encoding="utf-8")

    notebook_path = tmp_path / "missing_reason.ipynb"
    write_notebook(
        notebook_path,
        cells=[code_cell("# parity: allow-coord\nlat = 29.12345\nlon = 35.67891\n")],
    )

    violations = scan_notebooks([notebook_path], mapping_path)

    assert any("coordinate allowlist requires a non-empty reason string" in item for item in violations)


def test_notebook_safety_scanner_rejects_markdown_ee_authenticate(tmp_path: Path) -> None:
    mapping_path = tmp_path / "CLASS_MAPPING.md"
    mapping_path.write_text(CLASS_MAPPING, encoding="utf-8")

    notebook_path = tmp_path / "markdown_auth.ipynb"
    forbidden_ee_auth = "ee." + "Authenticate("
    write_notebook(
        notebook_path,
        cells=[markdown_cell(f"Migration note still shows {forbidden_ee_auth}) as an example.")],
    )

    violations = scan_notebooks([notebook_path], mapping_path)
    expected_ee_auth_message = "forbidden ee." + "Authenticate()"

    assert any(expected_ee_auth_message in item for item in violations)


def test_notebook_safety_scanner_rejects_markdown_absolute_paths(tmp_path: Path) -> None:
    mapping_path = tmp_path / "CLASS_MAPPING.md"
    mapping_path.write_text(CLASS_MAPPING, encoding="utf-8")

    notebook_path = tmp_path / "markdown_path.ipynb"
    write_notebook(
        notebook_path,
        cells=[
            markdown_cell(
                'Legacy note: credentials were once stored at "C:/Users/alice/keys/service-account-key.json".'
            )
        ],
    )

    violations = scan_notebooks([notebook_path], mapping_path)

    assert any("hardcoded absolute local path" in item for item in violations)
    assert any("service-account key path" in item for item in violations)


def test_notebook_safety_main_scans_default_notebooks_directory(tmp_path: Path, monkeypatch) -> None:
    notebooks_dir = tmp_path / "notebooks"
    notebooks_dir.mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "CLASS_MAPPING.md").write_text(CLASS_MAPPING, encoding="utf-8")

    write_notebook(
        notebooks_dir / "safe.ipynb",
        cells=[
            code_cell(
                "# parity: allow-coord Example coordinate pair for notebook migration docs\n"
                "lat = 29.12345\n"
                "lon = 35.67891\n"
            )
        ],
    )

    monkeypatch.chdir(tmp_path)

    assert main([]) == 0


def test_notebook_safety_real_repo_notebooks_are_clean() -> None:
    violations = scan_notebooks(
        collect_notebook_paths([Path("notebooks")]),
        Path("docs/CLASS_MAPPING.md"),
    )

    assert violations == []


def write_notebook(path: Path, *, cells: list[dict[str, object]]) -> None:
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": cells,
    }
    path.write_text(json.dumps(notebook), encoding="utf-8")


def code_cell(
    source: str,
    *,
    outputs: list[dict[str, object]] | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata or {},
        "outputs": outputs or [],
        "source": [source],
    }


def markdown_cell(source: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [source],
    }


def stream_output(text: str) -> dict[str, object]:
    return {"output_type": "stream", "name": "stdout", "text": [text]}
