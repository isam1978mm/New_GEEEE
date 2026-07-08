# V6 / Imagery Export Package Scope

## Current Operator Decision

The export package feature stays in scope.

It is an offline package export that the operator can use outside the app when preparing an imagery request. It is not a live ordering service.

Do not remove this feature. Do not mark it deprecated, parked, or out of current app work.

## Correct Name

Use this user-facing name:

```text
Imagery Export Package
```

`V6` is legacy internal naming. It may remain in module names temporarily, but docs and UI should explain the product as an export package.

## Product Boundary

In scope:

- candidate-zone package files;
- quote/template CSV files;
- summary text;
- inventory JSON;
- validation report;
- ZIP export;
- backend generate/review/retrieve flow;
- frontend metadata-only review panel.

Out of scope:

- live external service integration;
- automatic ordering;
- payment flow;
- automatic imagery download.

## Provenance Rule

The old external V6 notebook/package source remains unresolved. Therefore app-generated package rows must carry honest provenance.

Generated scores, request zones, quote rows, and maps must not be represented as frozen notebook parity unless the original source is supplied and verified.

## Fixing Plan

### P0: Package readiness honesty

- `package_ready` must be true only after OK validation.
- Invalid validation must return `package_ready=false`.
- UI must block ZIP retrieval when validation is not OK.

### P0: ZIP/report pairing

- Pair ZIP and validation report by the same generation token.
- Reject mismatched ZIP/report pairs.

### P1: Provenance fields

- Record package provenance.
- Record score basis.
- Record geometry basis.
- Label fallback score or fallback geometry when used.
- Do not claim frozen notebook parity unless the source is verified.

### P1: UI wording

- Panel title should describe an export package, not a live service.
- Use generate/review/retrieve export wording.
- Keep UI metadata-only.

### P1: Placeholder map honesty

- If the map file is placeholder content, mark it as placeholder in inventory and validation report.

## Files To Inspect

```text
app/services/v6_app_flow.py
app/services/v6_real_package.py
app/services/v6_local_package_input.py
app/services/v6_package_validator.py
frontend-v2/src/app/components/V6PrivatePackagePanel.tsx
frontend-v2/src/app/api/v6PackageFlow.ts
docs/V6_REAL_PACKAGE_1.md
docs/V6_FINAL_WIRING_1.md
docs/V6_APP_FLOW_1.md
docs/V6_APP_UI_1.md
```

## Verification

```powershell
python -m pytest tests/unit/test_v6_app_flow.py tests/unit/test_v6_real_package.py tests/unit/test_v6_local_package_input.py tests/unit/test_v6_package_validator.py -q
cd frontend-v2
npm run build
```

## Done Criteria

- Feature is documented as in scope.
- Feature is documented as offline export only.
- UI uses export-package wording.
- Readiness depends on OK validation.
- ZIP/report generations match.
- Provenance is recorded.
- Tests cover the behavior.

Do not remove this feature.
