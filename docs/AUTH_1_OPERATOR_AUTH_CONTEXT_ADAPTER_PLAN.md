# Auth-1 — Operator Auth Context Adapter Plan

Date: 2026-06-07
Status: Step 2 complete — route refactor added
Implementation status: Step 2 route refactor complete; unit tests not started

## Purpose

Auth-1 is a small backend cleanup step. It creates one adapter for the current operator identity context used by the private operator overlay route.

This is **not** real auth provider integration. It must not add Supabase, OIDC, JWT verification, frontend session handling, login/logout UI, or a new auth dependency.

## Current state

Current route:

```text
app/api/operator_overlays.py
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

Current issue:

```text
app/api/operator_overlays.py parses X-Operator-* headers inline.
```

Auth-1 should move that parsing into one backend service adapter.

## Target design

New adapter file:

```text
app/services/operator_auth_context.py
```

The route should ask the adapter:

```text
Who is this operator for this request?
```

The adapter should return:

```text
actor_id
is_authenticated
roles
authorized_run_ids
request_id
```

The route should then pass those fields into the existing operator overlay preview service without changing route path, query params, header names, response shape, or status behavior.

## Allowed scope

Auth-1 may change only:

```text
app/api/operator_overlays.py
app/services/operator_auth_context.py
tests/unit/test_operator_auth_context.py
tests/integration/test_operator_overlay_preview_api.py   # only if needed
docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md        # checklist/status only
```

Auth-1 may:

- Add a frozen `OperatorAuthContext` data object.
- Add `resolve_operator_auth_context(...)`.
- Preserve current trusted-header parsing behavior.
- Preserve generated fallback request ID behavior.
- Add focused unit tests for the adapter.
- Keep existing API behavior unchanged.

## Forbidden scope

Auth-1 must not:

- Add Supabase.
- Add OIDC.
- Add JWT verification.
- Add frontend session handling.
- Add login/logout UI.
- Add new auth provider dependencies.
- Change artifact-serving policy.
- Change public/private exposure behavior.
- Change H3/H4 behavior.
- Change SAR math.
- Change GRID logic.
- Change notebook parity logic.
- Change candidate screening math.
- Commit generated/private artifacts.

## Implementation checklist

### Step 0 — Documentation first

Status: Complete. This checkpoint was completed as a docs-only commit. Auth-1 implementation remains not started.

- [x] Add this planning document to `docs/AUTH_1_OPERATOR_AUTH_CONTEXT_ADAPTER_PLAN.md`.
- [x] Commit documentation only.
- [x] Do not change code in the planning commit.

### Step 1 — Adapter implementation

- [x] Add `app/services/operator_auth_context.py`.
- [x] Define `OperatorAuthContext` as frozen dataclass.
- [x] Define `resolve_operator_auth_context(...)`.
- [x] Preserve current parsing behavior exactly.
- [x] Preserve generated request ID fallback.
- [x] Export public symbols using `__all__`.

### Step 2 — Route refactor

- [x] Update `app/api/operator_overlays.py` to import the adapter.
- [x] Keep the same route path.
- [x] Keep the same query parameters.
- [x] Keep the same header names.
- [x] Remove inline parsing from the route.
- [x] Pass adapter fields to `build_operator_overlay_preview(...)`.
- [x] Keep response shape unchanged.

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

## Validation commands for Auth-1 implementation

```bash
pytest tests/unit/test_operator_auth_context.py -v
pytest tests/integration/test_operator_overlay_preview_api.py -v
pytest tests/unit/ tests/integration/ -v
git status --short
git diff --stat
```

## Acceptance criteria

Auth-1 is accepted only if all are true:

- [x] Step 0 planning document exists and is committed.
- [ ] Operator header parsing is centralized in `app/services/operator_auth_context.py`.
- [ ] `app/api/operator_overlays.py` no longer parses roles/runs/request ID inline.
- [ ] Existing API behavior is unchanged.
- [ ] Denied responses remain redacted.
- [ ] Allowed previews remain coordinate-free.
- [ ] No public/private artifact policy change is introduced.
- [ ] No frontend files changed.
- [ ] No Supabase/OIDC/JWT/provider dependency added.
- [ ] No H3/H4/SAR/GRID/notebook parity/screening math changed.
- [ ] Focused tests pass.
- [ ] Broad unit/integration tests pass or unrelated failure is clearly identified with evidence.

## Process rule for next implementation step

For real implementation work, ask Codex to:

1. Pull latest `main` before starting.
2. Make the scoped change only.
3. Run the required validation commands.
4. Push the commit.
5. Report commit SHA, exact changed files, validation output, and forbidden-scope confirmation.

Do not start Step 1 until this Step 0 checkpoint is accepted.
