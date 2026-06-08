"""
Deploy-1 OIDC environment sanity-check.

Validates that the current environment has the required Generic OIDC runtime
variables set correctly before activating OIDC on a server.

Safety guarantees:
  - Never reads or prints bearer token values.
  - Never prints full secret/URL/subject values (everything is masked).
  - Never calls the network.
  - Never modifies files.

Usage:
  uv run python scripts/deploy1_oidc_env_check.py            # human-readable, exit 0 on warnings
  uv run python scripts/deploy1_oidc_env_check.py --strict   # exit nonzero if any required check fails
  uv run python scripts/deploy1_oidc_env_check.py --json     # machine-readable safe output
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.parse import urlparse

# Required runtime variables (besides the JSON map handled separately).
_TRUE_LIKE = {"true", "1", "yes", "on"}
_BEARER_TOKEN_ENV = "AUTH5_SMOKE_BEARER_TOKEN"

# Severity levels
_PASS = "PASS"
_WARN = "WARN"
_FAIL = "FAIL"


def _is_true_like(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUE_LIKE


def _mask_host(url: str | None) -> str:
    """Return host only (no path/query), masking the full URL."""
    if not url:
        return "<missing>"
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/…"
        return "<unparseable>"
    except Exception:
        return "<unparseable>"


def _mask_client_id(value: str | None) -> str:
    """Show first 3 / last 3 chars only."""
    if not value:
        return "<missing>"
    v = value.strip()
    if len(v) <= 6:
        return f"len={len(v)}"
    return f"{v[:3]}…{v[-3:]} (len={len(v)})"


def _mask_actor(actor_id: str) -> str:
    """Redact actor subject — show length only, never the subject string."""
    return f"actor(len={len(actor_id)})"


def _check_bool_true(name: str, results: list[dict[str, str]]) -> None:
    value = os.environ.get(name)
    if _is_true_like(value):
        results.append({"check": name, "status": _PASS, "detail": "true-like"})
    else:
        results.append({"check": name, "status": _FAIL, "detail": "not set to a true-like value"})


def _check_https_url(name: str, results: list[dict[str, str]]) -> None:
    value = os.environ.get(name)
    if not value or not value.strip():
        results.append({"check": name, "status": _FAIL, "detail": "missing or blank"})
        return
    if not value.strip().startswith("https://"):
        results.append({"check": name, "status": _FAIL, "detail": "must start with https://"})
        return
    results.append({"check": name, "status": _PASS, "detail": f"host={_mask_host(value)}"})


def _check_present(name: str, results: list[dict[str, str]], *, masked: str) -> None:
    value = os.environ.get(name)
    if not value or not value.strip():
        results.append({"check": name, "status": _FAIL, "detail": "missing or blank"})
        return
    results.append({"check": name, "status": _PASS, "detail": masked})


def _check_run_authorizations(results: list[dict[str, str]]) -> None:
    name = "OPERATOR_RUN_AUTHORIZATIONS"
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        results.append({"check": name, "status": _FAIL, "detail": "missing or blank"})
        return

    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        results.append({"check": name, "status": _FAIL, "detail": "not valid JSON"})
        return

    if not isinstance(parsed, dict):
        results.append({"check": name, "status": _FAIL, "detail": "must be a JSON object"})
        return

    # Validate each actor -> list[str] mapping. Never print actor subjects or run IDs.
    actor_count = 0
    actor_with_runs = 0
    for actor_id, run_ids in parsed.items():
        if not isinstance(actor_id, str):
            results.append({"check": name, "status": _FAIL, "detail": "actor keys must be strings"})
            return
        if not isinstance(run_ids, list) or not all(isinstance(r, str) for r in run_ids):
            results.append({
                "check": name,
                "status": _FAIL,
                "detail": f"{_mask_actor(actor_id)} value must be list[str]",
            })
            return
        actor_count += 1
        if len(run_ids) >= 1:
            actor_with_runs += 1

    if actor_count == 0:
        results.append({"check": name, "status": _FAIL, "detail": "no actors mapped"})
        return
    if actor_with_runs == 0:
        results.append({
            "check": name,
            "status": _FAIL,
            "detail": f"{actor_count} actor(s) but none have any run IDs",
        })
        return

    results.append({
        "check": name,
        "status": _PASS,
        "detail": f"{actor_count} actor(s), {actor_with_runs} with >=1 run ID",
    })


def _check_trusted_proxy(results: list[dict[str, str]]) -> None:
    name = "OPERATOR_AUTH_TRUSTED_PROXY_ENABLED"
    value = os.environ.get(name)
    if _is_true_like(value):
        results.append({
            "check": name,
            "status": _WARN,
            "detail": "true while OIDC enabled — verify this is intended (token is the auth mechanism)",
        })
    else:
        results.append({"check": name, "status": _PASS, "detail": "false (recommended with OIDC)"})


def run_checks() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    _check_bool_true("OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED", results)
    _check_bool_true("OPERATOR_AUTH_OIDC_ENABLED", results)
    _check_https_url("OPERATOR_AUTH_OIDC_ISSUER_URL", results)
    _check_present(
        "OPERATOR_AUTH_OIDC_CLIENT_ID",
        results,
        masked=_mask_client_id(os.environ.get("OPERATOR_AUTH_OIDC_CLIENT_ID")),
    )
    _check_https_url("OPERATOR_AUTH_OIDC_JWKS_URI", results)
    _check_run_authorizations(results)
    _check_trusted_proxy(results)

    # Never print the bearer token; just confirm we are not exposing it.
    if os.environ.get(_BEARER_TOKEN_ENV):
        results.append({
            "check": _BEARER_TOKEN_ENV,
            "status": _WARN,
            "detail": "is set in environment; value intentionally not displayed",
        })

    return results


def _has_fail(results: list[dict[str, str]]) -> bool:
    return any(r["status"] == _FAIL for r in results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deploy-1 OIDC environment sanity-check. Prints no secrets or tokens.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable safe JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero if any required check FAILs (default: warnings exit 0)",
    )
    args = parser.parse_args(argv)

    results = run_checks()

    if args.json:
        print(json.dumps({"checks": results, "ok": not _has_fail(results)}, indent=2))
    else:
        for r in results:
            print(f"{r['status']:4}  {r['check']}: {r['detail']}")
        summary = "FAIL" if _has_fail(results) else "OK"
        print(f"\nSummary: {summary}")

    if args.strict and _has_fail(results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
