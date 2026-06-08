from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest

from app.config import Settings
from app.services.operator_auth_context import OperatorAuthContext, resolve_operator_auth_context
from app.services.operator_token_verifier import TokenVerificationResult


def _resolve(
    *,
    trusted_proxy_enabled: bool = True,
    x_operator_authenticated: str | None = None,
    x_operator_id: str | None = None,
    x_operator_roles: str | None = None,
    x_operator_authorized_runs: str | None = None,
    x_request_id: str | None = None,
) -> OperatorAuthContext:
    return resolve_operator_auth_context(
        trusted_proxy_enabled=trusted_proxy_enabled,
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
    )


def test_authenticated_true_parsing() -> None:
    assert _resolve(x_operator_authenticated=" true ").is_authenticated is True
    assert _resolve(x_operator_authenticated="TRUE").is_authenticated is True


@pytest.mark.parametrize("value", [None, "", "false", "yes"])
def test_non_true_values_parse_as_unauthenticated(value: str | None) -> None:
    assert _resolve(x_operator_authenticated=value).is_authenticated is False


def test_actor_id_trimming_and_empty_to_none_behavior() -> None:
    assert _resolve(x_operator_id=" operator-1 ").actor_id == "operator-1"
    assert _resolve(x_operator_id="").actor_id is None
    assert _resolve(x_operator_id="   ").actor_id is None
    assert _resolve(x_operator_id=None).actor_id is None


def test_roles_trimming_comma_splitting_and_empty_removal() -> None:
    assert _resolve(x_operator_roles="operator, admin, ,").roles == ("operator", "admin")
    assert _resolve(x_operator_roles="").roles == ()
    assert _resolve(x_operator_roles=None).roles == ()


def test_authorized_run_ids_trimming_comma_splitting_and_empty_removal() -> None:
    assert _resolve(x_operator_authorized_runs="run-a, run-b, ,").authorized_run_ids == (
        "run-a",
        "run-b",
    )
    assert _resolve(x_operator_authorized_runs="").authorized_run_ids == ()
    assert _resolve(x_operator_authorized_runs=None).authorized_run_ids == ()


def test_request_id_preservation_when_provided() -> None:
    assert _resolve(x_request_id=" req-test ").request_id == "req-test"


def test_request_id_fallback_when_missing_or_blank() -> None:
    missing = _resolve(x_request_id=None)
    blank = _resolve(x_request_id="   ")

    assert missing.request_id.startswith("req_")
    assert blank.request_id.startswith("req_")
    assert missing.request_id != blank.request_id


def test_resolver_returns_immutable_tuple_fields() -> None:
    context = _resolve(
        x_operator_roles="operator,admin",
        x_operator_authorized_runs="run-a,run-b",
    )

    assert isinstance(context.roles, tuple)
    assert isinstance(context.authorized_run_ids, tuple)


def test_trusted_proxy_disabled_fails_closed_even_with_truthy_headers() -> None:
    context = _resolve(
        trusted_proxy_enabled=False,
        x_operator_authenticated="true",
        x_operator_id="operator-1",
        x_operator_roles="operator,admin",
        x_operator_authorized_runs="run-a,run-b",
        x_request_id="req-test",
    )

    assert context.actor_id is None
    assert context.is_authenticated is False
    assert context.roles == ()
    assert context.authorized_run_ids == ()
    assert context.request_id.startswith("req_")
    assert context.request_id != "req-test"


def test_trusted_proxy_enabled_preserves_existing_parsing_behavior() -> None:
    context = _resolve(
        trusted_proxy_enabled=True,
        x_operator_authenticated=" true ",
        x_operator_id=" operator-1 ",
        x_operator_roles="operator, admin, ,",
        x_operator_authorized_runs="run-a, run-b, ,",
        x_request_id=" req-test ",
    )

    assert context.actor_id == "operator-1"
    assert context.is_authenticated is True
    assert context.roles == ("operator", "admin")
    assert context.authorized_run_ids == ("run-a", "run-b")
    assert context.request_id == "req-test"


def test_operator_auth_context_is_frozen() -> None:
    context = _resolve(x_operator_id="operator-1")

    with pytest.raises(FrozenInstanceError):
        context.actor_id = "operator-2"


# ---------------------------------------------------------------------------
# OIDC wiring tests — mock verify_operator_token, no real JWT operations
# ---------------------------------------------------------------------------

_OIDC_SETTINGS = Settings(
    operator_auth_oidc_enabled=True,
    operator_auth_oidc_issuer_url="https://issuer.example.test",
    operator_auth_oidc_client_id="gee-operator-ui",
    operator_auth_oidc_jwks_uri="https://issuer.example.test/.well-known/jwks.json",
)

_OIDC_DISABLED_SETTINGS = Settings(operator_auth_oidc_enabled=False)

_VERIFIED = TokenVerificationResult(
    verified=True, actor_id="operator-abc", roles=("operator",), reason="verified"
)

_DENIED = TokenVerificationResult(
    verified=False, actor_id=None, roles=(), reason="invalid_token"
)

_PATCH = "app.services.operator_auth_context.verify_operator_token"


def test_oidc_disabled_preserves_trusted_proxy_behavior() -> None:
    context = resolve_operator_auth_context(
        trusted_proxy_enabled=True,
        x_operator_authenticated="true",
        x_operator_id="operator-1",
        x_operator_roles="operator",
        x_operator_authorized_runs="run-a",
        x_request_id="req-test",
        settings=_OIDC_DISABLED_SETTINGS,
        authorization="Bearer fake.token",
    )
    assert context.actor_id == "operator-1"
    assert context.is_authenticated is True
    assert context.roles == ("operator",)
    assert context.authorized_run_ids == ("run-a",)
    assert context.request_id == "req-test"


def test_oidc_enabled_verified_token_populates_context() -> None:
    with patch(_PATCH, return_value=_VERIFIED):
        context = resolve_operator_auth_context(
            trusted_proxy_enabled=True,
            x_operator_authenticated=None,
            x_operator_id=None,
            x_operator_roles=None,
            x_operator_authorized_runs=None,
            x_request_id="req-test",
            settings=_OIDC_SETTINGS,
            authorization="Bearer fake.token.value",
        )
    assert context.actor_id == "operator-abc"
    assert context.is_authenticated is True
    assert context.roles == ("operator",)
    assert context.authorized_run_ids == ()
    assert context.request_id == "req-test"


def test_oidc_enabled_verified_token_ignores_conflicting_x_operator_headers() -> None:
    with patch(_PATCH, return_value=_VERIFIED):
        context = resolve_operator_auth_context(
            trusted_proxy_enabled=True,
            x_operator_authenticated="true",
            x_operator_id="evil-actor",
            x_operator_roles="admin",
            x_operator_authorized_runs="run-secret",
            x_request_id=None,
            settings=_OIDC_SETTINGS,
            authorization="Bearer fake.token.value",
        )
    assert context.actor_id == "operator-abc"
    assert context.is_authenticated is True
    assert context.roles == ("operator",)
    assert context.authorized_run_ids == ()


def test_oidc_enabled_failed_verification_fails_closed_even_with_truthy_headers() -> None:
    with patch(_PATCH, return_value=_DENIED):
        context = resolve_operator_auth_context(
            trusted_proxy_enabled=True,
            x_operator_authenticated="true",
            x_operator_id="operator-1",
            x_operator_roles="operator",
            x_operator_authorized_runs="run-a",
            x_request_id="req-from-header",
            settings=_OIDC_SETTINGS,
            authorization="Bearer bad.token",
        )
    assert context.actor_id is None
    assert context.is_authenticated is False
    assert context.roles == ()
    assert context.authorized_run_ids == ()
    assert context.request_id.startswith("req_")
    assert context.request_id != "req-from-header"


def test_oidc_enabled_bearer_token_extracted_without_prefix() -> None:
    with patch(_PATCH, return_value=_DENIED) as mock_verify:
        resolve_operator_auth_context(
            trusted_proxy_enabled=True,
            x_operator_authenticated=None,
            x_operator_id=None,
            x_operator_roles=None,
            x_operator_authorized_runs=None,
            x_request_id=None,
            settings=_OIDC_SETTINGS,
            authorization="Bearer   my.token.value  ",
        )
    assert mock_verify.call_args.kwargs["token"] == "my.token.value"


def test_oidc_enabled_non_bearer_authorization_passes_none_token() -> None:
    for bad_auth in ("Basic abc123", "Token abc123", "abc123", None, "", "   "):
        with patch(_PATCH, return_value=_DENIED) as mock_verify:
            resolve_operator_auth_context(
                trusted_proxy_enabled=True,
                x_operator_authenticated=None,
                x_operator_id=None,
                x_operator_roles=None,
                x_operator_authorized_runs=None,
                x_request_id=None,
                settings=_OIDC_SETTINGS,
                authorization=bad_auth,
            )
        passed = mock_verify.call_args.kwargs["token"]
        assert passed is None, f"Expected None for authorization={bad_auth!r}, got {passed!r}"


def test_oidc_enabled_verified_token_authenticates_regardless_of_trusted_proxy_flag() -> None:
    with patch(_PATCH, return_value=_VERIFIED):
        context = resolve_operator_auth_context(
            trusted_proxy_enabled=False,
            x_operator_authenticated=None,
            x_operator_id=None,
            x_operator_roles=None,
            x_operator_authorized_runs=None,
            x_request_id=None,
            settings=_OIDC_SETTINGS,
            authorization="Bearer fake.token.value",
        )
    assert context.actor_id == "operator-abc"
    assert context.is_authenticated is True
    assert context.roles == ("operator",)
    assert context.authorized_run_ids == ()
