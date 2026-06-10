"""
LOCAL-2 — static contract tests for the local operator UI token handoff path.

These tests read the existing frontend source as text and enforce the contract:

  caller-provided operatorAccessToken
    -> OperatorPrivateOverlayPanel
      -> getOperatorPrivateOverlayPreview(runId, family, { accessToken })
        -> Authorization: Bearer <trimmed token>  (only when nonblank)

They also enforce the negative boundary: no token storage, no login/logout UI,
no Supabase, and no auth provider SDK. No frontend test framework is required.
"""
from __future__ import annotations

import re
from pathlib import Path

_FRONTEND = Path(__file__).parent.parent.parent / "frontend-v2" / "src" / "app"
_API_FILE = _FRONTEND / "api" / "operatorOverlays.ts"
_PANEL_FILE = _FRONTEND / "components" / "OperatorPrivateOverlayPanel.tsx"

# Terms forbidden anywhere in the handoff path.
_FORBIDDEN_STORAGE = ("localStorage", "sessionStorage", "document.cookie")
_FORBIDDEN_PROVIDER_SDK = (
    "supabase",
    "auth0",
    "keycloak",
    "clerk",
    "firebase",
    "cognito",
    "msal",
)
_FORBIDDEN_LOGIN_WORDS = ("login", "logout", "signin", "sign-in", "signout", "sign-out")


def _read(path: Path) -> str:
    assert path.exists(), f"expected frontend file missing: {path}"
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace so assertions tolerate formatting differences."""
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# operatorOverlays.ts — API helper contract
# ---------------------------------------------------------------------------

def test_api_helper_accepts_optional_access_token_options() -> None:
    text = _norm(_read(_API_FILE))
    # getOperatorPrivateOverlayPreview signature includes an options param with accessToken.
    assert "getOperatorPrivateOverlayPreview" in text
    assert re.search(r"options\??\s*:\s*\{[^}]*accessToken", text), \
        "expected options param exposing accessToken"


def test_api_helper_access_token_supports_string_or_null() -> None:
    text = _norm(_read(_API_FILE))
    assert re.search(r"accessToken\??\s*:\s*string\s*\|\s*null", text), \
        "expected accessToken?: string | null shape"


def test_api_helper_trims_token_before_use() -> None:
    text = _norm(_read(_API_FILE))
    # Token is trimmed (e.g. (options?.accessToken ?? "").trim()).
    assert ".trim()" in text
    assert "accessToken" in text


def test_api_helper_sets_bearer_only_when_nonblank() -> None:
    text = _norm(_read(_API_FILE))
    # A Bearer header is constructed from the trimmed token.
    assert re.search(r"Authorization.{0,20}Bearer\s*\$\{?\s*trimmedToken", text) or \
        re.search(r"Bearer\s*\$\{trimmedToken\}", text), \
        "expected Authorization: Bearer <trimmedToken>"
    # The header is set inside a conditional guarded by the trimmed token.
    assert re.search(r"if\s*\(\s*trimmedToken\s*\)", text), \
        "expected Authorization to be set only when token is nonblank"


def test_api_helper_blank_token_path_has_no_authorization() -> None:
    text = _read(_API_FILE)
    # fetchOptions starts empty; Authorization is only added inside the guard.
    # Confirm there is no unconditional Authorization assignment.
    unconditional = re.findall(r"^\s*Authorization\s*:", text, flags=re.MULTILINE)
    # Any Authorization literal must appear within the guarded headers object,
    # not as a standalone unconditional statement.
    assert "fetchOptions" in text
    assert len(unconditional) == 0, "Authorization must not be set unconditionally"


def test_api_helper_calls_operator_private_overlay_endpoint() -> None:
    text = _norm(_read(_API_FILE))
    assert "fetch(" in text
    assert "/operator/private-overlays" in text


def test_api_helper_has_no_storage_or_provider_or_login() -> None:
    text = _read(_API_FILE)
    lowered = text.lower()
    for term in _FORBIDDEN_STORAGE:
        assert term not in text, f"forbidden storage usage in API helper: {term}"
    for term in _FORBIDDEN_PROVIDER_SDK:
        assert term not in lowered, f"forbidden provider SDK reference in API helper: {term}"
    for term in _FORBIDDEN_LOGIN_WORDS:
        assert term not in lowered, f"forbidden login/logout wording in API helper: {term}"


# ---------------------------------------------------------------------------
# OperatorPrivateOverlayPanel.tsx — component contract
# ---------------------------------------------------------------------------

def test_panel_props_include_operator_access_token() -> None:
    text = _norm(_read(_PANEL_FILE))
    assert re.search(r"operatorAccessToken\??\s*:\s*string\s*\|\s*null", text), \
        "expected operatorAccessToken?: string | null prop"


def test_panel_passes_access_token_to_api_helper() -> None:
    text = _norm(_read(_PANEL_FILE))
    assert re.search(
        r"getOperatorPrivateOverlayPreview\([^)]*\{\s*accessToken\s*:\s*resolvedOperatorAccessToken\s*\}",
        text,
    ), "expected panel to call helper with { accessToken: resolvedOperatorAccessToken }"


def test_panel_includes_access_token_in_effect_dependencies() -> None:
    text = _norm(_read(_PANEL_FILE))
    # The useEffect dependency array must list resolvedOperatorAccessToken.
    dep_arrays = re.findall(r"\}\s*,\s*\[([^\]]*)\]\s*\)", text)
    assert any("resolvedOperatorAccessToken" in dep for dep in dep_arrays), \
        "expected resolvedOperatorAccessToken in the effect dependency list"


def test_panel_has_no_storage_or_provider_or_login() -> None:
    text = _read(_PANEL_FILE)
    lowered = text.lower()
    for term in _FORBIDDEN_STORAGE:
        assert term not in text, f"forbidden storage usage in panel: {term}"
    for term in _FORBIDDEN_PROVIDER_SDK:
        assert term not in lowered, f"forbidden provider SDK reference in panel: {term}"
    for term in _FORBIDDEN_LOGIN_WORDS:
        assert term not in lowered, f"forbidden login/logout wording in panel: {term}"


# ---------------------------------------------------------------------------
# Cross-file boundary
# ---------------------------------------------------------------------------

def test_no_token_persistence_helper_or_auth_state_across_handoff_files() -> None:
    combined = (_read(_API_FILE) + "\n" + _read(_PANEL_FILE))
    lowered = combined.lower()
    # No persistence helper / store wording.
    for term in ("savetoken", "persisttoken", "tokenstore", "tokenstorage", "authstore", "authprovider"):
        assert term not in lowered.replace("_", ""), f"forbidden token persistence/auth-state term: {term}"
    # No storage APIs anywhere in the handoff path.
    for term in _FORBIDDEN_STORAGE:
        assert term not in combined, f"forbidden storage usage across handoff files: {term}"
