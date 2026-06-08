from __future__ import annotations

import pytest

from app.config import Settings
from app.services.operator_run_authorization import (
    OperatorRunAuthorizationResult,
    resolve_run_authorization,
)


def _make_settings(
    authorizations: dict[str, list[str]] | None = None,
) -> Settings:
    return Settings(operator_run_authorizations=authorizations or {})


def test_matching_actor_and_run_returns_allowed() -> None:
    settings = _make_settings(
        {"operator_1": ["run_authorized", "run_review"]}
    )
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_1",
        run_id="run_authorized",
    )
    assert result == OperatorRunAuthorizationResult(allowed=True, reason="authorized")


def test_unknown_actor_returns_denied() -> None:
    settings = _make_settings({"operator_1": ["run_a"]})
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_2",
        run_id="run_a",
    )
    assert result == OperatorRunAuthorizationResult(
        allowed=False, reason="actor_not_authorized"
    )


def test_known_actor_missing_run_returns_denied() -> None:
    settings = _make_settings({"operator_1": ["run_a"]})
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_1",
        run_id="run_b",
    )
    assert result == OperatorRunAuthorizationResult(
        allowed=False, reason="run_not_authorized"
    )


def test_none_actor_returns_denied() -> None:
    settings = _make_settings()
    result = resolve_run_authorization(
        settings=settings,
        actor_id=None,
        run_id="run_a",
    )
    assert result == OperatorRunAuthorizationResult(allowed=False, reason="missing_actor")


def test_blank_actor_returns_denied() -> None:
    settings = _make_settings()
    result = resolve_run_authorization(
        settings=settings,
        actor_id="   ",
        run_id="run_a",
    )
    assert result == OperatorRunAuthorizationResult(allowed=False, reason="missing_actor")


def test_blank_run_id_returns_denied() -> None:
    settings = _make_settings()
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_1",
        run_id="   ",
    )
    assert result == OperatorRunAuthorizationResult(allowed=False, reason="missing_run")


def test_actor_id_and_run_id_are_stripped_before_lookup() -> None:
    settings = _make_settings(
        {"operator_1": ["run_a"]}
    )
    result = resolve_run_authorization(
        settings=settings,
        actor_id="  operator_1  ",
        run_id="  run_a  ",
    )
    assert result == OperatorRunAuthorizationResult(allowed=True, reason="authorized")


def test_actor_with_empty_run_list_returns_denied() -> None:
    settings = _make_settings({"operator_1": []})
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_1",
        run_id="run_a",
    )
    assert result == OperatorRunAuthorizationResult(
        allowed=False, reason="run_not_authorized"
    )


def test_default_empty_settings_fail_closed() -> None:
    settings = Settings()
    result = resolve_run_authorization(
        settings=settings,
        actor_id="operator_1",
        run_id="run_a",
    )
    assert result == OperatorRunAuthorizationResult(
        allowed=False, reason="actor_not_authorized"
    )
