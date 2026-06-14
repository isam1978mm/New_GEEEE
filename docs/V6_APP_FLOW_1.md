# V6-APP-FLOW-1 Backend Flow

## Current Status

V6-APP-FLOW-1 adds the backend generate/review/retrieve flow for the real V6 package path.

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

The flow is backend-only. Frontend UI work is still not done.

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
- Frontend UI is not added in this step.

## Still Not Done

- frontend generate button;
- frontend review panel;
- frontend package action;
- end-to-end UI tests.

## Next Step

```text
V6-APP-UI-1: add frontend generate/review/retrieve UI wired to the backend flow.
```

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
- [ ] Add frontend generate action.
- [ ] Add frontend review panel.
- [ ] Add frontend package action.
- [ ] Add end-to-end UI tests.
