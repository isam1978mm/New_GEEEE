# V6.1-E2E-EXPAND-1-PLAN

## Status

Planning/checklist only.

Do not implement Playwright changes in this task.

The frozen V6 checkpoint remains unchanged. This task makes no frozen V6 generation changes, no scoring changes, no request-zone package-shape changes, and no generated artifact changes.

## Goal

Plan the browser E2E expansion for the operator-only V6 package flow before writing the Playwright implementation.

The implementation track will expand coverage around negative and recovery states while preserving the existing success-path E2E.

## Scenario gates

### Scenario 0 - existing success path baseline

Keep the existing V6 happy path intact:

1. operator panel is visible;
2. V6 package generation succeeds with mocked safe metadata;
3. metadata review succeeds;
4. ZIP retrieval succeeds;
5. no private rows or spatial payload bodies are rendered.

### Scenario 1 - disabled rollback state

Verify the UI handles the V6 package flow being disabled and shows a safe operator message.

### Scenario 2 - unauthenticated denied state

Verify the UI handles a generic denied response when no operator session is accepted.

### Scenario 3 - wrong role denied state

Verify the UI handles a generic denied response when the actor is missing the operator role.

### Scenario 4 - run not authorized state

Verify the UI handles a generic denied response when the actor is not authorized for the selected run.

### Scenario 5 - unavailable package state

Verify the UI shows unavailable when package inputs or generated package metadata are not present.

### Scenario 6 - invalid package input state

Verify the UI shows invalid input state without leaking private input content.

### Scenario 7 - retrieval failure state

Verify the UI reports retrieval failure when the ZIP request fails after metadata review.

### Scenario 8 - observability-safe assertions

Verify that mocked responses and UI assertions stay metadata-only.

## Implementation rules for the next track

- Create a separate Playwright spec or clearly separated describe block.
- Use mocks only.
- Use exact locators.
- Use safe fake run IDs and safe fake filenames.
- Keep all payload bodies synthetic and non-spatial.
- Do not weaken the existing success-path E2E.
- Keep `npm run e2e:v6` passing.
- Update docs after implementation.

## Safety rules

- No real spatial values in tests.
- No real V6 artifacts in repo.
- No auth secrets in tests or logs.
- No private rows or spatial payload bodies rendered in UI.
- Only safe metadata assertions are allowed.

## Validation for this plan

```powershell
python -m pytest tests/unit/test_v6_e2e_contract.py -q
python -m pytest tests/unit/test_v6_1_e2e_expand_plan_contract.py -q
```

## Validation for the future implementation track

```powershell
cd C:\Dev\New_GEE\frontend-v2
npm run e2e:v6
```

## Next track

V6.1-E2E-EXPAND-1-IMPLEMENT
