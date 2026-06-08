"""Unit tests for scripts/local_oidc_dev_harness.py. Local-only; no real network/provider."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import local_oidc_dev_harness as harness


def _args(**overrides: object):
    parser = harness.build_parser()
    ns = parser.parse_args([])
    for key, value in overrides.items():
        setattr(ns, key, value)
    return ns


# ---------------------------------------------------------------------------
# self-check
# ---------------------------------------------------------------------------

def test_self_check_exits_zero() -> None:
    assert harness.main(["--mode", "self-check"]) == 0


def test_defaults_use_localhost() -> None:
    args = _args()
    assert "127.0.0.1" in args.issuer
    assert args.host == "127.0.0.1"
    assert args.port == 8765


# ---------------------------------------------------------------------------
# env mode
# ---------------------------------------------------------------------------

def test_env_mode_prints_local_only_env_commands() -> None:
    lines = harness.mode_env(_args(run_id="local_run_001"))
    text = "\n".join(lines)
    assert "OPERATOR_AUTH_OIDC_ENABLED=true" in text
    assert "OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true" in text
    assert "127.0.0.1" in text


def test_env_mode_includes_auth3_run_authorization_mapping() -> None:
    lines = harness.mode_env(_args(sub="local-operator", run_id="local_run_001"))
    text = "\n".join(lines)
    assert "OPERATOR_RUN_AUTHORIZATIONS" in text
    # The mapping must connect the actor/sub to the run id.
    assert json.dumps({"local-operator": ["local_run_001"]}) in text


def test_env_mode_does_not_include_real_provider_domains() -> None:
    text = "\n".join(harness.mode_env(_args()))
    for forbidden in ("example.test", "auth0.com", "okta.com", "google.com", "microsoftonline.com"):
        assert forbidden not in text


# ---------------------------------------------------------------------------
# token generation
# ---------------------------------------------------------------------------

def test_token_generation_has_expected_claims_and_kid() -> None:
    token, jwks = harness.generate_bundle(
        issuer="http://127.0.0.1:8765",
        client_id="gee-local-operator-ui",
        sub="local-operator",
        ttl_seconds=300,
    )
    header = jwt.get_unverified_header(token)
    assert header["kid"] == "local-dev-key"
    assert header["alg"] == "RS256"

    # Verify the token against its own JWKS public key (round-trip, no network).
    from jwt.algorithms import RSAAlgorithm

    public_key = RSAAlgorithm.from_jwk(json.dumps(jwks["keys"][0]))
    claims = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="gee-local-operator-ui",
        issuer="http://127.0.0.1:8765",
    )
    assert claims["sub"] == "local-operator"
    assert claims["aud"] == "gee-local-operator-ui"
    assert claims["iss"] == "http://127.0.0.1:8765"
    assert claims["roles"] == ["operator"]


def test_make_token_does_not_print_full_token_by_default(
    capsys: pytest.CaptureFixture,
) -> None:
    token, _, lines = harness.mode_make_token(_args(print_token=False))
    text = "\n".join(lines)
    assert token not in text
    assert "pass --print-token to reveal" in text


def test_make_token_prints_full_token_when_requested() -> None:
    token, _, lines = harness.mode_make_token(_args(print_token=True))
    text = "\n".join(lines)
    assert token in text


# ---------------------------------------------------------------------------
# JWKS contains public key only
# ---------------------------------------------------------------------------

def test_jwks_contains_public_key_only_no_private_material() -> None:
    _, jwks = harness.generate_bundle(
        issuer="http://127.0.0.1:8765",
        client_id="gee-local-operator-ui",
        sub="local-operator",
        ttl_seconds=300,
    )
    key = jwks["keys"][0]
    assert key["kty"] == "RSA"
    assert "n" in key and "e" in key
    # Private RSA JWK fields must be absent.
    for private_field in ("d", "p", "q", "dp", "dq", "qi"):
        assert private_field not in key


def test_no_output_contains_private_key_material(capsys: pytest.CaptureFixture) -> None:
    harness.main(["--mode", "make-token", "--print-jwks", "--print-token"])
    out = capsys.readouterr().out
    # PEM private key markers must never appear.
    assert "PRIVATE KEY" not in out
    assert "BEGIN RSA" not in out
    # The printed JWKS must contain no private RSA JWK field.
    jwks_section = out.split("jwks (public only):", 1)[1]
    jwks = json.loads(jwks_section)
    key = jwks["keys"][0]
    for private_field in ("d", "p", "q", "dp", "dq", "qi"):
        assert private_field not in key


# ---------------------------------------------------------------------------
# localhost bind enforcement
# ---------------------------------------------------------------------------

def test_non_localhost_bind_is_rejected() -> None:
    with pytest.raises(ValueError):
        harness._validate_localhost("0.0.0.0")
    with pytest.raises(ValueError):
        harness._validate_localhost("10.0.0.5")


def test_localhost_bind_is_accepted() -> None:
    harness._validate_localhost("127.0.0.1")
    harness._validate_localhost("localhost")


def test_make_jwks_server_binds_localhost_only_and_closes() -> None:
    _, jwks = harness.generate_bundle(
        issuer="http://127.0.0.1:8765",
        client_id="gee-local-operator-ui",
        sub="local-operator",
        ttl_seconds=300,
    )
    # Ephemeral port 0 -> OS assigns a free port; bind on 127.0.0.1 then close.
    server = harness.make_jwks_server("127.0.0.1", 0, jwks)
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_make_jwks_server_rejects_non_localhost() -> None:
    _, jwks = harness.generate_bundle(
        issuer="http://127.0.0.1:8765",
        client_id="gee-local-operator-ui",
        sub="local-operator",
        ttl_seconds=300,
    )
    with pytest.raises(ValueError):
        harness.make_jwks_server("0.0.0.0", 0, jwks)


# ---------------------------------------------------------------------------
# all mode — local only, no VPS/deployment instructions
# ---------------------------------------------------------------------------

def test_all_mode_prints_local_steps_without_deployment_instructions() -> None:
    text = "\n".join(harness.mode_all(_args(run_id="local_run_001")))
    assert "127.0.0.1" in text
    assert "Terminal A" in text
    for forbidden in ("systemd", "nginx", "docker", "Docker", "VPS", "vps", "systemctl"):
        assert forbidden not in text
