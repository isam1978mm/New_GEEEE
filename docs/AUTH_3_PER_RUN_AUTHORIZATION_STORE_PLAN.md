# Auth-3 — Per-Run Authorization Source/Store Plan

Date: 2026-06-08
Status: Step 4 complete — resolver wired into authorization_result
Implementation status: Resolver wiring complete; post-wiring focused tests not started

## Purpose

Auth-3 moves per-run authorization away from trusting the upstream
`X-Operator-Authorized-Runs` header as the final source of truth about whether a
given actor may access a given run.

It introduces a small backend-controlled authorization resolver so that the
per-run access decision is derived from a store the backend owns, not from a
header value that an upstream proxy supplies.

This is not real auth provider integration. It does not add Supabase, OIDC, JWT
verification, frontend session handling, login/logout UI, or a new auth dependency.

## Plain-English Summary

Today, after Auth-1 and Auth-2, the operator overlay route works like this:

1. The trusted-proxy gate (Auth-2) is checked first. If disabled, all context is
   discarded and the request fails closed.
2. If trusted-proxy mode is on, `resolve_operator_auth_context(...)` parses the
   upstream headers and returns `authorized_run_ids` — a tuple of run IDs the
   proxy claims this actor is allowed to see.
3. `build_operator_overlay_preview(...)` passes those `authorized_run_ids` to
   `OverlayAccessRequest`.
4. `_is_run_authorized(request)` in `operator_overlay_access_foundation.py` checks
   whether the requested `run_id` is in that tuple.

The gap: the backend has no independent record of which actors are authorized for
which runs. It relies entirely on a header value supplied by the upstream proxy.
A misconfigured or compromised proxy can grant any actor access to any run simply
by including its ID in `X-Operator-Authorized-Runs`.

Auth-3 should add one backend-controlled resolver that produces a per-run
authorization result (`authorization_result: bool`) independently of the header
value, and wire that result into the existing `authorization_result` seam on
`OverlayAccessRequest` so the foundation's gate logic uses it instead of the raw
header tuple.

Backend config-backed resolver now supplies `authorization_result`; header-supplied
`authorized_run_ids` is no longer the final per-run gate.

## Why Auth-3 Comes After Auth-2

Auth-2 added a backend settings gate that decides whether the app trusts upstream
headers at all. Without Auth-2, Auth-3 would be providing a resolver whose output
the route might still silently override with raw header data.

Auth-1 established the stable adapter boundary in
`app/services/operator_auth_context.py`. Auth-2 placed the first explicit
backend decision point at the trusted-proxy setting. Auth-3 is the natural next
layer: given that the proxy is trusted at the transport level (Auth-2), what does
the backend itself know about which runs a given actor is authorized to access?

## Current State

After Auth-1 and Auth-2:

```text
- Operator header parsing is centralized in app/services/operator_auth_context.py
- Trusted-proxy gate enforced in resolve_operator_auth_context(trusted_proxy_enabled=...)
- app/api/operator_overlays.py calls the adapter and passes auth_context fields to
  build_operator_overlay_preview(...)
- build_operator_overlay_preview passes authorized_run_ids to OverlayAccessRequest
- _is_run_authorized() in operator_overlay_access_foundation.py currently uses:
    if request.authorization_result is not None:
        return bool(request.authorization_result)
    if request.authorized_run_ids is not None:
        return request.run_id in set(request.authorized_run_ids)
    return False
- No backend-controlled per-run authorization store exists
- No real auth provider exists
```

## Current Authorization Behavior

The existing `_is_run_authorized` seam in
`app/pipeline/parity/operator_overlay_access_foundation.py` already supports two
paths:

1. **`authorization_result`** — a pre-resolved `bool | None` set by the caller.
   If not `None`, this value is used directly and `authorized_run_ids` is ignored.

2. **`authorized_run_ids`** — a header-supplied tuple. Used only when
   `authorization_result` is `None`.

Currently `build_operator_overlay_preview(...)` always leaves
`authorization_result` as `None`, so the decision falls through to the
`authorized_run_ids` path. Auth-3 should use the `authorization_result` seam so
the backend resolver result drives the per-run gate.

## Proposed Per-Run Authorization Source/Store Boundary

Auth-3 should define one backend-controlled per-run authorization boundary:

```text
A backend resolver, given actor_id and run_id, returns whether that actor is
currently authorized for that run.
```

Proposed behavior:

- The resolver result (`True` or `False`) is passed as `authorization_result` to
  `OverlayAccessRequest`.
- The foundation's `_is_run_authorized` uses `authorization_result` in preference
  to `authorized_run_ids`.
- Failing closed is preserved: if the resolver is unavailable or has no record,
  the result is `False`.
- The resolver is backend-owned. The header-supplied `authorized_run_ids` is still
  parsed by the auth-context adapter (for later audit or logging use) but is no
  longer the final arbiter of per-run access.
- No public overlay, public download, or artifact-serving policy change is
  introduced.
- No exact coordinates, raw geometry, or private artifact contents are exposed.

## Proposed Authorization Store Direction

**Decision: config-backed first.**

The backing store for Auth-3 should be the smallest option consistent with the
existing project architecture.

The project already uses SQLite via:

```text
app/config.py → Settings.database_path
```

and the database is already managed through Alembic migrations. A lightweight
SQLite-backed store is therefore the natural fit and avoids any new infrastructure
dependency.

Possible alternative for an early iteration: a config-backed in-memory allow-list
(e.g., a new `Settings` field `operator_authorized_run_ids: list[str]`) that lets
an operator hard-configure which runs are pre-authorized in the `.env` file. This
is simpler to implement first and can be superseded by a SQLite-backed store in a
later slice if needed.

**Reason for selecting config-backed first:**
- Smaller first slice
- No migration required
- No new infrastructure
- Easier validation
- Proves the authorization_result resolver seam before adding SQLite-backed dynamic storage

Both directions are documented here. The selected order is: **config-backed first**, then migrate to SQLite-backed if dynamic per-actor-per-run management is needed.

## Allowed Scope

Auth-3 may change only the smallest backend boundary needed for per-run
authorization resolver wiring:

```text
app/config.py                                 (only if a config-backed store is chosen)
app/services/operator_run_authorization.py    (new — the resolver service)
app/services/operator_overlay_preview.py      (wire authorization_result= from resolver)
tests/unit/test_operator_run_authorization.py (new — unit tests for the resolver)
tests/integration/test_operator_overlay_preview_api.py
                                               (only if a real coverage gap is found)
docs/AUTH_3_PER_RUN_AUTHORIZATION_STORE_PLAN.md
```

Auth-3 may:

- Add one new resolver service module.
- Add a focused unit test suite for the resolver.
- Wire the resolver output into the existing `authorization_result` seam on
  `OverlayAccessRequest`.
- Add a new `Settings` field if a config-backed store is chosen.
- Add a new Alembic migration and SQLite table if a database-backed store is chosen.
- Preserve existing route path, response shape, and operator-only preview
  boundaries.
- Continue reading `authorized_run_ids` from the auth context for audit or
  logging, but not as the per-run gate.

## Forbidden Scope

Auth-3 must not:

- Add Supabase.
- Add OIDC.
- Add JWT verification.
- Add frontend session handling.
- Add login/logout UI.
- Add a UI management page for per-run authorization.
- Add a new non-SQLite/non-config auth store dependency (no Postgres, Redis,
  Celery, RQ, arq, or separate worker).
- Change artifact-serving policy.
- Change public/private exposure behavior.
- Expose exact coordinates, raw geometry, KML contents, heatmap point payloads,
  local filesystem paths, or private hashes.
- Change H3/H4 behavior.
- Change SAR math.
- Change GRID logic.
- Change notebook parity logic.
- Change candidate screening math.
- Commit generated/private artifacts.
- Remove the trusted-proxy gate added in Auth-2.
- Remove the auth-context adapter added in Auth-1.

Auth-3 is not real provider integration.
Auth-3 is not Supabase.
Auth-3 is not OIDC.
Auth-3 is not JWT verification.
Auth-3 does not add login/logout UI.

## Progress Checklist

- [x] Step 1: choose config-backed store direction
- [x] Step 2: add config-backed authorization setting
- [x] Step 3: add operator run authorization resolver with direct unit tests
- [x] Step 4: wire resolver output into authorization_result
- [ ] Step 5: add post-wiring focused tests
- [ ] Step 6: run focused and broad validation

## Proposed Implementation Steps

1. ~~Choose and document the backing store direction (config-backed or SQLite-backed)
    before writing any code. Commit the choice as a one-line note in this document.~~
   **Done:** config-backed first selected.

2. Add `app/services/operator_run_authorization.py`:
   - Define a small `OperatorRunAuthorizationResult` dataclass (or plain `bool`
     return) with fields `allowed: bool` and optionally `reason: str`.
   - Define `resolve_run_authorization(*, actor_id: str | None, run_id: str,
     settings: Settings) -> bool` (or returning the small dataclass).
   - Implement fail-closed: if the store has no record for `(actor_id, run_id)`,
     return `False`.
   - Export public symbols using `__all__`.

3. Wire the resolver in `app/services/operator_overlay_preview.py`:
   - Call `resolve_run_authorization(actor_id=actor_id, run_id=run_id,
     settings=settings)` before building `OverlayAccessRequest`.
   - Pass the result as `authorization_result=` to `OverlayAccessRequest`.
   - Keep passing `authorized_run_ids` for audit use if needed, or omit it once
     `authorization_result` is always set.

4. If config-backed: add a new `Settings` field:
   `operator_run_authorizations: dict[str, list[str]] = Field(default_factory=dict)`
   and use it inside the resolver to check membership.

5. If SQLite-backed: add one Alembic migration creating a small authorization
   table (`operator_run_authorizations`) with at minimum `actor_id TEXT`,
   `run_id TEXT`, `created_at TEXT`, `granted_by TEXT`. Keep the table minimal.

6. Add `tests/unit/test_operator_run_authorization.py`:
   - Test that an actor with a matching record is authorized.
   - Test that an actor with no record is denied (fail-closed).
   - Test that a `None` actor_id is denied.
   - Test that the resolver output is passed correctly as `authorization_result=`.

7. Re-run focused and broad tests to confirm existing redaction and operator-only
   behavior remain unchanged.

## Expected Changed Files for Later Implementation

```text
app/services/operator_run_authorization.py          (new)
app/services/operator_overlay_preview.py            (wire authorization_result=)
tests/unit/test_operator_run_authorization.py       (new)
docs/AUTH_3_PER_RUN_AUTHORIZATION_STORE_PLAN.md     (progress/status updates)
```

If config-backed store is chosen, additionally:

```text
app/config.py
tests/unit/test_config_auth_settings.py
```

If SQLite-backed store is chosen, additionally:

```text
alembic/versions/<hash>_add_operator_run_authorizations_table.py
```

Integration test file is expected to need no changes unless a real coverage gap is
found.

## Validation Commands

Recommended commands for the later implementation slice:

```bash
uv run python -m pytest tests/unit/test_operator_run_authorization.py -v
uv run python -m pytest tests/unit/test_config_auth_settings.py -v
uv run python -m pytest tests/unit/test_operator_auth_context.py -v
uv run python -m pytest tests/integration/test_operator_overlay_preview_api.py -v
uv run python -m pytest tests/unit/ tests/integration/ -v
git status --short
git diff --stat
git diff -- docs/AUTH_3_PER_RUN_AUTHORIZATION_STORE_PLAN.md
```

## Acceptance Criteria

Auth-3 should be accepted only if all are true:

- A backend-controlled per-run authorization resolver exists in
  `app/services/operator_run_authorization.py`.
- The resolver output is passed as `authorization_result=` to
  `OverlayAccessRequest`, not derived from the header-supplied `authorized_run_ids`
  alone.
- The resolver fails closed when no record exists for `(actor_id, run_id)`.
- The trusted-proxy gate from Auth-2 remains in place.
- The auth-context adapter from Auth-1 remains in place.
- Existing operator overlay response shape is unchanged.
- Existing redaction behavior is unchanged.
- No public overlay or artifact-serving behavior changes are introduced.
- No frontend changes are required.
- No Supabase/OIDC/JWT/provider dependency is added.
- No H3/H4/SAR/GRID/notebook parity/screening math behavior changes are introduced.
- Focused unit tests for the resolver pass.
- Broad unit and integration tests pass without regressions.

## Rollback Plan

If the Auth-3 implementation causes regressions:

1. Revert the resolver wiring change in `app/services/operator_overlay_preview.py`
   so `authorization_result` is again `None` and `authorized_run_ids` is used as
   before.
2. Remove or disable the new resolver service.
3. Re-run the focused unit and integration tests for operator auth context and
   operator overlay preview.
4. Leave the per-run authorization store work blocked until a smaller or clearer
   Auth-3 implementation is approved.

## Codex Goal Template for Later Implementation

Use a later scoped goal in this shape:

```text
goal Auth-3 implementation only — per-run authorization store

Repo / branch / sync rules
- Repo: C:\Dev\New_GEE
- Remote: https://github.com/max2026-lab/New_GEE.git
- Branch: main
- Pull latest main before starting.
- Do not force push.
- Push the final commit to origin main.

MUST READ FIRST
- docs/AUTH_3_PER_RUN_AUTHORIZATION_STORE_PLAN.md
- app/config.py
- app/services/operator_auth_context.py
- app/services/operator_overlay_preview.py
- app/pipeline/parity/operator_overlay_access_foundation.py
- app/api/operator_overlays.py
- tests/integration/test_operator_overlay_preview_api.py

CURRENT LOCKED STATE
- Auth-1 is fully closed.
- Auth-2 is fully closed.
- Auth-3 implementation is not started.

SCOPE
- Add app/services/operator_run_authorization.py.
- Wire authorization_result= into build_operator_overlay_preview via the resolver.
- Add tests/unit/test_operator_run_authorization.py.
- [If config-backed: add one Settings field and test it.]
- [If SQLite-backed: add one Alembic migration.]
- Update docs/AUTH_3_PER_RUN_AUTHORIZATION_STORE_PLAN.md progress/status.

STRICT DO NOT CHANGE
- Do not modify app/api/operator_overlays.py.
- Do not modify app/services/operator_auth_context.py.
- Do not remove the trusted-proxy gate.
- Do not add real auth provider integration.
- Do not add frontend session handling.
- Do not add login/logout UI.
- Do not add Supabase / OIDC / JWT verification.
- Do not add new non-SQLite/non-config store dependencies.
- Do not add UI management for authorization.
- Do not change artifact-serving policy.
- Do not change public/private exposure behavior.
- Do not change H3/H4 / SAR / GRID / notebook parity / screening math.
- Do not commit generated/private artifacts.

Validation commands:
- uv run python -m pytest tests/unit/test_operator_run_authorization.py -v
- uv run python -m pytest tests/unit/ tests/integration/ -v
- git status --short
- git diff --stat

Before commit checks:
- Confirm app/api/operator_overlays.py did not change.
- Confirm app/services/operator_auth_context.py did not change.
- Confirm no frontend files changed.
- Confirm no SAR/GRID/H3/H4/notebook parity/screening math files changed.
- Confirm no new auth provider dependency was added.
- Confirm no generated/private artifact was committed.
- Confirm authorization_result= is wired and _is_run_authorized uses it.

Commit message: feat: add Auth-3 per-run authorization resolver

Final report requirements:
1. Commit SHA
2. Exact changed files
3. Whether config-backed or SQLite-backed store was chosen and why
4. Full validation command output or clear pass/fail summary
5. Confirmation app/api/operator_overlays.py and operator_auth_context.py not changed
6. Confirmation no frontend/UI authorization management added
7. Confirmation real auth provider not added
8. Confirmation authorization_result= is now wired from the backend resolver
9. Confirmation commit was pushed to origin main
```
