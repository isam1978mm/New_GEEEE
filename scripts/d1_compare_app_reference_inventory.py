from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {
    "bundle_id",
    "notebook_name",
    "notebook_version",
    "collected_at",
    "operator",
    "source_run_id",
    "artifact_families",
    "local_artifact_paths",
    "notes",
}


class InventoryCompareError(ValueError):
    pass


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InventoryCompareError(f"manifest not found: {path.as_posix()}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InventoryCompareError("manifest must be a JSON object")
    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        raise InventoryCompareError(f"manifest missing keys: {missing}")
    paths = data.get("local_artifact_paths")
    families = data.get("artifact_families")
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise InventoryCompareError("manifest local_artifact_paths must be a list of strings")
    if not isinstance(families, list) or not all(isinstance(item, str) for item in families):
        raise InventoryCompareError("manifest artifact_families must be a list of strings")
    return data


def _family_from_reference_path(path_text: str) -> str:
    parts = Path(path_text.replace("\\", "/")).parts
    try:
        idx = parts.index("artifacts")
    except ValueError:
        return "unknown"
    if idx + 1 >= len(parts):
        return "unknown"
    return parts[idx + 1]


def _scan_app_files(app_output_dir: Path) -> list[Path]:
    if not app_output_dir.is_dir():
        raise InventoryCompareError(f"app output dir not found: {app_output_dir.as_posix()}")
    return sorted(path for path in app_output_dir.rglob("*") if path.is_file())


def _family_hint_from_app_path(path: Path) -> str:
    text = path.as_posix().lower()
    if "dem_geo8" in text or "/dem" in text:
        return "dem"
    if "radar" in text or "/sar" in text:
        return "sar"
    if "qa" in text or "report" in text or "manifest" in text:
        return "report"
    if "ai_ready" in text or "npy_stacks" in text or "/stacks" in text or "full_job" in text:
        return "private_semantic"
    return "unknown"


def compare_inventory(reference_manifest: Path, app_output_dir: Path) -> dict[str, Any]:
    manifest = _load_manifest(reference_manifest)
    reference_paths = [str(item) for item in manifest["local_artifact_paths"]]
    app_files = _scan_app_files(app_output_dir)

    ref_by_name: dict[str, list[str]] = defaultdict(list)
    ref_family_counts: Counter[str] = Counter()
    for path_text in reference_paths:
        name = Path(path_text.replace("\\", "/")).name
        ref_by_name[name].append(path_text)
        ref_family_counts[_family_from_reference_path(path_text)] += 1

    app_names = {path.name for path in app_files}
    app_family_counts: Counter[str] = Counter(_family_hint_from_app_path(path) for path in app_files)

    matched_names = sorted(name for name in ref_by_name if name in app_names)
    missing_names = sorted(name for name in ref_by_name if name not in app_names)
    extra_app_count = sum(1 for path in app_files if path.name not in ref_by_name)

    family_summaries = []
    for family in sorted(set(ref_family_counts) | set(app_family_counts)):
        family_summaries.append(
            {
                "family": family,
                "reference_count": ref_family_counts.get(family, 0),
                "app_hint_count": app_family_counts.get(family, 0),
            }
        )

    status = "passed" if not missing_names else "incomplete"
    return {
        "schema_version": "d1_app_reference_inventory_compare_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "bundle_id": manifest.get("bundle_id"),
        "source_run_id": manifest.get("source_run_id"),
        "status": status,
        "reference_artifact_count": len(reference_paths),
        "app_file_count": len(app_files),
        "matched_reference_name_count": len(matched_names),
        "missing_reference_name_count": len(missing_names),
        "extra_app_file_count": extra_app_count,
        "family_summaries": family_summaries,
        "missing_reference_names": missing_names[:200],
        "notes": "Inventory-only comparison. It checks file-name presence and family counts without reading artifact contents. Passing this report is not notebook-value parity.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare a D1 local reference manifest against an app output folder by safe inventory only.")
    parser.add_argument("--reference-manifest", required=True)
    parser.add_argument("--app-output-dir", required=True)
    parser.add_argument("--report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = compare_inventory(Path(args.reference_manifest), Path(args.app_output_dir))
    except (InventoryCompareError, json.JSONDecodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}")
        return 1

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"reference_artifact_count: {result['reference_artifact_count']}")
        print(f"app_file_count: {result['app_file_count']}")
        print(f"matched_reference_name_count: {result['matched_reference_name_count']}")
        print(f"missing_reference_name_count: {result['missing_reference_name_count']}")
        print("note: inventory-only; not notebook-value parity")
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
