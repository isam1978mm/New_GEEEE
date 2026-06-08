# Auth-1 — Operator Auth Context Adapter Plan

Date: 2026-06-07
Status: Proposed planning document only
Implementation status: Not started

## 1. Purpose

Auth-1 creates a small backend adapter that centralizes the current operator identity parsing for private overlay preview requests.

The goal is not to add a real authentication provider. The goal is to stop the route from parsing `X-Operator-*` headers directly and instead call one backend adapter that returns a stable operator auth context object.

## 2. Plain-English Summary

Today, the operator private overlay route reads trusted operator headers directly.

After Auth-1, the route should ask one backend helper:

```text
Who is this operator for this request?
```

The helper returns:

```text
actor_id
is_authenticated
roles
authorized_run_ids
request_id
```

The route then passes those fields into the existing operator overlay preview service.

This is a cleanup and safety-boundary step. It prepares the codebase for later trusted proxy or real auth provider work without adding those systems now.

## 3. Why This Comes Before Real Auth Provider Integration

Real provider integration would involve frontend session handling, JWT/OIDC/Supabase verification, token refresh behavior, provider configuration, and production deployment secrets.

The repo is not ready for that as the next immediate step. The current handoff says the preferred next slice is adapter-only:

```text
Auth-1 — operator auth context adapter, no provider yet
```

Auth-1 creates the seam where later auth work can plug in safely.

## 4. Current Known State

Current backend route:

```text
app/api/operator_overlays.py
```

Current preview service:

```text
app/services/operator_overlay_preview.py
```

Current integration test:

```text
tests/integration/test_operator_overlay_preview_api.py
```

Current route behavior:

```text
GET /runs/{run_id}/operator/private-overlays?artifact_family=...&access_mode=operator_only_preview
```

Current trusted headers:

```text
X-Operator-Authenticated
X-Operator-Id
X-Operator-Roles
X-Operator-Authorized-Runs
X-Request-Id
```

## 5. Scope

### Allowed Scope

Auth-1 may:

- Add `app/services/operator_auth_context.py`.
- Define an immutable `OperatorAuthContext` data object.
- Define `resolve_operator_auth_context(...)`.
- Move current header parsing out of `app/api/operator_overlays.py` into the adapter.
- Keep current trusted-header behavior exactly the same.
- Keep generated fallback request ID behavior.
- Add focused unit tests for the adapter.
- Update existing operator overlay API tests only if needed to preserve the same behavior.
- Add or update documentation for Auth-1.

### Forbidden Scope

Auth-1 must not:

- Add Supabase.
- Add OIDC.
- Add JWT verification.
- Add frontend session handling.
- Add login/logout UI.
- Add new auth provider dependencies.
- Change artifact-serving policy.
- Add public overlay exposure.
- Add public downloads.
- Expose private artifact paths.
- Expose exact coordinates.
- Expose hashes.
- Change H3/H4 behavior.
- Change SAR math.
- Change GRID logic.
- Change notebook parity logic.
- Change candidate screening math.
- Change private map artifact writers/comparators unless a test import-only adjustment is required.
- Commit private/generated artifacts.

## 6. Proposed Target Design

### New file

```text
app/services/operator_auth_context.py
```

### Proposed data object

```python
@dataclass(frozen=True)
class OperatorAuthContext:
    actor_id: str | None
    is_authenticated: bool
    roles: tuple[str, ...]
    authorized_run_ids: tuple[str, ...]
    request_id: str
```

### Proposed resolver behavior

The resolver should accept the existing raw header values and return an `OperatorAuthContext`.

Expected parsing rules:

```text
x_operator_authenticated:
  true only when stripped lowercase value equals "true"
  otherwise false

x_operator_id:
  stripped non-empty string, otherwise None

x_operator_roles:
  comma-separated, stripped, remove empty values, tuple result

x_operator_authorized_runs:
  comma-separated, stripped, remove empty values, tuple result

x_request_id:
  stripped non-empty string, otherwise generated fallback request id
```

Fallback request ID format should stay compatible with current behavior:

```text
req_<uuid hex>
```

## 7. Route Flow After Auth-1

```text
app/api/operator_overlays.py
  receives request and query params
  calls resolve_operator_auth_context(...header values...)
  passes auth_context.actor_id
         auth_context.is_authenticated
         auth_context.roles
         auth_context.authorized_run_ids
         auth_context.request_id
  into build_operator_overlay_preview(...)
```

## 8. Files Checklist

### Expected changed files

```text
app/api/operator_overlays.py
app/services/operator_auth_context.py
tests/unit/test_operator_auth_context.py
tests/integration/test_operator_overlay_preview_api.py   # only if needed
```

### Optional documentation file

```text
docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md
```

### Files that should not change

```text
frontend-v2/**
app/services/operator_overlay_preview.py                 # unless strictly necessary; prefer no change
app/pipeline/stages/**
app/pipeline/stages_experimental/**
app/pipeline/parity/private_map_artifact_*.py
app/pipeline/parity/operator_overlay_access_foundation.py
notebooks/**
config/**
data/**
```

## 9. Implementation Checklist

### Step 0 — Documentation first

- [ ] Add this planning document to `docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md`.
- [ ] Commit documentation only.
- [ ] Do not change code in the planning commit.

### Step 1 — Adapter implementation

- [ ] Add `app/services/operator_auth_context.py`.
- [ ] Define `OperatorAuthContext` as frozen dataclass.
- [ ] Define `resolve_operator_auth_context(...)`.
- [ ] Preserve current parsing behavior exactly.
- [ ] Preserve generated request ID fallback.
- [ ] Export public symbols using `__all__`.

### Step 2 — Route refactor

- [ ] Update `app/api/operator_overlays.py` to import the adapter.
- [ ] Keep the same route path.
- [ ] Keep the same query parameters.
- [ ] Keep the same header names.
- [ ] Remove inline parsing from the route.
- [ ] Pass adapter fields to `build_operator_overlay_preview(...)`.
- [ ] Keep response shape unchanged.

### Step 3 — Unit tests

- [ ] Test authenticated true parsing.
- [ ] Test non-true values parse as unauthenticated.
- [ ] Test actor ID trimming and empty-to-None behavior.
- [ ] Test roles trimming, comma splitting, and empty removal.
- [ ] Test authorized run IDs trimming, comma splitting, and empty removal.
- [ ] Test request ID preservation when provided.
- [ ] Test request ID fallback when missing or blank.
- [ ] Test resolver returns immutable tuple fields.

### Step 4 — Existing API behavior tests

- [ ] Confirm disabled-by-default still denies.
- [ ] Confirm unauthenticated actor still denies.
- [ ] Confirm non-operator actor still denies.
- [ ] Confirm unauthorized run still denies.
- [ ] Confirm unsupported artifact family still denies.
- [ ] Confirm public modes still deny.
- [ ] Confirm valid operator still receives coordinate-free preview.
- [ ] Confirm missing artifact still returns `not_available` for authorized operator.
- [ ] Confirm no public surface appears in allowed or denied responses.

## 10. Validation Commands

Run focused tests first:

```bash
pytest tests/unit/test_operator_auth_context.py -v
pytest tests/integration/test_operator_overlay_preview_api.py -v
```

Then run broader safe validation:

```bash
pytest tests/unit/ tests/integration/ -v
```

If notebook parity tests are normally part of your local gate and dependencies are available:

```bash
pytest tests/notebook_parity/ -v
```

Before final report:

```bash
git status --short
git diff --stat
git diff -- app/api/operator_overlays.py app/services/operator_auth_context.py tests/unit/test_operator_auth_context.py tests/integration/test_operator_overlay_preview_api.py docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md
```

## 11. Acceptance Criteria

Auth-1 is accepted only if all are true:

- [ ] The planning doc exists.
- [ ] Operator header parsing is centralized in `app/services/operator_auth_context.py`.
- [ ] `app/api/operator_overlays.py` no longer parses roles/runs/request ID inline.
- [ ] Existing API behavior is unchanged.
- [ ] Denied responses remain redacted.
- [ ] Allowed previews remain coordinate-free.
- [ ] No public overlay/download/artifact-serving behavior is introduced.
- [ ] No frontend files changed.
- [ ] No Supabase/OIDC/JWT/provider dependency added.
- [ ] No H3/H4/SAR/GRID/notebook parity/screening math changed.
- [ ] Focused tests pass.
- [ ] Broad unit/integration tests pass or any unrelated failure is clearly identified with evidence.

## 12. Rollback Plan

If Auth-1 breaks behavior:

1. Revert the implementation commit.
2. Keep the documentation commit only if it accurately marks implementation as not completed.
3. Re-run existing operator overlay API tests to confirm previous behavior is restored.

## 13. Codex Goal — Documentation Commit Only

```text
/goal Auth-1 planning document only — no code changes

Repo / branch / sync rules
- Repo: C:\Dev\GEE_screening
- Branch: main
- Pull latest main before starting.
- Do not force push.

MUST READ FIRST
- docs/HANDOFF_2026_06_07_OPERATOR_OVERLAY_AUTH_AND_H3H4.md
- app/api/operator_overlays.py
- tests/integration/test_operator_overlay_preview_api.py

SCOPE
Add a documentation-only plan for Auth-1.

Create:
- docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md

The document must clearly state:
- Auth-1 is adapter-only.
- No real auth provider yet.
- No frontend session handling.
- No JWT/OIDC/Supabase verification.
- The new backend adapter target is app/services/operator_auth_context.py.
- The current route app/api/operator_overlays.py should later call the adapter instead of parsing X-Operator-* headers inline.
- Exact allowed scope, forbidden scope, checklist, validation commands, and acceptance criteria.

Do not modify:
- app/**
- frontend-v2/**
- tests/**
- notebooks/**
- config/**
- data/**

Validation commands:
- git status --short
- git diff --stat
- git diff -- docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md

Commit message:
- docs: add Auth-1 operator auth context adapter plan

Final report requirements:
1. Commit SHA
2. Changed files
3. Confirmation this was docs-only
4. Confirmation no code/tests/frontend/SAR/GRID/H3/H4/notebook parity files changed
5. Validation command output summary
```

## 14. Codex Goal — Implementation Later, Only After Planning Doc Is Approved

```text
/goal Auth-1 — operator auth context adapter, no provider yet

Repo / branch / sync rules
- Repo: C:\Dev\GEE_screening
- Branch: main
- Pull latest main before starting.
- Do not force push.

MUST READ FIRST
- docs/HANDOFF_2026_06_07_OPERATOR_OVERLAY_AUTH_AND_H3H4.md
- docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md
- app/api/operator_overlays.py
- app/services/operator_overlay_preview.py
- tests/integration/test_operator_overlay_preview_api.py

SCOPE
Implement only Auth-1.

Purpose
Move existing X-Operator-* parsing out of app/api/operator_overlays.py into one backend adapter:
- app/services/operator_auth_context.py

Required behavior
- Add frozen OperatorAuthContext with:
  - actor_id
  - is_authenticated
  - roles
  - authorized_run_ids
  - request_id
- Add resolve_operator_auth_context(...) that preserves current parsing behavior exactly.
- Update app/api/operator_overlays.py so the route calls the adapter and passes the returned fields to build_operator_overlay_preview(...).
- Keep the same route path, query params, header names, response shape, and status behavior.
- Keep failing closed.
- Keep denied responses redacted.
- Keep allowed preview coordinate-free.

Do not:
- No frontend session handling.
- No login/logout UI.
- No JWT/OIDC/Supabase verification.
- No new auth provider dependency.
- No public exposure.
- No artifact-serving policy change.
- No public download.
- No exact coordinates.
- No private path/hash exposure.
- No H3/H4.
- No SAR/GRID/notebook parity/screening math changes.

Allowed files
- app/api/operator_overlays.py
- app/services/operator_auth_context.py
- tests/unit/test_operator_auth_context.py
- tests/integration/test_operator_overlay_preview_api.py only if needed
- docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md only if marking checklist status, no scope expansion

Do not modify
- frontend-v2/**
- app/pipeline/stages/**
- app/pipeline/stages_experimental/**
- notebooks/**
- config/**
- data/**
- private/generated artifacts

Validation commands
- pytest tests/unit/test_operator_auth_context.py -v
- pytest tests/integration/test_operator_overlay_preview_api.py -v
- pytest tests/unit/ tests/integration/ -v
- git status --short
- git diff --stat

Before commit checks
- Confirm no frontend files changed.
- Confirm no SAR/GRID/H3/H4/notebook parity/screening math files changed.
- Confirm no new auth provider dependency added.
- Confirm no generated/private artifact committed.

Commit message
- auth: add operator auth context adapter

Final report requirements
1. Commit SHA
2. Changed files
3. Summary of behavior preserved
4. Test commands and pass/fail results
5. Confirmation no forbidden files/scope changed
6. Confirmation real auth provider was not added
```
