# V6.1-PROD-SMOKE-1 Production-like Smoke Test

## Current Status

V6.1-PROD-SMOKE-1 defines the operator-approved production-like smoke test for the frozen V6 package flow.

This is a versioned V6.1 follow-up. It does not change frozen V6 generation, scoring, reduction, request-zone, package, backend, frontend, deployment, E2E, or safety behavior.

This document is the smoke-test procedure and evidence contract. The operator executes the production-like smoke in an approved environment and records only safe metadata results.

## Frozen Baseline

The smoke test starts from this frozen post-freeze baseline:

```text
V6-READY-FREEZE-1 -> done and tested
V6-DEPLOY-RUNBOOK-1 -> done and tested
V6-E2E-1 -> done and tested
V6.1-PLAN-1 -> done and tested
```

## Operator Approval Required

Before running the production-like smoke:

```text
[ ] operator approves the target environment
[ ] operator confirms the run is eligible for package generation
[ ] operator confirms the bearer/session mechanism is active
[ ] operator confirms generated artifacts will remain outside Git
[ ] operator confirms no real coordinates will be copied into docs, tests, issues, or chat
[ ] operator confirms no private rows or spatial payload bodies will be pasted into logs
```

## Scope

The smoke verifies the real operator workflow, not the scientific algorithm:

```text
select approved completed run
-> enable package flow only in the approved environment
-> start authenticated operator session
-> review V6 package metadata
-> generate package
-> review validation metadata
-> retrieve ZIP through authorized route
-> confirm UI shows metadata only
-> disable or leave disabled according to rollback policy
```

## Non-goals

This smoke does not authorize:

- changing frozen V6 formulas
- changing ranking, reduction, request-zone, or package schemas
- exposing private candidates publicly
- exposing spatial payload bodies publicly
- committing generated ZIPs, CSVs, GeoJSON, HTML, or reports
- adding provider ordering, provider purchasing, or payment automation
- saving bearer tokens to repo files, screenshots, docs, or logs
- adding real coordinates to repo fixtures or documentation

## Required Preflight

Run these local checks before the production-like smoke:

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_v6_ready_freeze_contract.py -q
python -m pytest tests/unit/test_v6_deploy_runbook_contract.py -q
python -m pytest tests/unit/test_v6_e2e_contract.py -q
python -m pytest tests/unit/test_v6_1_plan_contract.py -q
```

Run frontend checks:

```powershell
cd C:\Dev\New_GEE\frontend-v2
npm run build
npm run e2e:v6
```

Expected preflight result:

```text
all listed pytest commands pass
npm run build passes
npm run e2e:v6 passes
```

## Environment Gate

The package flow remains default-off. Enable it only for the approved smoke environment.

Required environment conditions:

```text
[ ] auth is enabled
[ ] operator-only route authorization is active
[ ] V6_PACKAGE_FLOW_ENABLED=true only for the approved smoke window
[ ] run storage is writable by the app
[ ] generated package output directory is outside Git tracking
[ ] logs are metadata-only
```

Rollback condition:

```text
V6_PACKAGE_FLOW_ENABLED=false
```

## Smoke Execution Checklist

### 1. Select approved run

```text
[ ] open operator UI
[ ] select approved completed run
[ ] verify run status is done
[ ] do not copy real coordinates into the smoke record
```

### 2. Start operator session

```text
[ ] start operator session with approved bearer/session mechanism
[ ] do not save bearer value in files, docs, screenshots, or logs
[ ] confirm operator-only private panel is available
```

### 3. Review metadata before generation

```text
[ ] click Review metadata
[ ] outcome is available or not_available according to current package state
[ ] UI shows metadata only
[ ] UI does not show candidate rows
[ ] UI does not show spatial payload bodies
[ ] UI does not show raw server paths
```

### 4. Generate package

```text
[ ] click Generate package
[ ] generation returns generated or safe error state
[ ] validation status is visible when package is generated
[ ] payload count is visible when package is generated
[ ] ZIP entry count is visible when package is generated
[ ] issue and warning counts are visible when reported
```

### 5. Retrieve package

```text
[ ] Retrieve ZIP is enabled only when package_ready=true
[ ] click Retrieve ZIP
[ ] ZIP retrieval starts through authorized route
[ ] retrieved filename is safe to display
[ ] no generated ZIP or payload file is committed to Git
```

### 6. Final safety check

```text
[ ] public API did not expose private rows
[ ] frontend did not render candidate rows
[ ] frontend did not render spatial payload bodies
[ ] logs did not include bearer token
[ ] logs did not include real coordinates
[ ] logs did not include generated artifact bodies
```

## Safe Evidence Record Template

Only record safe metadata:

```text
V6.1-PROD-SMOKE-1 evidence
Date/time:
Environment label:
Operator-approved run label:
Package flow enabled during smoke: yes/no
Review outcome:
Generate outcome:
Validation status:
Payload count:
ZIP entry count:
Issue count:
Warning count:
Retrieve ZIP result: started/not_started
Rollback state after smoke: enabled/disabled
Notes without private rows, coordinates, tokens, or artifact bodies:
```

Do not record:

```text
real coordinates
candidate rows
feature rows
spatial payload bodies
raw server paths
bearer tokens
provider credentials
generated ZIP content
generated CSV/GeoJSON/report bodies
```

## Failure Handling

If any smoke step fails:

```text
1. Set V6_PACKAGE_FLOW_ENABLED=false if the failure affects package generation or retrieval.
2. Keep generated artifacts outside Git.
3. Save only safe metadata error state.
4. Run backend contract tests again.
5. Run frontend build and browser E2E again.
6. Open a versioned bug-fix task.
7. Do not alter frozen V6 generation logic unless a source-locked defect is proven.
```

## Completion Criteria

V6.1-PROD-SMOKE-1 is complete when:

```text
[x] production-like smoke procedure is documented
[x] operator approval gates are documented
[x] preflight tests are documented
[x] package-flow enable/rollback gate is documented
[x] safe evidence template is documented
[x] no frozen V6 behavior is changed
[x] no production code changes are made by this planning/checklist task
```

## Next Recommended Track

```text
V6.1-OBSERVABILITY-1: add safe metadata-only counters and logs for package review, generation, retrieval, denied requests, and rollback state.
```
