# Local-3 — Full Auth Regression Closeout

Date: 2026-06-08
Status: Local-3 complete — local auth regression closeout validated

## Purpose

Local-3 freezes and documents the completed **local-only** authentication track.
It records the closed state of Auth-1 through Auth-5, the prepared-only boundary
of Deploy-1, and the local milestones Local-1 and Local-2. It adds a small static
contract test that protects these closeout boundaries and confirms the full
focused/broad validation suite passes.

## Explicit Boundary

- **Local only.**
- **No VPS**, no server activation, no deployment.
- **No real provider**, no real token.
- **No login UI, no logout UI**, no token acquisition, no session management.
- **No token storage** — no `localStorage`, `sessionStorage`, or cookie reads.
- **No Supabase or provider SDK.**

VPS deployment remains a separate future milestone and is not started.

## Completed Milestones

| Milestone | Scope                                                                             | Status                              |
|-----------|-----------------------------------------------------------------------------------|-------------------------------------|
| Auth-1    | Operator auth context adapter (centralized header parsing)                        | Closed                              |
| Auth-2    | Trusted proxy mode / settings gate (`operator_auth_trusted_proxy_enabled`)        | Closed                              |
| Auth-3    | Backend per-run authorization resolver (`operator_run_authorizations`)            | Closed — final run gate             |
| Auth-4    | Generic OIDC config / verifier / adapter wiring / frontend bearer forwarding      | Closed                              |
| Auth-5    | OIDC runtime deployment runbook + smoke tooling                                    | Closed                              |
| Deploy-1  | Server activation packet                                                           | Prepared reference only, not executed |
| LOCAL-1   | Local OIDC dev harness (in-memory keypair, fake token, localhost JWKS)            | Closed                              |
| LOCAL-2   | Local operator UI token handoff contract                                          | Closed                              |
| LOCAL-3   | Local full auth regression closeout                                               | Closed                              |

## Final Local Auth Flow Summary

1. **Local-1** mints a local fake OIDC token and serves a matching JWKS on `127.0.0.1`.
2. The **backend verifier** (`operator_token_verifier.py`) validates the token
   signature, issuer, audience, and expiry against the JWKS.
3. The **auth context** (`operator_auth_context.py`) resolves actor id and roles
   from the verified token claims.
4. **Auth-3** (`operator_run_authorization.py`) checks per-run authorization in
   `operator_run_authorizations` — this remains the **final run gate**.
5. **Local-2** confirms the UI can forward an already-obtained token via the
   `operatorAccessToken` prop to `Authorization: Bearer <token>`.
6. Denied responses remain redacted and default-off — no private fields leak.

## Intentionally Out of Scope

- Real OIDC provider setup.
- Login UI / logout UI.
- Token acquisition flow.
- Token storage (localStorage / sessionStorage / cookies).
- VPS deployment.
- Production / server activation.

## Regression Matrix

| Case                                                          | Expected behavior                          | Covered by                                          |
|---------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------|
| No token                                                      | 403 denied                                 | `test_operator_overlay_preview_api`, `auth5` smoke  |
| Invalid token                                                 | 403 denied                                 | `test_operator_token_verifier`, `auth5` smoke       |
| Valid token + authorized run                                  | 200 allowed                                | `test_operator_overlay_preview_api` (OIDC)          |
| Valid token + unauthorized run                                | 403 denied (Auth-3 final gate)             | `test_operator_overlay_preview_api` (OIDC)          |
| Trusted proxy disabled                                        | Fail-closed                                | `test_operator_auth_context`, overlay API           |
| OIDC invalid token + truthy `X-Operator-*` headers            | Ignores headers, fail-closed               | `test_operator_auth_context`, overlay API           |
| Frontend forwards token only when supplied and nonblank       | `Authorization` set only when nonblank     | `test_local_operator_ui_token_handoff_contract`     |
| Frontend stores no token                                      | No storage APIs in handoff path            | `test_local_operator_ui_token_handoff_contract`     |
| Denied responses leak no private fields                       | No run_id/artifact_family/preview_payload  | `test_operator_overlay_preview_api`, `auth5` smoke  |

## Security / Privacy Closeout

- No real secrets committed.
- No `.env` committed.
- No generated private keys or tokens committed (harness keeps keys in memory only;
  `data/` is gitignored).
- No public overlay / download / artifact-serving exposure changes.
- No operator overlay response shape changes.
- No verifier failure details exposed in responses.

## Validation Results

Date: 2026-06-08

| Check                                | Command                                                                | Result        |
|--------------------------------------|------------------------------------------------------------------------|---------------|
| LOCAL-3 closeout contract tests      | `pytest tests/unit/test_local_auth_track_closeout_contract.py`         | 16 passed     |
| LOCAL-2 contract tests               | `pytest tests/unit/test_local_operator_ui_token_handoff_contract.py`   | 12 passed     |
| LOCAL-1 harness unit tests           | `pytest tests/unit/test_local_oidc_dev_harness.py`                     | 15 passed     |
| Auth-5 smoke unit tests              | `pytest tests/unit/test_auth5_oidc_smoke.py`                           | 18 passed     |
| Deploy-1 env-check unit tests        | `pytest tests/unit/test_deploy1_oidc_env_check.py`                     | 15 passed     |
| Focused Auth backend                 | `pytest <token_verifier+auth_context+config+run_auth+overlay_api>`     | 68 passed     |
| Broad backend regression             | `pytest tests/unit/ tests/integration/`                                | 540 passed    |
| Frontend build                       | `cd frontend-v2 && npm run build`                                      | built clean   |

The broad count increased from 524 to 540, reflecting the 16 new LOCAL-3 contract tests.

## Closeout

Local-3 is complete and local-only.

- The full local auth track (Auth-1 → Auth-5, Deploy-1 prepared-only, Local-1,
  Local-2, Local-3) is frozen and documented.
- No backend auth behavior changed.
- No frontend behavior changed.
- No dependencies changed.
- No login/logout UI added.
- No token storage added.
- No Supabase or provider SDK added.
- No systemd/nginx/Docker/VPS automation added.
- Auth-3 per-run config remains the final run gate.
- Auth-1/Auth-2/Auth-3/Auth-4/Auth-5/Deploy-1/Local-1/Local-2 boundaries remain intact.
- No SAR/GRID/H3/H4/notebook parity/screening math changed.

## Next Possible Future Milestone

The LOCAL track is complete for Generic OIDC readiness. Future VPS deployment is a
separate milestone and is not started. It begins only if the operator explicitly says:

```text
start VPS deployment milestone
```

Until then, all work stays local-first and must not instruct server runtime activation.
