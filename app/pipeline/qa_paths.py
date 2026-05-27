from __future__ import annotations

from pathlib import Path

NOTEBOOK_QA_DIRNAME = "QA"


def ensure_run_qa_dir(run_dir: Path) -> Path:
    """Return the canonical run QA directory, fixing lowercase casing if needed."""
    qa_dir = run_dir / NOTEBOOK_QA_DIRNAME

    children = run_dir.iterdir() if run_dir.exists() else ()
    for child in children:
        if child.is_dir() and child.name.casefold() == NOTEBOOK_QA_DIRNAME.casefold():
            if child.name == NOTEBOOK_QA_DIRNAME:
                return child
            tmp_dir = run_dir / "__qa_casefix_tmp__"
            if tmp_dir.exists():
                raise FileExistsError("Temporary QA case-fix directory already exists.")
            child.rename(tmp_dir)
            tmp_dir.rename(qa_dir)
            return qa_dir

    qa_dir.mkdir(parents=True, exist_ok=True)
    return qa_dir
