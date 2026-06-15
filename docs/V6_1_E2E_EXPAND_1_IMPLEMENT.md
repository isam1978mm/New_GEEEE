# V6.1-E2E-EXPAND-1-IMPLEMENT

## Status

Done and tested.

## Scope

Expanded the existing V6 browser E2E coverage using mocked responses only. This task did not change V6 scoring, generation math, request-zone package shape, or generated artifact contents.

## Implemented checks

The Playwright V6 package flow spec now covers:

- existing success baseline;
- disabled rollback denial;
- unauthenticated denial before operator session;
- wrong-role denial;
- run-not-authorized denial;
- unavailable package state;
- invalid package input state;
- retrieval failure after metadata review;
- metadata-only/safe assertion guardrails.

## Frontend behavior fix

The V6 package API client now preserves backend `invalid_package_inputs` JSON responses even when the HTTP status is non-OK, so the UI can show the intended invalid-input operator message instead of collapsing the response into a generic temporary-unavailable state.

## Safety boundaries

- Uses safe fake run IDs, fake tokens, and fake filenames.
- Uses mocked metadata-only responses.
- Does not commit real V6 artifacts.
- Does not render private rows, package input bodies, raw coordinate fields, or spatial payload bodies.
- Does not alter backend V6 generation/scoring/request-zone logic.
- Keeps D1/D2/D3 operator-only private preview parked separately as issue #2.

## Validation

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_v6_1_e2e_expand_plan_contract.py -q

cd C:\Dev\New_GEE\frontend-v2
npm run e2e:v6
```

Observed local result:

- `python -m pytest tests/unit/test_v6_1_e2e_expand_plan_contract.py -q` -> 5 passed, 1 `.pytest_cache` access warning.
- `npm run e2e:v6` -> 9 passed.

## Final commits

- Implementation: `899aa61`
- Strict-mode assertion fix: `0b09baa`
