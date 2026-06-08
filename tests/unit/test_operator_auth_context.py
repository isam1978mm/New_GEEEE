from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.operator_auth_context import OperatorAuthContext, resolve_operator_auth_context


def _resolve(
    *,
    x_operator_authenticated: str | None = None,
    x_operator_id: str | None = None,
    x_operator_roles: str | None = None,
    x_operator_authorized_runs: str | None = None,
    x_request_id: str | None = None,
) -> OperatorAuthContext:
    return resolve_operator_auth_context(
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


def test_operator_auth_context_is_frozen() -> None:
    context = _resolve(x_operator_id="operator-1")

    with pytest.raises(FrozenInstanceError):
        context.actor_id = "operator-2"
