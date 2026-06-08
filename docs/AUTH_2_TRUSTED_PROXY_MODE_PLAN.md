# Auth-2 — Trusted Proxy Mode / Settings Gate Plan

Date: 2026-06-08
Status: Step 2 complete — trusted-proxy gate enforced
Implementation status: Step 2 gate enforcement complete; integration fail-closed coverage not started

## Purpose

Auth-2 adds a documented plan for a fail-closed settings gate before the app trusts any upstream operator identity headers.

This slice exists to preserve the current local-first default while creating an explicit deployment boundary for future reverse-proxy or controlled operator environments.

## Plain-English Summary

Today, the operator overlay route can read operator context from request headers after Auth-1 centralized that parsing behind one adapter.

Auth-2 does not add a real auth provider. It adds a later implementation plan so the backend will only accept those upstream operator headers when a dedicated trusted-proxy setting is explicitly enabled. When that setting is off, header-based operator context must be treated as untrusted and must fail closed.

## Why Auth-2 Comes After Auth-1

Auth-1 created the stable adapter boundary:

```text
app/services/operator_auth_context.py
```

and moved route-level parsing behind that adapter.

Auth-2 builds on that boundary. The trusted-proxy decision should happen in one place, not inline inside the route. Without Auth-1, Auth-2 would either duplicate parsing logic or reintroduce route-level policy coupling.

## Current State

Current local state after Auth-1:

```text
- Operator header parsing is centralized in app/services/operator_auth_context.py
- app/api/operator_overlays.py calls the adapter and passes the returned fields to the preview service
- Integration tests confirm existing operator overlay behavior
- No real provider integration exists
```

Current trusted headers:

```text
X-Operator-Authenticated
X-Operator-Id
X-Operator-Roles
X-Operator-Authorized-Runs
X-Request-Id
```

Current gap:

```text
The app has no explicit settings gate that decides whether upstream operator headers are trusted in the current runtime mode.
```

## Proposed Trusted Proxy Mode Boundary

Auth-2 should define one explicit backend trust boundary:

```text
Header-based operator context is accepted only when trusted proxy mode is enabled.
```

Proposed behavior:

- Default local-first behavior remains unchanged for general app startup and deployment assumptions.
- Trusted proxy mode is disabled by default.
- When trusted proxy mode is disabled, the operator auth adapter must fail closed for header-based operator identity.
- Failing closed should mean the resulting operator context is treated as unauthenticated or otherwise denied by existing operator-only preview policy.
- No public overlay, public download, or artifact-serving policy change is introduced.

This boundary prepares for a later reverse-proxy deployment where the proxy is responsible for setting trusted identity headers after its own authentication checks.

## Proposed Settings Gate

Primary proposed setting:

```text
operator_auth_trusted_proxy_enabled: bool = False
```

Optional future proposal, only if later implementation needs an extra guard:

```text
operator_auth_trusted_proxy_required_header: str | None = None
```

The optional secondary setting is not required for Auth-2. It is only a possible extension if a later deployment needs one extra proxy-marker header before trusting operator identity headers.

Proposed gate semantics:

- `False`:
  Header-based operator context is not trusted.
- `True`:
  Header-based operator context may be resolved through the Auth-1 adapter.

The plan for later implementation should keep the decision in backend settings and should not rely on frontend behavior.

## Allowed Scope

Later Auth-2 implementation may change only the smallest backend boundary needed to enforce trusted-proxy gating, likely around:

```text
app/config.py
app/services/operator_auth_context.py
app/api/operator_overlays.py
tests/unit/test_operator_auth_context.py
tests/integration/test_operator_overlay_preview_api.py
docs/AUTH_2_TRUSTED_PROXY_MODE_PLAN.md
```

Auth-2 may:

- Add one explicit settings flag for trusted proxy mode.
- Fail closed when trusted proxy mode is disabled.
- Preserve existing route path, response shape, and operator-only preview boundaries.
- Add focused unit and integration coverage for the settings gate.

## Forbidden Scope

Auth-2 must not:

- Add Supabase.
- Add OIDC.
- Add JWT verification.
- Add frontend session handling.
- Add login/logout UI.
- Add a new auth provider dependency.
- Add browser-side token storage.
- Change artifact-serving policy.
- Change public/private exposure behavior.
- Change H3/H4 behavior.
- Change SAR math.
- Change GRID logic.
- Change notebook parity logic.
- Change candidate screening math.
- Commit generated/private artifacts.

Auth-2 is not real provider integration.
Auth-2 is not Supabase.
Auth-2 is not OIDC.
Auth-2 is not JWT verification.
Auth-2 does not add login/logout UI.

## Proposed Implementation Steps

1. Add a new settings field in `app/config.py` for trusted proxy mode with default `False`.
2. Extend the Auth-1 adapter path so the trusted-proxy gate is enforced before header-based operator context is treated as valid.
3. Decide and document the fail-closed behavior when the setting is disabled.
4. Keep `app/api/operator_overlays.py` thin and continue routing through the adapter rather than reintroducing inline checks.
5. Add focused unit tests for trusted-proxy enabled and disabled behavior.
6. Add focused integration coverage that proves operator overlay access is denied when trusted proxy mode is disabled, even if headers are present.
7. Re-run the current Auth-1 integration suite to confirm existing redaction and operator-only behavior remain unchanged.

## Progress Checklist

- [x] Step 1: add `operator_auth_trusted_proxy_enabled` to `Settings` with default `False`
- [x] Step 2: enforce trusted-proxy gate in operator auth context resolution
- [ ] Step 3: add integration coverage for fail-closed behavior when trusted proxy mode is disabled
- [ ] Step 4: confirm post-gate operator overlay behavior remains redacted and operator-only

## Expected Changed Files for Later Implementation

Expected implementation-time files:

```text
app/config.py
app/services/operator_auth_context.py
app/api/operator_overlays.py
tests/unit/test_operator_auth_context.py
tests/integration/test_operator_overlay_preview_api.py
docs/AUTH_2_TRUSTED_PROXY_MODE_PLAN.md
```

These are proposals for the later implementation slice only. Auth-2 planning does not modify them now.

## Validation Commands

Recommended commands for the later implementation slice:

```bash
uv run python -m pytest tests/unit/test_operator_auth_context.py -v
uv run python -m pytest tests/integration/test_operator_overlay_preview_api.py -v
uv run python -m pytest tests/unit/test_operator_auth_context.py tests/integration/test_operator_overlay_preview_api.py -v
git status --short
git diff --stat
```

## Acceptance Criteria

Auth-2 should be accepted only if all are true in the later implementation slice:

- A trusted-proxy settings flag exists and defaults to `False`.
- Header-based operator identity is not trusted when trusted proxy mode is disabled.
- The route still goes through `resolve_operator_auth_context(...)`.
- Operator-only preview requests fail closed when the trusted-proxy gate is off.
- Existing operator overlay response shape remains unchanged.
- Existing redaction behavior remains unchanged.
- No public overlay or artifact-serving behavior changes are introduced.
- No frontend changes are required.
- No Supabase/OIDC/JWT/provider dependency is added.
- No H3/H4/SAR/GRID/notebook parity/screening math behavior changes are introduced.

## Rollback Plan

If the later Auth-2 implementation causes regressions:

1. Revert the trusted-proxy settings gate changes in the small implementation commit.
2. Restore the prior Auth-1-only adapter behavior.
3. Re-run the focused unit and integration tests for operator auth context and operator overlay preview.
4. Leave real provider integration blocked until a smaller or clearer Auth-2 implementation is approved.

## Codex Goal for Later Implementation

Use a later scoped goal in this shape:

```text
/goal Auth-2 implementation only — trusted proxy mode / settings gate

Repo / branch / sync rules
MUST READ FIRST
SCOPE
Required behavior
Allowed files
Validation commands
Before commit checks
Commit message
Final report requirements
```

The later implementation goal should require:

- default-off trusted proxy mode
- fail-closed behavior when disabled
- no provider integration
- no frontend changes
- no artifact-serving or exposure changes
