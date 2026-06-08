# Deploy-1 — OIDC Server Activation Packet

Date: 2026-06-08
Status: Prepared reference only — not executed

## Boundary

This document is a prepared reference packet only.

It has not been executed on a VPS or server.

VPS deployment is a separate future milestone and must not be assumed from the local-first Auth and Deploy readiness work.

Do not run server activation steps unless the operator explicitly starts the VPS deployment milestone.

## Current locked state

- Current track: local only.
- Auth-1: fully closed.
- Auth-2: fully closed.
- Auth-3: fully closed.
- Auth-4: fully closed.
- Auth-5: fully closed.
- Deploy-1: prepared reference packet only.
- VPS deployment: future milestone, not started.
- Real runtime activation: not started.
- Real server smoke test: not started.

## What Deploy-1 prepared

Deploy-1 prepared repo-side readiness materials:

- A safe runtime example file at `docs/examples/oidc-runtime.env.example`.
- An environment check script at `scripts/deploy1_oidc_env_check.py`.
- Unit tests for that script at `tests/unit/test_deploy1_oidc_env_check.py`.
- Validation records from local/repo test runs.

These materials are for a future VPS milestone. They do not mean a server exists, is configured, or has run these steps.

## Future VPS milestone rule

The future VPS milestone starts only after the operator explicitly says:

```text
start VPS deployment milestone
```

Until then, future goals must stay local-first and must not instruct the operator to activate server runtime settings.

## Local-first track includes

- Local app run and validation.
- Local smoke script checks.
- The local-only OIDC dev harness at `docs/LOCAL_1_OIDC_DEV_HARNESS.md` — the
  correct current path for testing the OIDC valid-token flow locally.
- The local-only operator UI token handoff contract validation at
  `docs/LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md`.
- The local full auth regression closeout at
  `docs/LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md` — confirms the local auth track
  is closed. Deploy-1 remains prepared reference only, not executed.
- Repo documentation and tests.
- Frontend build checks.
- No VPS assumptions.
- No production activation.

## Future VPS track may include

- Confirming the VPS host.
- Pulling the repository on the VPS.
- Installing runtime dependencies.
- Configuring the process manager if approved.
- Configuring runtime environment values outside Git.
- Running environment checks on the VPS.
- Running smoke tests against the VPS runtime.
- Verifying rollback.

## Closeout

Deploy-1 remains complete as a prepared packet, but it is not an executed deployment.

The next valid local-first step must not assume VPS deployment.
