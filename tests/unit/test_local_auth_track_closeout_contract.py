"""
LOCAL-3 — static contract tests protecting the local auth track closeout.

Read docs and source as text (and check file paths) to freeze the local-only
auth track boundaries: Auth-1..Auth-5 closed, Deploy-1 prepared-only, Local-1,
Local-2, Local-3 closed; no token storage / provider SDK in the frontend handoff;
no active VPS deployment automation in the repo.
"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_DOCS = _ROOT / "docs"
_FRONTEND = _ROOT / "frontend-v2" / "src" / "app"
_API_FILE = _FRONTEND / "api" / "operatorOverlays.ts"
_PANEL_FILE = _FRONTEND / "components" / "OperatorPrivateOverlayPanel.tsx"

_LOCAL_1 = _DOCS / "LOCAL_1_OIDC_DEV_HARNESS.md"
_LOCAL_2 = _DOCS / "LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md"
_LOCAL_3 = _DOCS / "LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md"
_DEPLOY_1 = _DOCS / "DEPLOY_1_OIDC_SERVER_ACTIVATION_RUNBOOK.md"
_README = _ROOT / "README.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected file missing: {path}"
    return path.read_text(encoding="utf-8")


def _lower(path: Path) -> str:
    return _read(path).lower()


# ---------------------------------------------------------------------------
# Prior local milestones still closed
# ---------------------------------------------------------------------------

def test_local_1_doc_exists_and_says_complete() -> None:
    assert "local-1 complete" in _lower(_LOCAL_1)


def test_local_2_doc_exists_and_says_complete() -> None:
    assert "local-2 complete" in _lower(_LOCAL_2)


def test_deploy_1_says_prepared_reference_only_not_executed() -> None:
    text = _lower(_DEPLOY_1)
    assert "prepared reference only" in text
    assert "not executed" in text


def test_readme_is_local_first_and_mentions_local_1_and_local_2() -> None:
    text = _lower(_README)
    assert "local-first" in text
    assert "local_1_oidc_dev_harness.md" in text
    assert "local_2_operator_ui_token_handoff.md" in text


# ---------------------------------------------------------------------------
# LOCAL-3 closeout doc content
# ---------------------------------------------------------------------------

def test_local_3_doc_exists_and_says_complete() -> None:
    assert "local-3 complete" in _lower(_LOCAL_3)


def test_local_3_says_vps_is_future_not_started() -> None:
    text = _lower(_LOCAL_3)
    assert "vps" in text
    assert "not started" in text


def test_local_3_says_no_login_ui_and_no_token_storage() -> None:
    text = _lower(_LOCAL_3)
    assert "no login ui" in text or "no login/logout ui" in text
    assert "no token storage" in text


def test_local_3_says_auth3_remains_final_run_gate() -> None:
    assert "final run gate" in _lower(_LOCAL_3)


def test_local_3_lists_all_milestones() -> None:
    text = _lower(_LOCAL_3)
    for milestone in ("auth-1", "auth-2", "auth-3", "auth-4", "auth-5",
                      "deploy-1", "local-1", "local-2", "local-3"):
        assert milestone in text, f"LOCAL-3 doc missing milestone: {milestone}"


def test_local_3_readme_pointer_present() -> None:
    text = _lower(_README)
    assert "local_3_full_auth_regression_closeout.md" in text


# ---------------------------------------------------------------------------
# Frontend handoff boundary still holds
# ---------------------------------------------------------------------------

def test_frontend_handoff_files_have_no_storage_or_provider_sdk() -> None:
    combined = _read(_API_FILE) + "\n" + _read(_PANEL_FILE)
    lowered = combined.lower()
    for term in ("localStorage", "sessionStorage", "document.cookie"):
        assert term not in combined, f"forbidden storage usage in handoff files: {term}"
    for term in ("supabase", "auth0", "keycloak", "clerk", "firebase", "cognito", "msal"):
        assert term not in lowered, f"forbidden provider SDK reference in handoff files: {term}"


# ---------------------------------------------------------------------------
# Backend auth files still present (boundary intact)
# ---------------------------------------------------------------------------

def test_backend_auth_files_exist() -> None:
    for rel in (
        "app/services/operator_auth_context.py",
        "app/services/operator_token_verifier.py",
        "app/services/operator_run_authorization.py",
        "app/api/operator_overlays.py",
    ):
        assert (_ROOT / rel).exists(), f"expected backend auth file missing: {rel}"


# ---------------------------------------------------------------------------
# No active VPS / deployment automation (path checks, not text grep)
# ---------------------------------------------------------------------------

def test_no_dockerfile_present() -> None:
    assert not (_ROOT / "Dockerfile").exists()
    assert not (_ROOT / "Dockerfile.prod").exists()


def test_no_docker_compose_present() -> None:
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        assert not (_ROOT / name).exists(), f"unexpected compose file: {name}"


def test_no_deploy_vps_dir_present() -> None:
    assert not (_ROOT / "deploy" / "vps").exists()


def test_no_systemd_or_nginx_config_files_present() -> None:
    # Path-based: no *.service (systemd) or nginx config files anywhere in the tree,
    # excluding dependency/build dirs.
    skip_dirs = {".venv", "node_modules", ".git", "dist", "__pycache__"}

    def _iter(root: Path):
        for p in root.rglob("*"):
            if any(part in skip_dirs for part in p.parts):
                continue
            yield p

    for path in _iter(_ROOT):
        if path.is_file():
            name = path.name.lower()
            assert not name.endswith(".service"), f"unexpected systemd unit: {path}"
            assert name != "nginx.conf", f"unexpected nginx config: {path}"
            assert not (name.startswith("nginx") and name.endswith(".conf")), \
                f"unexpected nginx config: {path}"
