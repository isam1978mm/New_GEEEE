"""Static contract tests for the local operator session shell."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_COMPONENTS = _ROOT / "frontend-v2" / "src" / "app" / "components"
_SESSION_SHELL = _COMPONENTS / "OperatorSessionShell.tsx"
_SESSION_CONTEXT = _COMPONENTS / "OperatorSessionContext.tsx"
_PRIVATE_PANEL = _COMPONENTS / "OperatorPrivateOverlayPanel.tsx"
_MAIN = _ROOT / "frontend-v2" / "src" / "main.tsx"


def _read(path: Path) -> str:
    assert path.exists(), f"expected file missing: {path}"
    return path.read_text(encoding="utf-8")


def test_operator_session_shell_exists_and_is_local_only() -> None:
    text = _read(_SESSION_SHELL)
    assert "Local operator session" in text
    assert "onStartSession" in text
    assert "onEndSession" in text
    assert "useState" in text


def test_operator_session_shell_has_no_browser_persistence() -> None:
    text = _read(_SESSION_SHELL)
    for term in ("localStorage", "sessionStorage", "document.cookie"):
        assert term not in text


def test_operator_session_shell_adds_no_provider_sdk_terms() -> None:
    lowered = _read(_SESSION_SHELL).lower()
    for term in ("supabase", "auth0", "keycloak", "clerk", "firebase", "cognito", "msal"):
        assert term not in lowered


def test_operator_session_context_wraps_children_and_exposes_value() -> None:
    text = _read(_SESSION_CONTEXT)
    assert "OperatorSessionProvider" in text
    assert "OperatorSessionContext.Provider" in text
    assert "useOperatorAccessToken" in text
    assert "OperatorSessionShell" in text


def test_main_mounts_operator_session_provider() -> None:
    text = _read(_MAIN)
    assert "OperatorSessionProvider" in text
    assert "<OperatorSessionProvider>" in text
    assert "<App />" in text


def test_private_overlay_panel_reads_session_context() -> None:
    text = _read(_PRIVATE_PANEL)
    assert "useOperatorAccessToken" in text
    assert "contextOperatorAccessToken" in text
    assert "resolvedOperatorAccessToken" in text
    assert "accessToken: resolvedOperatorAccessToken" in text


def test_private_overlay_panel_keeps_existing_optional_prop_contract() -> None:
    text = _read(_PRIVATE_PANEL)
    assert "operatorAccessToken?: string | null" in text
    assert "operatorAccessToken" in text


def test_session_files_do_not_add_public_overlay_or_download_terms() -> None:
    combined = _read(_SESSION_SHELL) + "\n" + _read(_SESSION_CONTEXT)
    lowered = combined.lower()
    for term in ("public overlay", "download", "geometry", "coordinates"):
        assert term not in lowered
