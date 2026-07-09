# V6-APP-FLOW-1 Backend Flow For Paid Imagery Export Package

## Current Status

`V6` is legacy/internal naming for the app's Paid Imagery Export Package.

This feature remains in scope. It generates an offline export package for manual operator use outside the app. It is not a live ordering service or external provider integration.

V6-APP-FLOW-1 adds the backend generate/review/retrieve flow for the package path.

Implemented now:

- default-off package-flow setting;
- operator/role/run authorization gate;
- run-local package input location;
- backend generate service;
- backend review service;
- backend package resolver;
- API routes under the operator router;
- metadata-only JSON responses;
- file response for the ZIP package only after authorization;
- unit tests.

The backend flow is implemented. Frontend UI was added later and is documented in `docs/V6_APP_UI_1.md`.

## Added Files

```text
app/services/v6_app_flow.py
app/api/v6_app_flow.py
tests/unit/test_v6_app_flow.py
```

## Updated Files

```text
app/config.py
app/api/operator_overlays.py
```

## Backend Flow

The backend expects a run-local package input file and writes generated package output in a run-local operator area.

The review endpoint returns metadata only.

The package retrieval endpoint returns the ZIP file only after the same authorization gates pass.

## Safety Rules

- Default-off unless `v6_package_flow_enabled` is true.
- Operator authentication is required.
- Operator role is required.
- Run authorization is required.
- Denied responses are generic.
- Denied requests do not read package inputs.
- JSON responses do not include rows, spatial payloads, hashes, or filesystem paths.
- Generated package files remain filesystem artifacts.
- Provider request submission remains manual and outside the app.

## Current Follow-Up Work

The audit fixing plan tracks the remaining backend correctness work:

```text
docs/AUDIT_FIX_PLAN_STUB.md
```

Relevant checklist items:

- `package_ready=true` only after OK validation;
- pair ZIP and validation report by one generation token;
- reject mismatched ZIP/report pairs;
- keep review responses metadata-only;
- add provenance labels in generated package data.

## Checklist

- [x] Add default-off package-flow setting.
- [x] Add operator access gate.
- [x] Add run-local input file location.
- [x] Add backend generate service.
- [x] Add backend review service.
- [x] Add backend package resolver.
- [x] Add operator API routes.
- [x] Mount routes through existing operator router.
- [x] Keep JSON responses metadata-only.
- [x] Add unit tests.
- [ ] Gate package readiness on OK validation.
- [ ] Pair ZIP and validation report by generation.
- [ ] Reject mismatched package generations.
