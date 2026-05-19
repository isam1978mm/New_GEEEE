from __future__ import annotations

import re
from pathlib import Path


def test_source_notebook_terms_are_confined_to_class_mapping_doc() -> None:
    mappings = _load_class_mapping_rows()
    _assert_complete_neutral_id_set(mappings)
    terms = [source_term for source_term, _neutral_id in mappings]
    assert terms

    scan_roots = [Path("app"), Path("tests"), Path("frontend")]
    offenders: list[str] = []
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            normalized_name = path.name.casefold()
            text = path.read_text(encoding="utf-8", errors="ignore").casefold()
            for term in terms:
                normalized_term = term.casefold()
                if normalized_term in normalized_name or normalized_term in text:
                    offenders.append(f"{path}: {term}")
    assert offenders == []


def _load_class_mapping_rows() -> list[tuple[str, str]]:
    mapping_path = Path("docs/CLASS_MAPPING.md")
    text = mapping_path.read_text(encoding="utf-8")
    return re.findall(r"\|\s*`([^`]+)`\s*\|\s*`(Class_[A-N])`\s*\|", text)


def _assert_complete_neutral_id_set(mappings: list[tuple[str, str]]) -> None:
    expected_ids = [f"Class_{chr(code)}" for code in range(ord("A"), ord("N") + 1)]
    actual_ids = [neutral_id for _source_term, neutral_id in mappings]

    assert actual_ids == expected_ids
    assert len(set(actual_ids)) == len(expected_ids)
