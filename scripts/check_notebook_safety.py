from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence


FORBIDDEN_EE_AUTH = "ee.Authenticate("
ALLOW_COORD_SOURCE_RE = re.compile(r"#\s*parity:\s*allow-coord\b(?::|\s+-\s+|\s+)?(.*)$", re.IGNORECASE)
ALLOW_COORD_REASON_RE = re.compile(r"#\s*parity:\s*allow-coord-reason\b(?::|\s+)(.+)$", re.IGNORECASE)
ABSOLUTE_LOCAL_PATH_RE = re.compile(
    r"(?i)(?:[A-Z]:[\\/][^\s\"']+|/(?:Users|home|content|mnt|private|tmp|var|opt|srv)[^\s\"']*)"
)
SERVICE_ACCOUNT_KEY_PATH_RE = re.compile(
    r"(?i)(?:[A-Z]:[\\/][^\s\"']*|/(?:Users|home|content|mnt|private|tmp|var|opt|srv)[^\s\"']*)"
    r"(?:service[_ -]?account|credentials?|earthengine|gee|key)[^\s\"']*\.json"
)
COORDINATE_PATTERNS = (
    re.compile(r"(?i)\b(?:lat|latitude)\s*[:=]\s*[-+]?\d{1,2}\.\d+\b"),
    re.compile(r"(?i)\b(?:lon|lng|longitude)\s*[:=]\s*[-+]?\d{1,3}\.\d+\b"),
    re.compile(r"(?<!\d)[-+]?\d{1,2}\.\d{3,}\s*,\s*[-+]?\d{1,3}\.\d{3,}(?!\d)"),
    re.compile(r"\[\s*[-+]?\d{1,3}\.\d+\s*,\s*[-+]?\d{1,3}\.\d+\s*\]"),
)
CLASS_MAPPING_ROW_RE = re.compile(r"\|\s*`([^`]+)`\s*\|\s*`Class_[A-N]`\s*\|")


def load_forbidden_classifier_terms(mapping_path: Path) -> list[str]:
    if not mapping_path.exists():
        return []
    text = mapping_path.read_text(encoding="utf-8")
    return [term for term in CLASS_MAPPING_ROW_RE.findall(text)]


def collect_notebook_paths(inputs: Sequence[Path]) -> list[Path]:
    paths: list[Path] = []
    for candidate in inputs:
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob("*.ipynb")))
        elif candidate.suffix == ".ipynb" and candidate.exists():
            paths.append(candidate)
    return paths


def scan_notebooks(notebook_paths: Sequence[Path], mapping_path: Path) -> list[str]:
    forbidden_terms = load_forbidden_classifier_terms(mapping_path)
    violations: list[str] = []
    for notebook_path in notebook_paths:
        violations.extend(scan_notebook(notebook_path, forbidden_terms))
    return sorted(violations)


def scan_notebook(notebook_path: Path, forbidden_terms: Sequence[str]) -> list[str]:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        cell_type = cell.get("cell_type", "")
        source_text = join_lines(cell.get("source", []))
        source_context = f"{notebook_path}:cell-{index}:source"
        output_text = join_output_texts(cell.get("outputs", []))
        output_context = f"{notebook_path}:cell-{index}:output"

        if cell_type == "code":
            if FORBIDDEN_EE_AUTH in source_text:
                violations.append(f"{source_context}: forbidden ee.Authenticate()")
            if FORBIDDEN_EE_AUTH in output_text:
                violations.append(f"{output_context}: forbidden ee.Authenticate()")

            violations.extend(scan_text_for_paths(source_text, source_context))
            violations.extend(scan_text_for_paths(output_text, output_context))

            if contains_coordinate_like_content(source_text) or contains_coordinate_like_content(output_text):
                allowlisted, reason = get_coordinate_allowlist(cell)
                if not allowlisted:
                    violations.append(
                        f"{notebook_path}:cell-{index}: coordinate-like content requires allowlist marker or metadata"
                    )
                elif not reason:
                    violations.append(
                        f"{notebook_path}:cell-{index}: coordinate allowlist requires a non-empty reason string"
                    )

        violations.extend(scan_forbidden_terms(source_text, source_context, forbidden_terms))
        violations.extend(scan_forbidden_terms(output_text, output_context, forbidden_terms))
    return violations


def scan_text_for_paths(text: str, context: str) -> list[str]:
    violations: list[str] = []
    if ABSOLUTE_LOCAL_PATH_RE.search(text):
        violations.append(f"{context}: hardcoded absolute local path")
    if SERVICE_ACCOUNT_KEY_PATH_RE.search(text):
        violations.append(f"{context}: service-account key path")
    return violations


def scan_forbidden_terms(text: str, context: str, forbidden_terms: Sequence[str]) -> list[str]:
    lowered = text.casefold()
    violations: list[str] = []
    for term in forbidden_terms:
        if term.casefold() in lowered:
            violations.append(f"{context}: forbidden classifier term `{term}`")
    return violations


def contains_coordinate_like_content(text: str) -> bool:
    return any(pattern.search(text) for pattern in COORDINATE_PATTERNS)


def get_coordinate_allowlist(cell: dict[str, Any]) -> tuple[bool, str]:
    metadata = cell.get("metadata", {})
    if metadata.get("parity_allow_coord") is True:
        return True, str(metadata.get("parity_allow_coord_reason", "")).strip()

    source_text = join_lines(cell.get("source", []))
    for line in source_text.splitlines():
        marker_match = ALLOW_COORD_SOURCE_RE.search(line)
        if marker_match:
            inline_reason = marker_match.group(1).strip()
            if inline_reason:
                return True, inline_reason
            continue
        reason_match = ALLOW_COORD_REASON_RE.search(line)
        if reason_match:
            return True, reason_match.group(1).strip()
    if "# parity: allow-coord" in source_text:
        return True, ""
    return False, ""


def join_lines(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(join_lines(item) for item in value)
    return ""


def join_output_texts(outputs: Iterable[dict[str, Any]]) -> str:
    parts: list[str] = []
    for output in outputs:
        for key in ("text", "ename", "evalue"):
            if key in output:
                parts.append(join_lines(output[key]))
        data = output.get("data")
        if isinstance(data, dict):
            parts.append(flatten_text_values(data.values()))
    return "\n".join(part for part in parts if part)


def flatten_text_values(values: Iterable[Any]) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.append("".join(flatten_text_values([item]) for item in value))
        elif isinstance(value, dict):
            parts.append(flatten_text_values(value.values()))
        else:
            parts.append(str(value))
    return "\n".join(part for part in parts if part)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=["notebooks"])
    parser.add_argument("--class-mapping", default="docs/CLASS_MAPPING.md")
    args = parser.parse_args(argv)

    notebook_paths = collect_notebook_paths([Path(path) for path in args.paths])
    violations = scan_notebooks(notebook_paths, Path(args.class_mapping))
    if violations:
        for violation in violations:
            print(violation)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
