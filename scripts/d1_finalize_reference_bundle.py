from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


class BundleFinalizeError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_token(value: str, name: str) -> str:
    value = value.strip()
    if not value or not TOKEN.fullmatch(value):
        raise BundleFinalizeError(f"{name} must use only letters, numbers, dot, dash, or underscore")
    return value


def safe_family(value: str) -> str:
    return safe_token(value, "artifact family")


def scan_artifacts(bundle_root: Path) -> tuple[list[str], list[str]]:
    artifacts_root = bundle_root / "artifacts"
    if not artifacts_root.is_dir():
        raise BundleFinalizeError(f"artifacts folder not found: {artifacts_root.as_posix()}")

    local_paths: list[str] = []
    families: set[str] = set()
    for item in sorted(artifacts_root.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(artifacts_root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        local_paths.append(str(item.as_posix()))
        family = rel.parts[0] if len(rel.parts) > 1 else "new_ipynb_outputs"
        families.add(safe_family(family))

    if not local_paths:
        raise BundleFinalizeError("no artifact files found under artifacts")
    return sorted(families), local_paths


def load_template(bundle_root: Path) -> dict[str, object]:
    template_path = bundle_root / "manifest.local.template.json"
    if not template_path.is_file():
        return {}
    data = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BundleFinalizeError("manifest template must be a JSON object")
    return data


def finalize_bundle(
    bundle_root: Path,
    notebook_version: str | None = None,
    source_run_id: str | None = None,
    operator: str | None = None,
    collected_at: str | None = None,
) -> dict[str, str | int]:
    if not bundle_root.is_dir():
        raise BundleFinalizeError(f"bundle folder not found: {bundle_root.as_posix()}")

    template = load_template(bundle_root)
    bundle_id = str(template.get("bundle_id") or bundle_root.name)
    safe_token(bundle_id, "bundle id")
    families, local_paths = scan_artifacts(bundle_root)

    manifest = {
        "bundle_id": bundle_id,
        "notebook_name": "new.ipynb",
        "notebook_version": notebook_version or str(template.get("notebook_version") or "local-new-ipynb-version"),
        "collected_at": collected_at or utc_now(),
        "operator": operator or str(template.get("operator") or "local_operator"),
        "source_run_id": source_run_id or str(template.get("source_run_id") or "local-source-run"),
        "artifact_families": families,
        "local_artifact_paths": local_paths,
        "notes": "LOCAL ONLY. Final D1 new.ipynb reference manifest. Keep outside Git.",
    }
    manifest_path = bundle_root / "manifest.local.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "manifest_path": str(manifest_path.as_posix()),
        "artifact_count": len(local_paths),
        "family_count": len(families),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize a local D1 new.ipynb reference manifest from files already under artifacts.")
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--notebook-version")
    parser.add_argument("--source-run-id")
    parser.add_argument("--operator")
    parser.add_argument("--collected-at")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = finalize_bundle(
            Path(args.bundle_root),
            notebook_version=args.notebook_version,
            source_run_id=args.source_run_id,
            operator=args.operator,
            collected_at=args.collected_at,
        )
    except (BundleFinalizeError, json.JSONDecodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}")
        return 1

    if args.json:
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    else:
        print("OK: D1 local reference manifest finalized")
        print(f"manifest_path: {result['manifest_path']}")
        print(f"artifact_count: {result['artifact_count']}")
        print(f"family_count: {result['family_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
