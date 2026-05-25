from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from base64 import urlsafe_b64encode
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import Settings


MANIFEST_PATH = Path("tests/notebook_parity/fixtures/reference_run_v1/MANIFEST.json")
PATH_MAP_PATH = Path("tests/notebook_parity/fixtures/reference_run_v1/PATH_MAP.local.json")
NOTEBOOK_PATH = Path("notebooks/new.ipynb")
REQUIRES_CAPTURE = "REQUIRES_OPERATOR_CAPTURE"
IRON_SWIR_OPTION_A_RULE = "option_a_corrected_app_reference"


def main() -> int:
    settings = Settings()
    bundle_dir = settings.notebook_reference_bundle_dir
    if bundle_dir is None:
        print(
            "ERROR: NOTEBOOK_REFERENCE_BUNDLE_DIR is unset. "
            "Set it to the operator-supplied notebook reference bundle before generating MANIFEST.json.",
            file=sys.stderr,
        )
        return 2
    if not bundle_dir.is_dir():
        print(
            "ERROR: NOTEBOOK_REFERENCE_BUNDLE_DIR is configured but is not a readable directory.",
            file=sys.stderr,
        )
        return 2

    manifest, path_map = build_manifest(bundle_dir)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PATH_MAP_PATH.write_text(json.dumps(path_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote MANIFEST.json with {len(manifest['files'])} files.")
    return 0


def build_manifest(bundle_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    files, path_map = manifest_files(bundle_dir)
    manifest = {
        "schema_version": 1,
        "reference_run_id": "reference_run_v1",
        "notebook_commit_sha": git_head_sha(),
        "notebook_file_sha256": sha256_file(NOTEBOOK_PATH) if NOTEBOOK_PATH.is_file() else REQUIRES_CAPTURE,
        "capture_date_iso": datetime.now(UTC).date().isoformat(),
        "canonical_roi_label": "canonical_roi_v1",
        "grid_identity": extract_grid_identity(bundle_dir),
        "files": files,
        "comparison_rules": {
            "IRON_SWIR.tif": IRON_SWIR_OPTION_A_RULE,
        },
    }
    return manifest, path_map


def manifest_files(bundle_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    path_entries: dict[str, str] = {}
    for index, path in enumerate(sorted(item for item in bundle_dir.rglob("*") if item.is_file()), start=1):
        artifact_id = f"file_{index:06d}"
        relative_path = path.relative_to(bundle_dir).as_posix()
        path_entries[artifact_id] = encode_path(relative_path)
        entries.append(
            {
                "artifact_id": artifact_id,
                "redacted_path": f"redacted/{artifact_id}{safe_suffix(path)}",
                "artifact_name": safe_artifact_name(path.name),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return entries, {"schema_version": 1, "paths": path_entries}


def safe_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".json", ".csv", ".txt", ".tif", ".npy"}:
        return f"_{suffix.removeprefix('.')}"
    return "_bin"


def encode_path(relative_path: str) -> str:
    return urlsafe_b64encode(relative_path.encode("utf-8")).decode("ascii")


def safe_artifact_name(filename: str) -> str:
    lower = filename.lower()
    unsafe_tokens = ("lat", "lon", "focus_mask_17m", "bounds", "crstransform")
    if any(token in lower for token in unsafe_tokens):
        return "redacted_artifact"
    if any(char.isdigit() for char in filename):
        return "redacted_artifact"
    return filename


def extract_grid_identity(bundle_dir: Path) -> dict[str, Any]:
    payload = first_json_payload(bundle_dir, ("QA_RADAR_META*.json", "grid_manifest.json"))
    crs = first_value(payload, "crs", "CRS", "projection")
    epsg = epsg_from_crs(crs) or first_value(payload, "epsg", "EPSG")
    return {
        "crs": crs or REQUIRES_CAPTURE,
        "epsg": int(epsg) if isinstance(epsg, int | float) or str(epsg).isdigit() else REQUIRES_CAPTURE,
        "utm_zone": value_or_requires(first_value(payload, "utm_zone", "UTM_ZONE")),
        "hemisphere": value_or_requires(first_value(payload, "hemisphere", "HEMISPHERE")),
        "scale_m": value_or_requires(first_value(payload, "scale_m", "scale", "SCALE")),
        "out_size": value_or_requires(first_value(payload, "out_size", "OUT_SIZE")),
        "nodata": value_or_requires(first_value(payload, "nodata", "NODATA")),
    }


def first_json_payload(root: Path, patterns: tuple[str, ...]) -> dict[str, Any]:
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(payload, dict):
                return payload
    return {}


def first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    for value in payload.values():
        if isinstance(value, dict):
            nested = first_value(value, *keys)
            if nested is not None:
                return nested
    return None


def epsg_from_crs(crs: Any) -> int | None:
    if not isinstance(crs, str):
        return None
    marker = "EPSG:"
    if marker not in crs.upper():
        return None
    suffix = crs.upper().split(marker, 1)[1]
    digits = "".join(character for character in suffix if character.isdigit())
    return int(digits) if digits else None


def value_or_requires(value: Any) -> Any:
    return REQUIRES_CAPTURE if value is None else value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return REQUIRES_CAPTURE
    return result.stdout.strip() or REQUIRES_CAPTURE


if __name__ == "__main__":
    raise SystemExit(main())
