# V6.1-E2E-EXPAND-1-IMPLEMENT

## Status

Implemented; pending local validation.

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

## Validation

```powershell
cd C:\Dev\New_GEE\frontend-v2
npm run e2e:v6
```

Expected result: all V6 Playwright tests pass.
