from app.config import Settings
from app.services.operator_auth_context import resolve_operator_auth_context
from app.services.operator_run_authorization import resolve_run_authorization


def test_loopback_local_operator_context_does_not_require_browser_token_or_headers(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.db",
        allow_network_bind=False,
        operator_auth_oidc_enabled=False,
        operator_auth_trusted_proxy_enabled=False,
    )

    context = resolve_operator_auth_context(
        trusted_proxy_enabled=settings.operator_auth_trusted_proxy_enabled,
        x_operator_authenticated=None,
        x_operator_id=None,
        x_operator_roles=None,
        x_operator_authorized_runs=None,
        x_request_id="req-local",
        settings=settings,
        authorization=None,
    )

    assert context.actor_id == "local-operator"
    assert context.is_authenticated is True
    assert context.roles == ("operator",)
    assert context.authorized_run_ids == ("*",)
    assert context.request_id == "req-local"


def test_loopback_local_operator_can_open_any_local_run(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.db",
        allow_network_bind=False,
        operator_auth_oidc_enabled=False,
        operator_run_authorizations={},
    )

    result = resolve_run_authorization(settings=settings, actor_id="local-operator", run_id="any-local-run")

    assert result.allowed is True
    assert result.reason == "local_development_allowed"


def test_network_bind_still_requires_real_authorization(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.db",
        allow_network_bind=True,
        operator_auth_oidc_enabled=False,
        operator_run_authorizations={},
    )

    result = resolve_run_authorization(settings=settings, actor_id="local-operator", run_id="any-local-run")

    assert result.allowed is False
    assert result.reason == "actor_not_authorized"
