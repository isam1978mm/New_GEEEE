from __future__ import annotations

import re
from pathlib import Path


def test_source_notebook_terms_are_confined_to_class_mapping_doc() -> None:
    terms = _load_source_terms()
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
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in terms:
                if term in path.name or term in text:
                    offenders.append(f"{path}: {term}")
    assert offenders == []


def _load_source_terms() -> list[str]:
    mapping_path = Path("docs/CLASS_MAPPING.md")
    text = mapping_path.read_text(encoding="utf-8")
    return re.findall(r"\|\s*`([^`]+)`\s*\|\s*`Class_[A-N]`\s*\|", text)
