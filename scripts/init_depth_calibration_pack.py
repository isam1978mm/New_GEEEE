"""Create an empty private depth-calibration pack outside the repository.

The script copies repository-safe templates only. It does not create records,
write coordinates, calculate depth, train a model, or change app outputs.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "templates" / "depth_calibration"
PRIVATE_ROOT = REPO_ROOT.parent / f"{REPO_ROOT.name}_PRIVATE"
DEFAULT_DESTINATION = PRIVATE_ROOT / "DEPTH_CALIBRATION" / "dataset_v001"
REQUIRED_FILES = (
    "calibration_records.csv",
    "calibration_manifest.json",
    "feature_manifest.json",
    "source_index.csv",
    "exclusions.csv",
    "DATASET_CARD.md",
    "README.md",
)


class PackInitError(ValueError):
    """Raised when an empty private pack cannot be initialized safely."""


def initialize_pack(destination: Path, *, template_dir: Path = TEMPLATE_DIR) -> dict[str, object]:
    destination = Path(destination)
    template_dir = Path(template_dir)
    _require_outside_repo(destination, "destination")
    if not template_dir.is_dir():
        raise PackInitError(f"template directory does not exist: {template_dir}")

    missing = [name for name in REQUIRED_FILES if not (template_dir / name).is_file()]
    if missing:
        raise PackInitError(f"template files are missing: {', '.join(missing)}")

    if destination.exists() and any(destination.iterdir()):
        raise PackInitError("destination exists and is not empty")
    destination.mkdir(parents=True, exist_ok=True)

    for name in REQUIRED_FILES:
        shutil.copyfile(template_dir / name, destination / name)

    return {
        "status": "empty_private_pack_initialized",
        "file_count": len(REQUIRED_FILES),
        "files": list(REQUIRED_FILES),
        "destination_outside_repository": True,
        "real_records_written": False,
        "depth_model_started": False,
    }


def _require_outside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise PackInitError(f"{label} must be outside the repository")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy the empty depth-calibration template pack outside Git.")
    parser.add_argument("--destination", default=str(DEFAULT_DESTINATION))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = initialize_pack(Path(args.destination))
    except (OSError, PackInitError) as exc:
        print(json.dumps({"status": "initialization_failed", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
