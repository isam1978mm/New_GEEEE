# V6-APP-UI-1 Frontend Package Flow

## Current Status

`V6` is legacy/internal naming for the app's Paid Imagery Export Package.

This feature remains in scope. It generates an offline export package for manual operator use outside the app. It is not a live ordering service or external provider integration.

V6-APP-UI-1 adds the frontend generate/review/retrieve UI wired to the backend package flow.

Current user-facing name should be one of:

```text
Paid Imagery Export Package
Imagery Export Package
```

Implementation note: `V6` remains an internal compatibility label for routes, filenames, paths, and tests where needed. Do not rename internal V6 compatibility names just because the visible UI wording changed.

Implemented now:

- frontend package API client;
- operator token forwarding;
- user-facing package panel;
- generate package action;
- review package metadata action;
- retrieve package ZIP action;
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

Recorded result at the original checkpoint:

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

The export package panel appears in the operator private section and uses the same operator access token context as the private overlay preview.

The panel has three actions:

- generate export package;
- review package metadata;
- retrieve package ZIP.

The panel displays metadata only: outcome, readiness, validation status, payload count, ZIP entry count, issue count, warning count, package filename, and category counts.

## Safety Rules

- The browser never renders package rows.
- The browser never renders spatial payload bodies.
- The browser forwards an operator bearer token only when one is present.
- Denied and unavailable states are displayed as generic status messages.
- Retrieval uses the private backend route and starts only from an authorized browser session.
- Provider request submission remains manual and outside the app.

## Current Follow-Up Work

The audit fixing plan tracks the remaining UI work:

```text
docs/AUDIT_FIX_PLAN_STUB.md
```

Relevant checklist items:

- use user-facing name `Paid Imagery Export Package` or `Imagery Export Package`;
- disable retrieve action when validation is not OK;
- keep UI/review responses metadata-only;
- do not imply live ordering or automatic imagery download.

## Checklist

- [x] Add package frontend API client.
- [x] Add user-facing package panel title.
- [x] Add generate package action.
- [x] Add review package metadata action.
- [x] Add retrieve package ZIP action.
- [x] Forward operator token.
- [x] Add metadata-only status panel.
- [x] Mount panel in operator private section.
- [x] Add frontend contract tests.
- [x] Add browser end-to-end smoke test.
- [x] Record local E2E validation: 9 passed.
- [ ] Rename visible panel/buttons to export-package wording.
- [ ] Disable retrieve action unless validation is OK.
- [ ] Add operator enablement runbook.
- [ ] Add full regression checklist.
