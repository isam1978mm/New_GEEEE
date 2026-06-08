from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any

import jwt
from jwt.algorithms import RSAAlgorithm

from app.config import Settings

_VERIFIED = "verified"
_OIDC_DISABLED = "oidc_disabled"
_MISSING_TOKEN = "missing_token"
_MISSING_ISSUER = "missing_issuer"
_MISSING_CLIENT_ID = "missing_client_id"
_MISSING_JWKS_URI = "missing_jwks_uri"
_MISSING_SUBJECT = "missing_subject"
_INVALID_TOKEN = "invalid_token"


@dataclass(frozen=True)
class TokenVerificationResult:
    verified: bool
    actor_id: str | None
    roles: tuple[str, ...]
    reason: str


def verify_operator_token(
    *,
    token: str | None,
    settings: Settings,
) -> TokenVerificationResult:
    """Verify a Generic OIDC JWT and extract operator identity.

    Fails closed on any error. Does not log or return raw token values.
    """
    if not settings.operator_auth_oidc_enabled:
        return _denied(_OIDC_DISABLED)

    if not token or not token.strip():
        return _denied(_MISSING_TOKEN)

    if not settings.operator_auth_oidc_issuer_url:
        return _denied(_MISSING_ISSUER)

    if not settings.operator_auth_oidc_client_id:
        return _denied(_MISSING_CLIENT_ID)

    if not settings.operator_auth_oidc_jwks_uri:
        return _denied(_MISSING_JWKS_URI)

    try:
        public_key = _resolve_signing_key(token, settings.operator_auth_oidc_jwks_uri)
        claims: dict[str, Any] = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.operator_auth_oidc_client_id,
            issuer=settings.operator_auth_oidc_issuer_url,
        )
    except Exception:
        return _denied(_INVALID_TOKEN)

    sub = claims.get("sub")
    if not sub or not isinstance(sub, str) or not sub.strip():
        return _denied(_MISSING_SUBJECT)

    return TokenVerificationResult(
        verified=True,
        actor_id=sub.strip(),
        roles=_extract_roles(claims),
        reason=_VERIFIED,
    )


def _resolve_signing_key(token: str, jwks_uri: str) -> Any:
    jwks_data = _fetch_jwks(jwks_uri)
    keys = jwks_data.get("keys", [])

    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except Exception:
        kid = None

    matching = [k for k in keys if not kid or k.get("kid") == kid]
    if not matching:
        matching = keys
    if not matching:
        raise ValueError("no_signing_key_found")

    return RSAAlgorithm.from_jwk(json.dumps(matching[0]))


def _fetch_jwks(jwks_uri: str) -> dict[str, Any]:
    with urllib.request.urlopen(jwks_uri, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _extract_roles(claims: dict[str, Any]) -> tuple[str, ...]:
    raw: list[str] = []
    for key in ("roles", "role"):
        value = claims.get(key)
        if isinstance(value, list):
            raw = [str(v) for v in value]
            break
        if isinstance(value, str):
            raw = [value]
            break

    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return tuple(result)


def _denied(reason: str) -> TokenVerificationResult:
    return TokenVerificationResult(verified=False, actor_id=None, roles=(), reason=reason)


__all__ = (
    "TokenVerificationResult",
    "verify_operator_token",
)
