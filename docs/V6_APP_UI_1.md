# V6-APP-UI-1 Frontend Package Flow

## Current Status

V6-APP-UI-1 adds the frontend generate/review/retrieve UI wired to the backend V6 package flow.

Implemented now:

- frontend V6 package API client;
- operator token forwarding;
- generate package action;
- review metadata action;
- retrieve ZIP action;
- metadata-only package status panel;
- backend denial and unavailable states;
- panel mounted in the existing operator private section;
- frontend contract tests.

## Added Files

```text
frontend-v2/src/app/api/v6PackageFlow.ts
frontend-v2/src/app/components/V6PrivatePackagePanel.tsx
tests/unit/test_v6_app_ui_contract.py
```

## Updated Files

```text
frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx
```

## UI Behavior

The V6 panel appears in the operator private section and uses the same operator access token context as the private overlay preview.

The panel has three actions:

- Generate package;
- Review metadata;
- Retrieve ZIP.

The panel displays metadata only: outcome, readiness, validation status, payload count, ZIP entry count, issue count, warning count, package filename, and category counts.

## Safety Rules

- The browser never renders package rows.
- The browser never renders spatial payload bodies.
- The browser forwards an operator bearer token only when one is present.
- Denied and unavailable states are displayed as generic status messages.
- Retrieval uses the private backend route and starts only from an authorized browser session.

## Still Not Done

- browser end-to-end test through a running app server;
- production UX polish;
- operator docs for enabling the package flow flag.

## Next Step

```text
V6-FINAL-WIRING-1: add final backend-to-frontend smoke documentation and full regression checklist.
```

## Checklist

- [x] Add V6 package frontend API client.
- [x] Add generate action.
- [x] Add review action.
- [x] Add retrieve action.
- [x] Forward operator token.
- [x] Add metadata-only status panel.
- [x] Mount panel in operator private section.
- [x] Add frontend contract tests.
- [ ] Add browser end-to-end smoke test.
- [ ] Add operator enablement runbook.
- [ ] Add full regression checklist.
