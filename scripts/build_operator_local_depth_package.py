from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from app.pipeline.depth.interpolation import (
    OPERATOR_CANDIDATES_SCHEMA,
    OPERATOR_METHOD_KIND,
    OPERATOR_PACKAGE_SCHEMA_VERSION,
    load_operator_interpolation_package,
)
from app.pipeline.depth.package import CHECKSUMS_NAME, MANIFEST_NAME


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("operator calibration config does not exist")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("operator calibration config is not readable JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("operator calibration config must be a JSON object")
    return payload


def _prepare_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_operator_local_depth_package(
    *,
    config_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = _load_json_object(config_path)
    _prepare_output_dir(output_dir)

    manifest = {
        "schema_version": OPERATOR_PACKAGE_SCHEMA_VERSION,
        "method_kind": OPERATOR_METHOD_KIND,
        "method_version": config.get("method_version"),
        "calibration_dataset_version": config.get("calibration_dataset_version"),
        "site_id": config.get("site_id"),
        "validation_status": config.get("validation_status", "provisional"),
        "allow_run_quality_warning": bool(config.get("allow_run_quality_warning", False)),
        "signal_name": config.get("signal_name"),
        "signal_units": config.get("signal_units", "unitless"),
        "default_signal_uncertainty": config.get("default_signal_uncertainty", 0.0),
        "warnings": config.get("warnings", []),
        "anchors": config.get("anchors"),
    }
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    raw_anchors = manifest.get("anchors")
    if not isinstance(raw_anchors, list) or len(raw_anchors) < 2:
        raise ValueError("config must contain at least two anchors")
    signal_values = sorted(float(anchor["signal_value"]) for anchor in raw_anchors)
    midpoint = (signal_values[0] + signal_values[-1]) / 2.0
    template = {
        "schema_version": OPERATOR_CANDIDATES_SCHEMA,
        "template_only": True,
        "candidates": [
            {
                "candidate_id": "replace-with-candidate-id",
                "signal_name": manifest.get("signal_name"),
                "signal_value": midpoint,
                "signal_uncertainty": manifest.get("default_signal_uncertainty", 0.0),
            }
        ],
    }
    template_path = output_dir / "candidate_input_template.json"
    template_path.write_text(
        json.dumps(template, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checksums_path = output_dir / CHECKSUMS_NAME
    checksums_path.write_text(
        "\n".join(
            [
                f"{_sha256(manifest_path)}  {MANIFEST_NAME}",
                f"{_sha256(template_path)}  candidate_input_template.json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    package = load_operator_interpolation_package(output_dir)
    return {
        "status": "package_created",
        "package_dir": str(package.root),
        "method_kind": package.method_kind,
        "method_version": package.method_version,
        "calibration_dataset_version": package.calibration_dataset_version,
        "site_id": package.site_id,
        "signal_name": package.signal_name,
        "signal_units": package.signal_units,
        "anchor_count": len(package.anchors),
        "validation_status": package.validation_status,
        "candidate_template": template_path.name,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a private operator-calibrated local depth package.",
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = build_operator_local_depth_package(
        config_path=args.config,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
