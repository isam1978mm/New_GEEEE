from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.services.operator_token_verifier import (
    TokenVerificationResult,
    verify_operator_token,
)

_FAKE_TOKEN = "fake.token.value"
_FAKE_JWKS = {
    "keys": [{"kty": "RSA", "kid": "key-1", "use": "sig", "alg": "RS256", "n": "abc", "e": "AQAB"}]
}
_BASE_CLAIMS = {
    "sub": "operator-abc",
    "iss": "https://issuer.example.test",
    "aud": "gee-operator-ui",
    "roles": ["operator"],
}


def _oidc_settings(**overrides: object) -> Settings:
    base: dict[str, object] = dict(
        operator_auth_oidc_enabled=True,
        operator_auth_oidc_issuer_url="https://issuer.example.test",
        operator_auth_oidc_client_id="gee-operator-ui",
        operator_auth_oidc_jwks_uri="https://issuer.example.test/.well-known/jwks.json",
    )
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Fail-closed gates — no network or crypto needed
# ---------------------------------------------------------------------------

def test_oidc_disabled_fails_closed() -> None:
    settings = Settings(operator_auth_oidc_enabled=False)
    result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(verified=False, actor_id=None, roles=(), reason="oidc_disabled")


@pytest.mark.parametrize("bad_token", [None, "", "   "])
def test_missing_token_fails_closed(bad_token: str | None) -> None:
    settings = _oidc_settings()
    result = verify_operator_token(token=bad_token, settings=settings)
    assert result == TokenVerificationResult(verified=False, actor_id=None, roles=(), reason="missing_token")


def test_missing_issuer_fails_closed() -> None:
    settings = _oidc_settings(operator_auth_oidc_issuer_url=None)
    result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(verified=False, actor_id=None, roles=(), reason="missing_issuer")


def test_missing_client_id_fails_closed() -> None:
    settings = _oidc_settings(operator_auth_oidc_client_id=None)
    result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(verified=False, actor_id=None, roles=(), reason="missing_client_id")


def test_missing_jwks_uri_fails_closed() -> None:
    settings = _oidc_settings(operator_auth_oidc_jwks_uri=None)
    result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(verified=False, actor_id=None, roles=(), reason="missing_jwks_uri")


# ---------------------------------------------------------------------------
# Successful verification — JWKS fetch + decode mocked, no network
# ---------------------------------------------------------------------------

def test_successful_token_returns_actor_and_roles() -> None:
    settings = _oidc_settings()
    claims = {**_BASE_CLAIMS, "roles": ["operator", "admin"]}
    fake_key = MagicMock()
    with (
        patch("app.services.operator_token_verifier._fetch_jwks", return_value=_FAKE_JWKS),
        patch("app.services.operator_token_verifier.RSAAlgorithm.from_jwk", return_value=fake_key),
        patch("app.services.operator_token_verifier.jwt.decode", return_value=claims),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result.verified is True
    assert result.actor_id == "operator-abc"
    assert result.roles == ("operator", "admin")
    assert result.reason == "verified"


def test_string_role_is_normalized() -> None:
    settings = _oidc_settings()
    claims = {**_BASE_CLAIMS, "roles": None, "role": "  operator  "}
    fake_key = MagicMock()
    with (
        patch("app.services.operator_token_verifier._fetch_jwks", return_value=_FAKE_JWKS),
        patch("app.services.operator_token_verifier.RSAAlgorithm.from_jwk", return_value=fake_key),
        patch("app.services.operator_token_verifier.jwt.decode", return_value=claims),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result.roles == ("operator",)


def test_duplicate_and_blank_roles_are_removed() -> None:
    settings = _oidc_settings()
    claims = {**_BASE_CLAIMS, "roles": ["operator", "  ", "operator", "admin"]}
    fake_key = MagicMock()
    with (
        patch("app.services.operator_token_verifier._fetch_jwks", return_value=_FAKE_JWKS),
        patch("app.services.operator_token_verifier.RSAAlgorithm.from_jwk", return_value=fake_key),
        patch("app.services.operator_token_verifier.jwt.decode", return_value=claims),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result.roles == ("operator", "admin")


# ---------------------------------------------------------------------------
# Missing subject
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sub_value", [None, "", "   ", 42])
def test_missing_subject_fails_closed(sub_value: object) -> None:
    settings = _oidc_settings()
    claims: dict[str, object] = {k: v for k, v in _BASE_CLAIMS.items() if k != "sub"}
    if sub_value is not None:
        claims["sub"] = sub_value
    fake_key = MagicMock()
    with (
        patch("app.services.operator_token_verifier._fetch_jwks", return_value=_FAKE_JWKS),
        patch("app.services.operator_token_verifier.RSAAlgorithm.from_jwk", return_value=fake_key),
        patch("app.services.operator_token_verifier.jwt.decode", return_value=claims),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(
        verified=False, actor_id=None, roles=(), reason="missing_subject"
    ), f"sub={sub_value!r}"


# ---------------------------------------------------------------------------
# Decode / JWKS failure
# ---------------------------------------------------------------------------

def test_decode_or_jwks_failure_fails_closed_without_raw_error() -> None:
    settings = _oidc_settings()
    with patch(
        "app.services.operator_token_verifier._fetch_jwks",
        side_effect=OSError("network unreachable"),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(
        verified=False, actor_id=None, roles=(), reason="invalid_token"
    )
    assert "network unreachable" not in result.reason


def test_expired_token_fails_closed() -> None:
    import jwt as pyjwt

    settings = _oidc_settings()
    fake_key = MagicMock()
    with (
        patch("app.services.operator_token_verifier._fetch_jwks", return_value=_FAKE_JWKS),
        patch("app.services.operator_token_verifier.RSAAlgorithm.from_jwk", return_value=fake_key),
        patch(
            "app.services.operator_token_verifier.jwt.decode",
            side_effect=pyjwt.ExpiredSignatureError("token is expired"),
        ),
    ):
        result = verify_operator_token(token=_FAKE_TOKEN, settings=settings)
    assert result == TokenVerificationResult(
        verified=False, actor_id=None, roles=(), reason="invalid_token"
    )
