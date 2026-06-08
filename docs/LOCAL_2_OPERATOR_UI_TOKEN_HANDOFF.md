# Local-2 — Operator UI Token Handoff Contract

Date: 2026-06-08
Status: Local-2 complete — operator UI token handoff contract validated

## Purpose

Local-2 proves and documents the **existing** local operator UI token handoff
contract. It adds no UI, no token acquisition, and no storage. It validates that
a token the caller already holds can flow from a component prop all the way to an
`Authorization: Bearer` header on the operator overlay request:

```
caller-provided operatorAccessToken
  -> OperatorPrivateOverlayPanel
    -> getOperatorPrivateOverlayPreview(runId, family, { accessToken })
      -> Authorization: Bearer <trimmed token>   (only when nonblank)
```

## Explicit Boundary

- **Local only.**
- **No VPS**, no server activation, no deployment.
- **No real provider**, no real token.
- **No login UI, no logout UI**, no session management.
- **No token storage** — no `localStorage`, `sessionStorage`, or cookie reads.

VPS deployment remains a separate future milestone and is not started.

## What Is Being Validated

- The caller **already has** a bearer token (e.g. a Local-1 fake token, or in real
  use, a provider-issued token obtained outside this app).
- The caller passes that token into `OperatorPrivateOverlayPanel` via the
  `operatorAccessToken` prop.
- The panel forwards it to `getOperatorPrivateOverlayPreview` as `{ accessToken }`.
- The API helper trims the token and sets `Authorization: Bearer <trimmed token>`
  **only** when the token is nonblank.
- A blank / null / undefined token results in **no** `Authorization` header
  (preserving the default-off backend gate behavior).
- The token change is in the effect dependency list, so updating the token
  retriggers preview loading.

## What Is NOT Being Added

- Token acquisition / provider auth flow.
- Login UI or logout UI.
- Session management.
- Token storage (localStorage / sessionStorage / cookies).
- Supabase or any auth provider SDK (Auth0, Keycloak, Clerk, Firebase, Cognito, MSAL).
- A token persistence helper or new auth state manager.
- Any VPS / deployment automation.

## Relationship to Local-1

- **Local-1** (`docs/LOCAL_1_OIDC_DEV_HARNESS.md`) can mint a local fake token and
  serve a matching JWKS on `127.0.0.1`, letting you exercise the backend OIDC
  verification path end-to-end locally.
- **Local-2** confirms the **frontend handoff contract**: that an already-obtained
  token (such as a Local-1 fake token) can be forwarded by the UI to the backend
  without any storage or login machinery.

Together they cover both halves locally: Local-1 produces and verifies a token;
Local-2 confirms the UI can hand a token off to the request.

## Local Manual Check Sequence

This is optional and local-only; it requires no real provider:

1. Use Local-1 to run the local JWKS server, export local env, start the app, and
   run the no-token / invalid-token / valid-token smoke tests
   (see `docs/LOCAL_1_OIDC_DEV_HARNESS.md`).
2. In a local caller or test shell that renders `OperatorPrivateOverlayPanel`,
   pass the already-obtained token via the `operatorAccessToken` prop. The API
   helper forwards it as `Authorization: Bearer <token>`.
3. Confirm no token is written to `localStorage`, `sessionStorage`, or cookies.

## Contract Test Description

`tests/unit/test_local_operator_ui_token_handoff_contract.py` reads the two
frontend source files as text and enforces the contract statically (no frontend
test framework, no new dependencies):

For `frontend-v2/src/app/api/operatorOverlays.ts`:
- `getOperatorPrivateOverlayPreview` accepts an optional `options` param exposing `accessToken`.
- `accessToken?: string | null` shape is present.
- the token is trimmed before use.
- `Authorization: Bearer <trimmedToken>` is set only inside the nonblank guard.
- there is no unconditional `Authorization` assignment.
- the same `/operator/private-overlays` endpoint is still called.
- no `localStorage` / `sessionStorage` / `document.cookie`, no provider SDK, no login/logout wording.

For `frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx`:
- props include `operatorAccessToken?: string | null`.
- the helper is called with `{ accessToken: operatorAccessToken }`.
- `operatorAccessToken` is in the effect dependency list.
- no storage usage, no provider SDK, no login/logout UI.

Across both files:
- no storage APIs, no token-persistence helper, no auth-state/provider terms.

## Validation Results

Date: 2026-06-08

| Check                                | Command                                                                | Result        |
|--------------------------------------|------------------------------------------------------------------------|---------------|
| LOCAL-2 contract tests               | `pytest tests/unit/test_local_operator_ui_token_handoff_contract.py`   | 12 passed     |
| LOCAL-1 harness unit tests           | `pytest tests/unit/test_local_oidc_dev_harness.py`                     | 15 passed     |
| Auth-5 smoke unit tests              | `pytest tests/unit/test_auth5_oidc_smoke.py`                           | 18 passed     |
| Deploy-1 env-check unit tests        | `pytest tests/unit/test_deploy1_oidc_env_check.py`                     | 15 passed     |
| Focused Auth backend                 | `pytest <token_verifier+auth_context+config+run_auth+overlay_api>`     | 68 passed     |
| Broad backend regression             | `pytest tests/unit/ tests/integration/`                                | 524 passed    |
| Frontend build                       | `cd frontend-v2 && npm run build`                                      | built clean   |

The broad count increased from 512 to 524, reflecting the 12 new LOCAL-2 contract tests.

## Closeout

Local-2 is complete and local-only.

- The operator UI token handoff contract is validated by static tests.
- No frontend behavior changed (the existing contract already satisfied the tests).
- No VPS or server activation was added as current work.
- No real provider values, tokens, or keys were committed.
- No backend auth behavior changed.
- No dependencies changed (no frontend test framework, no backend deps).
- No login/logout UI added.
- No token storage added (no localStorage/sessionStorage/cookie reads).
- No Supabase or provider SDK added.
- No systemd/nginx/Docker/VPS automation added.
- Auth-1/Auth-2/Auth-3/Auth-4/Auth-5/Local-1 boundaries remain intact.
- No SAR/GRID/H3/H4/notebook parity/screening math changed.
- Deploy-1 remains a prepared reference packet only, not executed.
