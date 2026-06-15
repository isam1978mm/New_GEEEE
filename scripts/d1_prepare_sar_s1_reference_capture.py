from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from d1_sar_s1_recovery_contract import REQUIRED_OUTPUTS

TIF_DIR = "GEOTIFF_RADAR_BANDS"
NPY_DIR = "NPY_RADAR_BANDS"
STACK_DIR = "NPY_STACKS"
STACK_NAME = "S1_FILTERED_LAYERS_STACK_640.npy"

STATUS_READY = "ready_to_copy"
STATUS_MISSING = "missing_source_output"


class D1SarS1ReferenceCaptureError(ValueError):
    pass


def target_relative_path(name: str) -> Path:
    if name == STACK_NAME:
        return Path(STACK_DIR) / name
    if name.endswith(".tif"):
        return Path(TIF_DIR) / name
    if name.endswith(".npy"):
        return Path(NPY_DIR) / name
    raise D1SarS1ReferenceCaptureError(f"unsupported required output type: {name}")


def find_by_name(root: Path, filename: str) -> Path | None:
    direct = root / filename
    if direct.is_file():
        return direct
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    return matches[0] if matches else None


def build_capture_plan(*, source_dir: str | Path, bundle_root: str | Path) -> dict[str, Any]:
    source_root = Path(source_dir)
    bundle = Path(bundle_root)
    if not source_root.is_dir():
        raise D1SarS1ReferenceCaptureError("source directory is missing")
    if not bundle.is_dir():
        raise D1SarS1ReferenceCaptureError("bundle root is missing")

    artifacts_sar = bundle / "artifacts" / "sar"
    items: list[dict[str, Any]] = []
    for name in REQUIRED_OUTPUTS:
        source_path = find_by_name(source_root, name)
        rel_target = target_relative_path(name)
        items.append(
            {
                "output_name": name,
                "source_present": source_path is not None,
                "target_relative_path": str(Path("artifacts") / "sar" / rel_target),
                "status": STATUS_READY if source_path is not None else STATUS_MISSING,
            }
        )
    missing = [item for item in items if item["status"] == STATUS_MISSING]
    return {
        "schema_version": "d1_sar_s1_reference_capture_plan_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "ready" if not missing else "missing_source_outputs",
        "required_output_count": len(items),
        "ready_to_copy_count": sum(item["status"] == STATUS_READY for item in items),
        "missing_source_count": len(missing),
        "items": items,
        "target_root_relative": str(Path("artifacts") / "sar"),
        "notes": "Reference capture helper only. It copies required S1 filtered notebook outputs into the local D1 reference bundle; it does not generate outputs or prove value parity.",
    }


def copy_ready_outputs(*, source_dir: str | Path, bundle_root: str | Path, dry_run: bool) -> dict[str, Any]:
    source_root = Path(source_dir)
    bundle = Path(bundle_root)
    plan = build_capture_plan(source_dir=source_root, bundle_root=bundle)
    copied: list[dict[str, Any]] = []
    if plan["status"] == "missing_source_outputs":
        return {**plan, "copied_count": 0, "dry_run": dry_run, "copied_outputs": copied}

    for item in plan["items"]:
        name = str(item["output_name"])
        source_path = find_by_name(source_root, name)
        if source_path is None:
            continue
        target = bundle / item["target_relative_path"]
        copied.append({"output_name": name, "target_relative_path": item["target_relative_path"]})
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
    return {**plan, "copied_count": len(copied), "dry_run": dry_run, "copied_outputs": copied}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or copy D1 SAR/S1 filtered reference outputs into the local reference bundle.")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--report")
    parser.add_argument("--copy", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = copy_ready_outputs(source_dir=args.source_dir, bundle_root=args.bundle_root, dry_run=not args.copy)
    except D1SarS1ReferenceCaptureError as exc:
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
        print(json.dumps({"ok": result["status"] == "ready", **result}, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"required_output_count: {result['required_output_count']}")
        print(f"ready_to_copy_count: {result['ready_to_copy_count']}")
        print(f"missing_source_count: {result['missing_source_count']}")
        print(f"copied_count: {result['copied_count']}")
        print(f"dry_run: {result['dry_run']}")
        print("note: reference capture helper only; not SAR value parity")
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
