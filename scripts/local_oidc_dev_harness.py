"""
LOCAL-1 — local-only Generic OIDC development harness.

Lets a developer exercise the full OIDC valid-token path on a local machine
WITHOUT any real provider, real secret, real token, VPS, or deployment.

LOCAL ONLY. This harness:
  - generates a throwaway RSA keypair in memory,
  - mints a short-lived local fake RS256 JWT,
  - serves a matching JWKS on 127.0.0.1 only,
  - prints local-only env export commands.

It never:
  - contacts a real OIDC provider,
  - writes or prints private key material,
  - prints full tokens unless you pass --print-token,
  - binds to anything other than localhost.

Requires only the Python standard library plus PyJWT (already a project
dependency via PyJWT[crypto]). Adds no new dependencies.

Modes:
  make-token  generate a local fake signed JWT + matching JWKS
  serve-jwks  serve a matching JWKS on http://127.0.0.1:<port>/.well-known/jwks.json
  env         print local-only env export commands
  all         print the full local test sequence
  self-check  validate defaults without network; exit 0 if valid
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

# Local-only defaults — never real provider values.
_DEFAULT_ISSUER = "http://127.0.0.1:8765"
_DEFAULT_CLIENT_ID = "gee-local-operator-ui"
_DEFAULT_SUB = "local-operator"
_DEFAULT_RUN_ID = "local_run_001"
_DEFAULT_PORT = 8765
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_TTL = 300
_KID = "local-dev-key"

_LOCALHOST_HOSTS = {"127.0.0.1", "localhost", "::1"}

# Ignored local-only output dir (data/ is gitignored).
_LOCAL_OUTPUT_DIR = os.path.join("data", "local_oidc_dev")
_JWKS_FILENAME = "jwks.json"


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

def _validate_localhost(host: str) -> None:
    if host not in _LOCALHOST_HOSTS:
        raise ValueError(
            f"refusing non-localhost bind: {host!r} (allowed: {sorted(_LOCALHOST_HOSTS)})"
        )


# ---------------------------------------------------------------------------
# Key / token / JWKS generation
# ---------------------------------------------------------------------------

def _generate_keypair() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _public_jwk(private_key: rsa.RSAPrivateKey, kid: str) -> dict[str, Any]:
    """Build a PyJWT-compatible PUBLIC JWK. Never includes private material."""
    public_jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk["kid"] = kid
    public_jwk["use"] = "sig"
    public_jwk["alg"] = "RS256"
    # Defensive: public JWK must not carry any private RSA fields.
    for private_field in ("d", "p", "q", "dp", "dq", "qi"):
        public_jwk.pop(private_field, None)
    return public_jwk


def generate_bundle(
    *,
    issuer: str,
    client_id: str,
    sub: str,
    ttl_seconds: int,
    kid: str = _KID,
) -> tuple[str, dict[str, Any]]:
    """Generate (signed_jwt, jwks_dict) sharing the same in-memory key.

    The private key never leaves this function; only the signed token and the
    public JWKS are returned.
    """
    private_key = _generate_keypair()
    now = int(time.time())
    claims = {
        "iss": issuer,
        "aud": client_id,
        "sub": sub,
        "roles": ["operator"],
        "iat": now,
        "exp": now + ttl_seconds,
    }
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": kid})
    jwks = {"keys": [_public_jwk(private_key, kid)]}
    return token, jwks


def _redacted_token_summary(token: str) -> str:
    return f"local fake JWT (RS256, kid={_KID}, len={len(token)}) — pass --print-token to reveal"


# ---------------------------------------------------------------------------
# JWKS HTTP server (127.0.0.1 only)
# ---------------------------------------------------------------------------

def make_jwks_handler(jwks: dict[str, Any]) -> type[BaseHTTPRequestHandler]:
    payload = json.dumps(jwks).encode("utf-8")

    class _JWKSHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/.well-known/jwks.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args: Any) -> None:  # silence noisy logging
            return

    return _JWKSHandler


def make_jwks_server(host: str, port: int, jwks: dict[str, Any]) -> HTTPServer:
    """Create (but do not start) a localhost-only JWKS HTTP server."""
    _validate_localhost(host)
    handler = make_jwks_handler(jwks)
    return HTTPServer((host, port), handler)


# ---------------------------------------------------------------------------
# Mode implementations — return printable lines so tests can inspect output
# ---------------------------------------------------------------------------

def mode_env(args: argparse.Namespace) -> list[str]:
    run_auth = json.dumps({args.sub: [args.run_id]})
    return [
        "# LOCAL-ONLY OIDC env (fake provider on 127.0.0.1) — do not use on a server",
        "export OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true",
        "export OPERATOR_AUTH_TRUSTED_PROXY_ENABLED=false",
        "export OPERATOR_AUTH_OIDC_ENABLED=true",
        f"export OPERATOR_AUTH_OIDC_ISSUER_URL={args.issuer}",
        f"export OPERATOR_AUTH_OIDC_CLIENT_ID={args.client_id}",
        f"export OPERATOR_AUTH_OIDC_JWKS_URI={args.issuer}/.well-known/jwks.json",
        f"export OPERATOR_RUN_AUTHORIZATIONS='{run_auth}'",
    ]


def mode_make_token(args: argparse.Namespace) -> tuple[str, dict[str, Any], list[str]]:
    token, jwks = generate_bundle(
        issuer=args.issuer,
        client_id=args.client_id,
        sub=args.sub,
        ttl_seconds=args.ttl_seconds,
    )
    lines = ["# LOCAL-ONLY fake token generated in memory (private key never written/printed)"]
    if args.print_token:
        lines.append(f"token: {token}")
    else:
        lines.append(_redacted_token_summary(token))

    if args.print_jwks:
        lines.append("jwks (public only):")
        lines.append(json.dumps(jwks, indent=2))

    if args.write_jwks:
        os.makedirs(_LOCAL_OUTPUT_DIR, exist_ok=True)
        jwks_path = os.path.join(_LOCAL_OUTPUT_DIR, _JWKS_FILENAME)
        with open(jwks_path, "w", encoding="utf-8") as fh:
            json.dump(jwks, fh)
        lines.append(f"wrote public JWKS to {jwks_path} (gitignored under data/)")

    return token, jwks, lines


def mode_all(args: argparse.Namespace) -> list[str]:
    return [
        "# LOCAL-ONLY end-to-end OIDC test sequence (local machine, no real provider)",
        "",
        "# Terminal A — serve the local fake JWKS (127.0.0.1 only):",
        f"uv run python scripts/local_oidc_dev_harness.py --mode serve-jwks --port {args.port} --print-token",
        "#   (copy the printed token from terminal A; it matches the served JWKS)",
        "",
        "# Terminal B — export the local-only env and start the app:",
        f"eval \"$(uv run python scripts/local_oidc_dev_harness.py --mode env --run-id {args.run_id})\"",
        "uvicorn app.main:app --host 127.0.0.1 --port 8015",
        "",
        "# Terminal C — run the Auth-5 smoke tests:",
        "uv run python scripts/auth5_oidc_smoke.py "
        f"--base-url http://127.0.0.1:8015 --run-id {args.run_id} --mode no-token",
        "uv run python scripts/auth5_oidc_smoke.py "
        f"--base-url http://127.0.0.1:8015 --run-id {args.run_id} --mode invalid-token",
        "#   then supply the local fake token from terminal A (shell only, never committed):",
        "export AUTH5_SMOKE_BEARER_TOKEN=<paste local fake token from terminal A>",
        "uv run python scripts/auth5_oidc_smoke.py "
        f"--base-url http://127.0.0.1:8015 --run-id {args.run_id} --mode valid-token",
        "unset AUTH5_SMOKE_BEARER_TOKEN",
    ]


def run_self_check(args: argparse.Namespace) -> bool:
    checks: list[tuple[object, object, str]] = [
        (args.issuer, _DEFAULT_ISSUER, "issuer default"),
        (args.client_id, _DEFAULT_CLIENT_ID, "client id default"),
        (args.sub, _DEFAULT_SUB, "actor/sub default"),
        (args.run_id, _DEFAULT_RUN_ID, "run id default"),
        (args.port, _DEFAULT_PORT, "port default"),
        (args.host, _DEFAULT_HOST, "host default"),
    ]
    ok = True
    for actual, expected, name in checks:
        if actual == expected:
            print(f"PASS  self-check: {name} == {expected!r}")
        else:
            print(f"FAIL  self-check: {name}: {actual!r} != {expected!r}")
            ok = False

    # Confirm localhost bind validation works both ways.
    try:
        _validate_localhost(args.host)
        print(f"PASS  self-check: localhost bind accepted for {args.host}")
    except ValueError:
        print(f"FAIL  self-check: localhost bind rejected for {args.host}")
        ok = False

    try:
        _validate_localhost("0.0.0.0")
        print("FAIL  self-check: non-localhost bind 0.0.0.0 was NOT rejected")
        ok = False
    except ValueError:
        print("PASS  self-check: non-localhost bind 0.0.0.0 correctly rejected")

    return ok


# ---------------------------------------------------------------------------
# Argument parser + main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LOCAL-ONLY Generic OIDC dev harness. No real provider, no VPS, no secrets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["make-token", "serve-jwks", "env", "all", "self-check"],
        default="self-check",
    )
    parser.add_argument("--issuer", default=_DEFAULT_ISSUER, help="local issuer URL (127.0.0.1)")
    parser.add_argument("--client-id", default=_DEFAULT_CLIENT_ID, help="local client id / audience")
    parser.add_argument("--sub", default=_DEFAULT_SUB, help="local subject / actor id")
    parser.add_argument("--run-id", default=_DEFAULT_RUN_ID, help="local run id for Auth-3 mapping")
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT, help="local JWKS port")
    parser.add_argument("--host", default=_DEFAULT_HOST, help="bind host (localhost only)")
    parser.add_argument("--ttl-seconds", type=int, default=_DEFAULT_TTL, help="token lifetime")
    parser.add_argument("--print-token", action="store_true", help="reveal the full local fake token")
    parser.add_argument("--print-jwks", action="store_true", help="print the public JWKS JSON")
    parser.add_argument(
        "--write-jwks",
        action="store_true",
        help="write public JWKS to data/local_oidc_dev/jwks.json (gitignored)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "self-check":
        return 0 if run_self_check(args) else 1

    if args.mode == "env":
        for line in mode_env(args):
            print(line)
        return 0

    if args.mode == "make-token":
        _, _, lines = mode_make_token(args)
        for line in lines:
            print(line)
        return 0

    if args.mode == "all":
        for line in mode_all(args):
            print(line)
        return 0

    if args.mode == "serve-jwks":
        try:
            _validate_localhost(args.host)
        except ValueError as exc:
            print(f"FAIL  {exc}")
            return 1
        token, jwks, lines = mode_make_token(args)
        for line in lines:
            print(line)
        server = make_jwks_server(args.host, args.port, jwks)
        url = f"http://{args.host}:{args.port}/.well-known/jwks.json"
        print(f"# Serving local JWKS at {url} (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n# Stopped local JWKS server")
        finally:
            server.server_close()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
