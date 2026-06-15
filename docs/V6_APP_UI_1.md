# V6-APP-UI-1 Frontend Package Flow

## Current Status

V6-APP-UI-1 adds the frontend generate/review/retrieve UI wired to the backend V6 package flow.

Current user-facing name:

```text
Paid Imagery Request Package
```

Implementation note: `V6` remains an internal compatibility label for routes, filenames, paths, and tests where needed. Do not rename internal V6 compatibility names just because the visible UI wording changed.

Implemented now:

- frontend V6 package API client;
- operator token forwarding;
- user-facing `Paid Imagery Request Package` panel title;
- `Generate request package` action;
- `Review package metadata` action;
- `Retrieve package ZIP` action;
- metadata-only package status panel;
- backend denial and unavailable states;
- panel mounted in the existing operator private section;
- frontend contract tests;
- browser end-to-end smoke test.

## Local Validation

```text
cd C:\Dev\New_GEE\frontend-v2
npm run e2e:v6
```

Result:

```text
9 passed
```

## Added Files

```text
frontend-v2/src/app/api/v6PackageFlow.ts
frontend-v2/src/app/components/V6PrivatePackagePanel.tsx
tests/unit/test_v6_app_ui_contract.py
```

## Updated Files

```text
frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx
frontend-v2/e2e/v6-package-flow.spec.ts
docs/LOCAL_PRIVATE_ROADMAP_CHECKLIST.md
docs/V6_APP_UI_1.md
```

## UI Behavior

The Paid Imagery Request Package panel appears in the operator private section and uses the same operator access token context as the private overlay preview.

The panel has three actions:

- Generate request package;
- Review package metadata;
- Retrieve package ZIP.

The panel displays metadata only: outcome, readiness, validation status, payload count, ZIP entry count, issue count, warning count, package filename, and category counts.

## Safety Rules

- The browser never renders package rows.
- The browser never renders spatial payload bodies.
- The browser forwards an operator bearer token only when one is present.
- Denied and unavailable states are displayed as generic status messages.
- Retrieval uses the private backend route and starts only from an authorized browser session.

## Still Not Done

- production UX polish;
- operator docs for enabling the package flow flag.

## Next Step

```text
D1 real new.ipynb reference freeze: freeze the real notebook outputs as the official private baseline outside Git.
```

## Checklist

- [x] Add V6 package frontend API client.
- [x] Add user-facing Paid Imagery Request Package panel title.
- [x] Add Generate request package action.
- [x] Add Review package metadata action.
- [x] Add Retrieve package ZIP action.
- [x] Forward operator token.
- [x] Add metadata-only status panel.
- [x] Mount panel in operator private section.
- [x] Add frontend contract tests.
- [x] Add browser end-to-end smoke test.
- [x] Record local E2E validation: 9 passed.
- [ ] Add operator enablement runbook.
- [ ] Add full regression checklist.
