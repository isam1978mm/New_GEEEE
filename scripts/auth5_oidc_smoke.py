"""
Auth-5 OIDC smoke-test script.

Tests that the operator overlay route enforces OIDC correctly in a running app:
  no-token      → expect HTTP 403 / denied
  invalid-token → expect HTTP 403 / denied
  valid-token   → expect configurable status/outcome (default 200/allowed)
  all           → no-token + invalid-token + valid-token (skipped if token env absent)
  self-check    → validates arg-parsing defaults, no network call

Never prints raw bearer tokens or Authorization header values.

Usage:
  uv run python scripts/auth5_oidc_smoke.py --mode self-check
  uv run python scripts/auth5_oidc_smoke.py --run-id <run-id> --mode no-token
  uv run python scripts/auth5_oidc_smoke.py --run-id <run-id> --mode invalid-token
  uv run python scripts/auth5_oidc_smoke.py --run-id <run-id> --mode valid-token
  uv run python scripts/auth5_oidc_smoke.py --run-id <run-id> --mode all
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_INVALID_TOKEN = "invalid.auth5.smoke.token"
_DENIED_LEAK_KEYS = ("preview_payload", "artifact_family", "run_id", "/download/", "sha256")


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------

def _build_url(base_url: str, run_id: str, artifact_family: str, access_mode: str) -> str:
    query = urllib.parse.urlencode({
        "artifact_family": artifact_family,
        "access_mode": access_mode,
    })
    run_id_enc = urllib.parse.quote(run_id, safe="")
    return f"{base_url.rstrip('/')}/runs/{run_id_enc}/operator/private-overlays?{query}"


def _fetch(url: str, token: str | None, timeout: int) -> tuple[int, dict[str, Any]]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return exc.code, body
    except Exception as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Response validators
# ---------------------------------------------------------------------------

def _check_denied_body(body: dict[str, Any]) -> list[str]:
    body_text = json.dumps(body).lower()
    return [key for key in _DENIED_LEAK_KEYS if key in body_text]


def _check_allowed_body(body: dict[str, Any], expected_outcome: str) -> list[str]:
    violations: list[str] = []
    if body.get("outcome") != expected_outcome:
        violations.append(f"outcome={body.get('outcome')!r}, want {expected_outcome!r}")
    if "frontend_visible" in body and body["frontend_visible"] != "operator_only":
        violations.append(f"frontend_visible={body['frontend_visible']!r}, want 'operator_only'")
    if "downloadable_via_api" in body and body["downloadable_via_api"] is not False:
        violations.append(f"downloadable_via_api={body['downloadable_via_api']!r}, want False")
    return violations


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _pass(label: str) -> None:
    print(f"PASS  {label}")


def _fail(label: str, reason: str) -> None:
    print(f"FAIL  {label}: {reason}")


# ---------------------------------------------------------------------------
# Smoke test runners
# ---------------------------------------------------------------------------

def run_no_token(args: argparse.Namespace) -> bool:
    label = "no-token → expect 403/denied"
    try:
        url = _build_url(args.base_url, args.run_id, args.artifact_family, args.access_mode)
        status, body = _fetch(url, token=None, timeout=args.timeout_seconds)
    except RuntimeError as exc:
        _fail(label, str(exc))
        return False

    if status != 403:
        _fail(label, f"HTTP {status}, want 403")
        return False
    if body.get("outcome") != "denied":
        _fail(label, f"outcome={body.get('outcome')!r}, want 'denied'")
        return False
    leaks = _check_denied_body(body)
    if leaks:
        _fail(label, f"response leaks: {leaks}")
        return False
    _pass(label)
    return True


def run_invalid_token(args: argparse.Namespace) -> bool:
    label = "invalid-token → expect 403/denied"
    try:
        url = _build_url(args.base_url, args.run_id, args.artifact_family, args.access_mode)
        status, body = _fetch(url, token=_INVALID_TOKEN, timeout=args.timeout_seconds)
    except RuntimeError as exc:
        _fail(label, str(exc))
        return False

    if status != 403:
        _fail(label, f"HTTP {status}, want 403")
        return False
    if body.get("outcome") != "denied":
        _fail(label, f"outcome={body.get('outcome')!r}, want 'denied'")
        return False
    leaks = _check_denied_body(body)
    if leaks:
        _fail(label, f"response leaks: {leaks}")
        return False
    _pass(label)
    return True


def run_valid_token(args: argparse.Namespace, *, skip_if_missing: bool = False) -> bool | None:
    """Run valid-token smoke check. Returns None if skipped (token absent and skip_if_missing=True)."""
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        if skip_if_missing:
            print(f"SKIP  valid-token: {args.token_env} not set — skipping (not a failure)")
            return None
        _fail("valid-token", f"env var {args.token_env!r} is missing or blank")
        return False

    label = f"valid-token → expect {args.expected_valid_status}/{args.expected_valid_outcome}"
    try:
        url = _build_url(args.base_url, args.run_id, args.artifact_family, args.access_mode)
        status, body = _fetch(url, token=token, timeout=args.timeout_seconds)
    except RuntimeError as exc:
        _fail(label, str(exc))
        return False

    if status != args.expected_valid_status:
        _fail(label, f"HTTP {status}, want {args.expected_valid_status}")
        return False

    violations = _check_allowed_body(body, args.expected_valid_outcome)
    if violations:
        _fail(label, "; ".join(violations))
        return False

    _pass(label)
    return True


def run_self_check(args: argparse.Namespace) -> bool:
    """Validate arg-parsing defaults without network calls. Returns True on all pass."""
    checks: list[tuple[object, object, str]] = [
        (args.artifact_family, "phase_d1_private_geojson", "artifact_family default"),
        (args.access_mode, "operator_only_preview", "access_mode default"),
        (args.token_env, "AUTH5_SMOKE_BEARER_TOKEN", "token_env default"),
        (args.expected_valid_status, 200, "expected_valid_status default"),
        (args.expected_valid_outcome, "allowed", "expected_valid_outcome default"),
        (args.timeout_seconds, 10, "timeout_seconds default"),
    ]
    ok = True
    for actual, expected, name in checks:
        if actual == expected:
            _pass(f"self-check: {name} == {expected!r}")
        else:
            _fail(f"self-check: {name}", f"{actual!r} != {expected!r}")
            ok = False
    return ok


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auth-5 OIDC smoke-test script. Never prints tokens.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AUTH5_SMOKE_BASE_URL", "http://127.0.0.1:8015"),
        help="Base URL of the running app (default: http://127.0.0.1:8015 or AUTH5_SMOKE_BASE_URL)",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("AUTH5_SMOKE_RUN_ID"),
        help="Run ID to test (required unless --mode self-check; or AUTH5_SMOKE_RUN_ID)",
    )
    parser.add_argument(
        "--artifact-family",
        default=os.environ.get("AUTH5_SMOKE_ARTIFACT_FAMILY", "phase_d1_private_geojson"),
        help="Artifact family to request (default: phase_d1_private_geojson)",
    )
    parser.add_argument(
        "--access-mode",
        default="operator_only_preview",
        help="Access mode query param (default: operator_only_preview)",
    )
    parser.add_argument(
        "--token-env",
        default="AUTH5_SMOKE_BEARER_TOKEN",
        help="Env var name holding the bearer token for valid-token mode",
    )
    parser.add_argument(
        "--mode",
        choices=["no-token", "invalid-token", "valid-token", "all", "self-check"],
        default="all",
        help="Which smoke test(s) to run (default: all)",
    )
    parser.add_argument(
        "--expected-valid-status",
        type=int,
        default=200,
        help="Expected HTTP status for valid-token mode (default: 200)",
    )
    parser.add_argument(
        "--expected-valid-outcome",
        default="allowed",
        help="Expected JSON outcome for valid-token mode (default: allowed)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.mode == "self-check":
        return 0 if run_self_check(args) else 1

    if not args.run_id:
        parser.error("--run-id is required unless --mode self-check")

    results: list[bool] = []

    if args.mode == "no-token":
        results.append(run_no_token(args))
    elif args.mode == "invalid-token":
        results.append(run_invalid_token(args))
    elif args.mode == "valid-token":
        result = run_valid_token(args, skip_if_missing=False)
        results.append(result if result is not None else False)
    elif args.mode == "all":
        results.append(run_no_token(args))
        results.append(run_invalid_token(args))
        skippable = run_valid_token(args, skip_if_missing=True)
        if skippable is not None:
            results.append(skippable)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
