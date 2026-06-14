# V6-FINAL-WIRING-1 Smoke Documentation And Regression Checklist

## Current Status

V6-FINAL-WIRING-1 documents the full backend-to-frontend smoke path for the real V6 package workflow and freezes the regression checklist for this phase.

Completed before this checkpoint:

- app-side V6 package feed;
- private backend generate/review/retrieve flow;
- default-off operator authorization gate;
- frontend generate/review/retrieve panel;
- metadata-only UI responses;
- unit and contract test coverage.

This document is the operator-facing smoke and regression guide. It does not add new production behavior.

## End-To-End Flow

```text
operator session
  -> selected run
  -> run-local V6 package input manifest
  -> backend generate action
  -> app-generated V6 package payloads
  -> validation report
  -> frontend review metadata panel
  -> authorized ZIP retrieval
```

The browser must only show metadata: readiness, validation status, payload count, ZIP entry count, issue count, warning count, package filename, and category counts.

The browser must not render candidate rows, spatial payload bodies, hashes, local filesystem paths, or private package contents.

## Required Flags And Auth Context

The backend flow is default-off.

For an operator smoke run, configure:

```text
v6_package_flow_enabled=true
operator_auth_trusted_proxy_enabled=true
operator_run_authorizations={"<operator_id>":["<run_id>"]}
```

The operator session must provide:

```text
X-Operator-Authenticated: true
X-Operator-Id: <operator_id>
X-Operator-Roles: operator
```

or a verified operator bearer token when OIDC mode is enabled.

## Backend Smoke Checklist

Run from the repository root:

```powershell
python -m pytest tests/unit/test_v6_final_wiring_contract.py -q
python -m pytest tests/unit/test_v6_app_ui_contract.py -q
python -m pytest tests/unit/test_v6_app_flow.py -q
python -m pytest tests/unit/test_v6_real_package.py -q
python -m pytest tests/unit/test_v6_real_zones.py -q
python -m pytest tests/unit/test_v6_real_reduce.py -q
python -m pytest tests/unit/test_v6_real_scoring.py -q
python -m pytest tests/unit/test_v6_real_gee_features.py -q
python -m pytest tests/unit/test_v6_real_gee_runtime.py -q
python -m pytest tests/unit/test_v6_generator_package.py -q
python -m pytest tests/unit/test_notebook_safety.py -q --basetemp .pytest-v6-generator
```

Pass criteria:

- all tests pass;
- denied V6 package requests return generic denial bodies;
- denied requests do not read V6 package input files;
- review responses are metadata-only;
- package retrieval resolves only after authorization;
- notebook safety tests remain unchanged.

## Frontend Smoke Checklist

Run from the frontend directory:

```powershell
cd frontend-v2
npm run build
```

Pass criteria:

- build completes;
- the operator private section mounts the V6 package panel;
- Generate package calls the backend generate route;
- Review metadata calls the backend review route;
- Retrieve ZIP calls the backend package retrieval route;
- the UI displays metadata only;
- the UI does not display candidate rows or spatial payload bodies.

## Manual Browser Smoke

1. Start the app with the V6 package flow flag enabled.
2. Open the app and select a completed run that has a run-local V6 package input manifest.
3. Start an operator session.
4. Enable the operator private section in settings.
5. Open the selected run dashboard.
6. Confirm the V6 package panel appears.
7. Click Review metadata.
8. Confirm the panel reports not available before generation or package metadata after generation.
9. Click Generate package.
10. Confirm validation status is shown and package-ready state becomes true.
11. Click Retrieve ZIP.
12. Confirm a ZIP retrieval starts.
13. Confirm no candidate rows, spatial payload bodies, hashes, local filesystem paths, or package internals are visible in the browser UI.

## Full Regression Checklist

```text
[x] V6 final wiring contract tests
[x] V6 frontend UI contract tests
[x] V6 scaffold package writer tests
[x] V6 runtime boundary tests
[x] V6 feature-layer boundary tests
[x] V6 scoring tests
[x] V6 reduction bridge tests
[x] V6 request-zone tests
[x] V6 real package-feed tests
[x] V6 backend app-flow tests
[x] notebook safety tests
[x] frontend production build
[x] manual browser smoke
```

## Production Safety Checklist

```text
[ ] Keep v6_package_flow_enabled default-off.
[ ] Enable only for trusted operator deployments.
[ ] Verify operator role and run authorization before every generate/review/retrieve action.
[ ] Store generated packages only in run-local operator-private storage.
[ ] Return metadata-only JSON for status/review surfaces.
[ ] Never expose rows, spatial payload bodies, hashes, local filesystem paths, or package internals in public responses.
[ ] Keep provider request submission manual and separate.
[ ] Treat outputs as desk-based shortlist/review aids, not proof or authorization.
```

## Current Gaps After This Checkpoint

- Browser end-to-end automation is still manual smoke only.
- Operator deployment docs still need environment-specific values.
- The real Earth Engine execution path still depends on configured credentials and runtime authorization.

## Next Step

```text
V6-READY-FREEZE-1: review final docs, run full regression, and freeze the V6 real package workflow checkpoint.
```
