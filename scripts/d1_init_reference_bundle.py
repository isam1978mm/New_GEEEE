from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path("data/private_references/notebook_frozen")
TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


class BundleInitError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_token(value: str, name: str) -> str:
    value = value.strip()
    if not value or not TOKEN.fullmatch(value):
        raise BundleInitError(f"{name} must use only letters, numbers, dot, dash, or underscore")
    return value


def looks_like_url(value: str) -> bool:
    lowered = value.strip().lower()
    return "://" in lowered or lowered.startswith(("http:", "https:", "ftp:", "s3:", "gs:"))


def safe_rel_path(value: str) -> str:
    value = value.strip().replace("\\", "/")
    path = Path(value)
    if not value or looks_like_url(value):
        raise BundleInitError("artifact path must be a local relative path")
    if path.is_absolute() or value.startswith(("/", "~")) or (len(value) >= 2 and value[1] == ":"):
        raise BundleInitError("artifact path must be relative under artifacts")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise BundleInitError("artifact path must not use current or parent segments")
    return value


def create_bundle(
    root: Path,
    bundle_id: str,
    notebook_version: str,
    source_run_id: str,
    operator: str,
    families: list[str],
    artifact_paths: list[str],
    collected_at: str | None = None,
) -> dict[str, str | bool]:
    bundle_id = safe_token(bundle_id, "bundle id")
    families = [safe_token(item, "artifact family") for item in families] or ["new_ipynb_outputs"]
    families = sorted(dict.fromkeys(families))
    artifact_paths = [safe_rel_path(item) for item in artifact_paths]

    bundle_root = root / bundle_id
    artifacts_root = bundle_root / "artifacts"
    logs_root = bundle_root / "logs"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)
    for family in families:
        (artifacts_root / family).mkdir(parents=True, exist_ok=True)

    local_paths = [str((artifacts_root / item).as_posix()) for item in artifact_paths]
    finalized = bool(local_paths)
    manifest_name = "manifest.local.json" if finalized else "manifest.local.template.json"
    manifest_path = bundle_root / manifest_name
    manifest = {
        "bundle_id": bundle_id,
        "notebook_name": "new.ipynb",
        "notebook_version": notebook_version,
        "collected_at": collected_at or utc_now(),
        "operator": operator,
        "source_run_id": source_run_id,
        "artifact_families": families,
        "local_artifact_paths": local_paths,
        "notes": "LOCAL ONLY. Keep outside Git.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (bundle_root / "README.local.txt").write_text(
        "D1 local reference bundle\nKeep this folder outside Git.\nPlace real notebook outputs under artifacts/.\n",
        encoding="utf-8",
    )
    return {
        "bundle_root": str(bundle_root.as_posix()),
        "artifacts_root": str(artifacts_root.as_posix()),
        "logs_root": str(logs_root.as_posix()),
        "manifest_path": str(manifest_path.as_posix()),
        "finalized_manifest": finalized,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a D1 local reference bundle skeleton under data/private_references.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--notebook-version", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--operator", default="local_operator")
    parser.add_argument("--artifact-family", action="append", default=[])
    parser.add_argument("--artifact-path", action="append", default=[])
    parser.add_argument("--collected-at")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = create_bundle(
            Path(args.root),
            args.bundle_id,
            args.notebook_version,
            args.source_run_id,
            args.operator,
            args.artifact_family,
            args.artifact_path,
            args.collected_at,
        )
    except BundleInitError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    else:
        print("OK: D1 local reference bundle skeleton created")
        print(f"bundle_root: {result['bundle_root']}")
        print(f"manifest_path: {result['manifest_path']}")
        print(f"finalized_manifest: {result['finalized_manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
