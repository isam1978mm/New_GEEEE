# V6-DEPLOY-RUNBOOK-1 Operator Deployment Runbook

## Current Status

V6-DEPLOY-RUNBOOK-1 documents how to enable the frozen V6 real package workflow safely in an operator-controlled environment.

This is a post-freeze deployment document. It does not change the frozen V6 workflow logic.

Frozen checkpoint before this runbook:

```text
V6-SCAFFOLD-1 -> done and tested
V6-REAL-GEE-1 -> done and tested
V6-REAL-GEE-2 -> done and tested
V6-REAL-SCORING-1 -> done and tested
V6-REAL-REDUCE-1 -> done and tested
V6-REAL-ZONES-1 -> done and tested
V6-REAL-PACKAGE-1 -> done and tested
V6-APP-FLOW-1 -> done and tested
V6-APP-UI-1 -> done and tested
V6-FINAL-WIRING-1 -> done and tested
V6-READY-FREEZE-1 -> done and tested
```

## Purpose

This runbook gives an operator-safe sequence for enabling the frozen V6 package flow on a deployed app instance.

The intended operator workflow is:

```text
completed run
-> run-local private V6 package input manifest exists
-> operator opens the private run panel
-> operator reviews safe metadata
-> operator generates package
-> operator reviews validation status
-> operator retrieves ZIP package
```

## Non-goals

This runbook does not authorize or implement:

- provider ordering
- payment or purchase flow
- public API exposure
- public candidate rows
- public spatial payloads
- generated artifact commits
- notebook runtime dependency
- manual edits to the frozen V6 package logic

## Required Preconditions

Before enabling the deployed V6 package flow, confirm:

```text
[ ] app deploy is using the frozen V6 checkpoint or a versioned post-freeze follow-up
[ ] database migrations required by the base app are already applied
[ ] run storage directory is mounted and writable by the app process
[ ] run-local private V6 package input manifest exists for the target run
[ ] target run belongs to an operator-approved environment
[ ] operator auth is enabled and working
[ ] operator private overlay is reachable only by authorized users
[ ] generated package output directory is outside Git
[ ] no real generated package artifacts are tracked in source control
```

## Required Configuration

The package flow is default-off. Enable it only after the preconditions are satisfied.

Required setting:

```text
V6_PACKAGE_FLOW_ENABLED=true
```

Operator auth must remain enabled. Do not enable the package flow in a public unauthenticated environment.

Recommended environment posture:

```text
AUTH_ENABLED=true
V6_PACKAGE_FLOW_ENABLED=true
```

Do not log secrets, private package input bodies, package rows, feature bodies, or spatial payload bodies.

## Operator Access Rules

Only an authorized operator may use the V6 package flow.

Required behavior:

```text
[ ] denied requests do not read private package input
[ ] denied requests do not generate package files
[ ] denied requests do not reveal package paths
[ ] denied requests return only safe error/status metadata
[ ] authorized review returns metadata only
[ ] authorized retrieval returns the package file only through the controlled route
```

## Backend Smoke Checklist

Run these from the repository root after deployment code is pulled:

```powershell
python -m pytest tests/unit/test_v6_app_flow.py -q
python -m pytest tests/unit/test_v6_real_package.py -q
python -m pytest tests/unit/test_v6_ready_freeze_contract.py -q
python -m pytest tests/unit/test_v6_final_wiring_contract.py -q
```

Expected result:

```text
all listed tests pass
```

Pytest cache permission warnings are local environment warnings and do not by themselves fail deployment validation.

## Frontend Smoke Checklist

Run from `frontend-v2`:

```powershell
npm run build
```

Expected result:

```text
build completes successfully
```

The built UI must show only safe metadata in the private V6 panel:

```text
readiness
validation status
payload count
ZIP entry count
issue count
warning count
package filename
category counts
```

The UI must not show:

```text
candidate rows
feature rows
private package input body
spatial payload body
full server filesystem paths
provider credentials
```

## Manual Operator Smoke

Use a non-public staging deployment first.

1. Sign in as an authorized operator.
2. Open a run that has a private V6 package input manifest.
3. Open the operator private panel.
4. Click package review.
5. Confirm only safe metadata appears.
6. Click generate package.
7. Confirm validation status is successful.
8. Click retrieve package.
9. Confirm the ZIP is returned through the controlled route.
10. Confirm the UI still does not display candidate rows, feature rows, or spatial payload bodies.

## Rollback Plan

If anything fails or the operator sees unsafe output:

```text
1. Set V6_PACKAGE_FLOW_ENABLED=false.
2. Restart/redeploy the app process.
3. Confirm package review/generate/retrieve routes are unavailable or denied.
4. Preserve logs for debugging, but do not paste private package input bodies into tickets.
5. Open a versioned bug-fix task before changing frozen workflow logic.
```

## Production Safety Rules

The frozen V6 package flow is allowed only under these rules:

```text
[x] generated package artifacts remain outside Git
[x] operator-only access is required
[x] frontend shows metadata only
[x] backend denied requests do not read package input
[x] package retrieval is controlled by authorization
[x] provider ordering remains separate and manual unless a future approved version adds it
[x] post-freeze changes must be versioned or bug-fix scoped
```

## Deployment Checklist

```text
[ ] pull latest main
[ ] confirm HEAD includes V6-READY-FREEZE-1 and this runbook
[ ] run backend smoke tests
[ ] run frontend build smoke
[ ] configure AUTH_ENABLED=true
[ ] configure V6_PACKAGE_FLOW_ENABLED=true only in approved operator environment
[ ] verify run storage is writable
[ ] verify private package input manifest exists for test run
[ ] perform manual operator smoke
[ ] confirm no generated V6 artifacts are staged or committed
[ ] record deployment result in operator notes
```

## Next Step

```text
V6-E2E-1: optional browser end-to-end smoke automation for the frozen V6 package flow.
```
