from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_PER_BAND_OUTPUTS = (
    "S1_ASC_VV_Filtered_640.tif",
    "S1_ASC_VH_Filtered_640.tif",
    "S1_DESC_VV_Filtered_640.tif",
    "S1_DESC_VH_Filtered_640.tif",
    "S1_ASC_VV_Filtered_640.npy",
    "S1_ASC_VH_Filtered_640.npy",
    "S1_DESC_VV_Filtered_640.npy",
    "S1_DESC_VH_Filtered_640.npy",
)

REQUIRED_STACK_OUTPUT = "S1_FILTERED_LAYERS_STACK_640.npy"
REQUIRED_OUTPUTS = REQUIRED_PER_BAND_OUTPUTS + (REQUIRED_STACK_OUTPUT,)

NON_EQUIVALENT_APP_OUTPUT_NAMES = (
    "VV_dB.tif",
    "VH_dB.tif",
    "logRatio_dB.tif",
    "incidence.tif",
    "RADAR_VV_dB_640_app.tif",
    "RADAR_VH_dB_640_app.tif",
    "RADAR_logRatio_dB_640_app.tif",
    "RADAR_angle_640_app.tif",
    "RADAR_STACK_HWC_640_app.npy",
    "radar_db_support_stack.npy",
    "radar_linear_support_stack.npy",
)

STATUS_READY_FOR_VALUE_PARITY = "ready_for_value_parity"
STATUS_MISSING_APP = "missing_app_output"
STATUS_MISSING_REFERENCE = "missing_reference_output"
STATUS_MISSING_BOTH = "missing_both"
OVERALL_READY = "contract_ready"
OVERALL_BLOCKED = "blocked_missing_required_outputs"


class D1SarS1RecoveryContractError(ValueError):
    pass


def find_by_name(root: Path, filename: str) -> Path | None:
    direct = root / filename
    if direct.is_file():
        return direct
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    return matches[0] if matches else None


def inspect_output(name: str, *, app_root: Path, reference_root: Path) -> dict[str, Any]:
    app_present = find_by_name(app_root, name) is not None
    reference_present = find_by_name(reference_root, name) is not None
    if app_present and reference_present:
        status = STATUS_READY_FOR_VALUE_PARITY
    elif app_present:
        status = STATUS_MISSING_REFERENCE
    elif reference_present:
        status = STATUS_MISSING_APP
    else:
        status = STATUS_MISSING_BOTH
    return {
        "output_name": name,
        "app_present": app_present,
        "reference_present": reference_present,
        "status": status,
    }


def inspect_non_equivalent_outputs(app_root: Path) -> list[dict[str, Any]]:
    return [
        {"output_name": name, "app_present": find_by_name(app_root, name) is not None, "equivalent_to_required_s1_filtered_output": False}
        for name in NON_EQUIVALENT_APP_OUTPUT_NAMES
    ]


def build_d1_sar_s1_recovery_contract(*, app_output_dir: str | Path, reference_sar_root: str | Path) -> dict[str, Any]:
    app_root = Path(app_output_dir)
    reference_root = Path(reference_sar_root)
    if not app_root.is_dir():
        raise D1SarS1RecoveryContractError("app output directory is missing")
    if not reference_root.is_dir():
        raise D1SarS1RecoveryContractError("reference SAR root is missing")

    required = [inspect_output(name, app_root=app_root, reference_root=reference_root) for name in REQUIRED_OUTPUTS]
    missing = [item for item in required if item["status"] != STATUS_READY_FOR_VALUE_PARITY]
    overall = OVERALL_READY if not missing else OVERALL_BLOCKED
    return {
        "schema_version": "d1_sar_s1_recovery_contract_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "overall_status": overall,
        "required_output_count": len(required),
        "ready_for_value_parity_count": sum(item["status"] == STATUS_READY_FOR_VALUE_PARITY for item in required),
        "missing_required_count": len(missing),
        "required_outputs": required,
        "non_equivalent_app_outputs": inspect_non_equivalent_outputs(app_root),
        "implementation_allowed": False,
        "value_parity_proven": False,
        "notes": "Recovery contract inventory only. Final RTC/radar support outputs must not be treated as equivalent to the notebook S1 ASC/DESC filtered support outputs.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect D1 SAR/S1 recovery contract readiness without reading raster contents.")
    parser.add_argument("--app-output-dir", required=True)
    parser.add_argument("--reference-sar-root", required=True)
    parser.add_argument("--report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = build_d1_sar_s1_recovery_contract(app_output_dir=args.app_output_dir, reference_sar_root=args.reference_sar_root)
    except D1SarS1RecoveryContractError as exc:
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
        print(json.dumps({"ok": result["overall_status"] == OVERALL_READY, **result}, indent=2, sort_keys=True))
    else:
        print(f"overall_status: {result['overall_status']}")
        print(f"required_output_count: {result['required_output_count']}")
        print(f"ready_for_value_parity_count: {result['ready_for_value_parity_count']}")
        print(f"missing_required_count: {result['missing_required_count']}")
        print("implementation_allowed: False")
        print("value_parity_proven: False")
        print("note: SAR/S1 recovery contract only; not SAR value parity")
    return 0 if result["overall_status"] == OVERALL_READY else 2


if __name__ == "__main__":
    sys.exit(main())
