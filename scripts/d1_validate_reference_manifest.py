"""
D1 — local-only validator for an outside-Git frozen notebook reference manifest.

Validates a manifest JSON file that an operator keeps OUTSIDE Git (under the
Git-ignored data/ tree). It does NOT read artifact contents, does NOT call the
network, and does NOT write any files.

Safety guarantees:
  - Never reads artifact file contents.
  - Never prints coordinates/geometry/hashes — it FAILS if the manifest carries
    suspicious keys (coordinates, geometry, bounds, bbox, lat/lon, crs,
    transform, sha256, hash, ...).
  - Only accepts local filesystem paths (rejects URLs).
  - Rejects absolute artifact paths outside data/private_references unless
    --allow-external is passed.

Usage:
  uv run python scripts/d1_validate_reference_manifest.py --manifest <path>
  uv run python scripts/d1_validate_reference_manifest.py --manifest <path> --strict
  uv run python scripts/d1_validate_reference_manifest.py --manifest <path> --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

_REQUIRED_KEYS = (
    "bundle_id",
    "notebook_name",
    "notebook_version",
    "collected_at",
    "operator",
    "source_run_id",
    "artifact_families",
    "local_artifact_paths",
    "notes",
)

# Keys that must never appear anywhere in a committed/inspected manifest —
# they would carry coordinates, geometry, or private digests.
_SUSPICIOUS_KEYS = {
    "coordinates",
    "geometry",
    "bounds",
    "bbox",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "crs",
    "transform",
    "sha256",
    "hash",
}

_ALLOWED_PREFIX = "data/private_references"

_PASS = "PASS"
_WARN = "WARN"
_FAIL = "FAIL"


def _looks_like_url(path: str) -> bool:
    lowered = path.strip().lower()
    return "://" in lowered or lowered.startswith(("http:", "https:", "ftp:", "s3:", "gs:"))


def _normalize(path: str) -> str:
    return path.replace("\\", "/")


def _is_rooted(raw: str) -> bool:
    """Platform-independent 'absolute/rooted' check (avoids os.path.isabs quirks).

    Treats leading slash, a drive letter (``C:``), or a home prefix (``~``) as rooted.
    """
    norm = _normalize(raw)
    if norm.startswith("/") or norm.startswith("~"):
        return True
    if len(raw) >= 2 and raw[1] == ":":
        return True
    return False


def _collect_keys(obj: Any) -> set[str]:
    """Recursively collect all dict keys (lowercased) in the manifest."""
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                found.add(key.lower())
            found |= _collect_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _collect_keys(item)
    return found


def validate_manifest(manifest: dict[str, Any], *, allow_external: bool) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    # 1. Required keys.
    missing = [k for k in _REQUIRED_KEYS if k not in manifest]
    if missing:
        results.append({"check": "required_keys", "status": _FAIL, "detail": f"missing: {missing}"})
    else:
        results.append({"check": "required_keys", "status": _PASS, "detail": "all present"})

    # 2. Suspicious keys (coordinates/geometry/hashes) anywhere in the manifest.
    suspicious_present = sorted(_collect_keys(manifest) & _SUSPICIOUS_KEYS)
    if suspicious_present:
        results.append({
            "check": "suspicious_keys",
            "status": _FAIL,
            "detail": f"forbidden keys present: {suspicious_present}",
        })
    else:
        results.append({"check": "suspicious_keys", "status": _PASS, "detail": "none found"})

    # 3. artifact_families must be a non-empty list of strings.
    families = manifest.get("artifact_families")
    if not isinstance(families, list) or not families or not all(isinstance(f, str) for f in families):
        results.append({
            "check": "artifact_families",
            "status": _FAIL,
            "detail": "must be a non-empty list of strings",
        })
    else:
        results.append({"check": "artifact_families", "status": _PASS, "detail": f"{len(families)} family(ies)"})

    # 4. local_artifact_paths: local only, no URLs, no absolute external paths.
    paths = manifest.get("local_artifact_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
        results.append({
            "check": "local_artifact_paths",
            "status": _FAIL,
            "detail": "must be a non-empty list of string paths",
        })
    else:
        path_failures: list[str] = []
        external_warn = 0
        for raw in paths:
            if _looks_like_url(raw):
                path_failures.append("url-like path")
                continue
            norm = _normalize(raw)
            is_abs = _is_rooted(raw)
            under_prefix = _ALLOWED_PREFIX in norm
            if is_abs and not under_prefix:
                if allow_external:
                    external_warn += 1
                else:
                    path_failures.append("absolute path outside data/private_references")
        if path_failures:
            results.append({
                "check": "local_artifact_paths",
                "status": _FAIL,
                "detail": f"{len(path_failures)} invalid: {sorted(set(path_failures))}",
            })
        else:
            detail = f"{len(paths)} local path(s)"
            if external_warn:
                detail += f"; {external_warn} external (allowed by flag)"
            results.append({"check": "local_artifact_paths", "status": _PASS, "detail": detail})

    # 5. Always remind that references live outside Git.
    results.append({
        "check": "outside_git",
        "status": _WARN,
        "detail": "frozen references are operator-owned OUTSIDE Git (data/ is gitignored)",
    })

    return results


def _has_fail(results: list[dict[str, str]]) -> bool:
    return any(r["status"] == _FAIL for r in results)


def _load_manifest(path: str) -> tuple[dict[str, Any] | None, str | None]:
    if _looks_like_url(path):
        return None, "manifest path must be a local filesystem path, not a URL"
    if not os.path.exists(path):
        return None, f"manifest file not found: {path}"
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        return None, f"manifest is not valid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return None, "manifest must be a JSON object"
    return data, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a local-only outside-Git D1 frozen reference manifest. Prints no artifact contents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--manifest", required=True, help="path to the local manifest JSON")
    parser.add_argument("--strict", action="store_true", help="exit nonzero if any check FAILs")
    parser.add_argument("--json", action="store_true", help="emit machine-readable safe JSON")
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="permit absolute artifact paths outside data/private_references (warns instead of fails)",
    )
    args = parser.parse_args(argv)

    manifest, load_error = _load_manifest(args.manifest)
    if load_error:
        if args.json:
            print(json.dumps({"checks": [{"check": "load", "status": _FAIL, "detail": load_error}], "ok": False}, indent=2))
        else:
            print(f"FAIL  load: {load_error}")
        return 1 if args.strict else 0

    assert manifest is not None
    results = validate_manifest(manifest, allow_external=args.allow_external)

    if args.json:
        print(json.dumps({"checks": results, "ok": not _has_fail(results)}, indent=2))
    else:
        for r in results:
            print(f"{r['status']:4}  {r['check']}: {r['detail']}")
        print(f"\nSummary: {'FAIL' if _has_fail(results) else 'OK'}")

    if args.strict and _has_fail(results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
