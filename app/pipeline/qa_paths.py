from __future__ import annotations

from pathlib import Path

NOTEBOOK_QA_DIRNAME = "QA"


def ensure_run_canonical_dir(run_dir: Path, dirname: str) -> Path:
    """Return a canonical top-level run directory, fixing casing when needed."""
    canonical_dir = run_dir / dirname

    children = run_dir.iterdir() if run_dir.exists() else ()
    for child in children:
        if child.is_dir() and child.name.casefold() == dirname.casefold():
            if child.name == dirname:
                return child
            tmp_dir = run_dir / f"__{dirname.casefold()}_casefix_tmp__"
            if tmp_dir.exists():
                raise FileExistsError(f"Temporary {dirname} case-fix directory already exists.")
            child.rename(tmp_dir)
            tmp_dir.rename(canonical_dir)
            return canonical_dir

    canonical_dir.mkdir(parents=True, exist_ok=True)
    return canonical_dir


def ensure_run_qa_dir(run_dir: Path) -> Path:
    """Return the canonical run QA directory, fixing lowercase casing if needed."""
    return ensure_run_canonical_dir(run_dir, NOTEBOOK_QA_DIRNAME)
