# Results refresh root cause — 2026-08-15

## Observed failure

A completed run can show generated classifier artifacts in the Overview output list while both Classifier Results and NB Results still show unavailable until the user manually refreshes or reopens the run.

The browser screenshots demonstrated this exact sequence: the run header was already `Done`, the output list contained `classifications.csv`, but both Results panels still showed unavailable; reopening/refreshing then made the same run display its classifier and NB rows.

## What was wrong with the earlier fixes

PR #66 and PR #67 refreshed the child Results panels based only on run state. That was not a strong enough synchronization point. A run can become `done` before the classifier and NB read paths are visible to the browser, so a one-time remount at `done` can still fetch too early and preserve the stale unavailable state.

## Correct repair

`ClassifierResultsPanel` now separates two checks:

1. poll run detail until the run is `done`;
2. after `done`, poll the actual result read APIs:
   - classifier summary fetch;
   - NB results fetch, requiring a status other than `not_available`.

The wrapper remounts the existing Results children only when those read paths become demonstrably ready. If classifier and NB become ready at different moments, the readiness mask allows another remount when the newly ready result appears.

The readiness polling is bounded and does not alter any calculation.

## Protected scope

No changes to:

- classifier calculations;
- Class A–J logic;
- classifier score values;
- Option 5 calculations or presentation;
- NB formulas;
- Numerical Depth / calibrated depth work;
- Results table content or labels.

The only behavior changed is when the already-existing Results panels refetch completed-run outputs.
