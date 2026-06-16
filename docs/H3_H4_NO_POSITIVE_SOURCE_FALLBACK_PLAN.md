# H3/H4 No Positive Source Fallback Plan

This document explains what to do if no approved positive independent-evidence source can be found.

This is documentation only.
It does not create data, assemble I2, start training, start inference, add dependencies, or change app behavior.

## Current blocker

```text
H3 needs positive independent evidence.
C05/C06/C07 are useful only for negative/background or hard-negative roles.
C01 is possible positive evidence, but it is not approved yet.
```

Plain meaning:

```text
The project has good negative examples for later.
The project still does not have trusted positive examples.
Without trusted positive examples, real H3 training should not start.
```

## If no positive source is found

The safe options are:

```text
Option 1: Keep H3/H4 blocked and pause ML training.
Option 2: Continue app use as a screening/ranking tool only.
Option 3: Build a private evidence-intake workflow, but do not train yet.
Option 4: Scout more positive sources later.
Option 5: Use synthetic/public data only for pipeline tests, not real model claims.
Option 6: Assemble negative/hard-negative readiness notes only, but do not create a real I2 training pack until positive evidence exists.
```

## Option 1 — Pause H3/H4

```text
status: safest default
```

Use this if no trusted positive source is available.

Result:

```text
H3 training: blocked
H4 inference: blocked
I2 assembly: not authorized
```

## Option 2 — Use app as screening only

The app can still produce candidate rankings and operator review outputs.

But:

```text
candidate zone != label
classifier score != truth
screening output != training dataset
```

This path is useful for human review, not for real supervised training.

## Option 3 — Build evidence intake later

A future private workflow can help the operator collect evidence safely.

It should collect only private operator-approved records outside Git.

It should not expose sensitive material publicly.

It should not mark anything as training-ready until the existing readiness validator passes.

## Option 4 — Scout more positive sources later

Future scouting should look for:

```text
field-verified records
authoritative external records
expert-adjudicated independent evidence
independently produced reference labels with clear method and rights
```

Reject as positive labels:

```text
D1 outputs
Phase F scores
candidate zones
same-app-layer signals
weak imagery-only signals without independent review
```

## Option 5 — Synthetic/public data for pipeline tests only

Synthetic or public non-sensitive examples can test code paths.

They cannot prove real H3 model quality.

Allowed meaning:

```text
pipeline test only
schema test only
validator test only
```

Not allowed meaning:

```text
real training proof
real H3 unlock
real H4 unlock
```

## Option 6 — Negative/hard-negative preparation only

C05/C06/C07 can help later negative/background or hard-negative roles.

They do not unlock H3 alone.

A later task may prepare negative-source manifests, but only after user approval and outside Git.

That task still cannot become a full I2 training pack until a positive source exists.

## Recommended path while waiting

While the operator checks positive-source options:

```text
[ ] keep H3/H4 blocked
[ ] keep I2 assembly not authorized
[ ] do not train
[ ] do not infer
[ ] do not treat app candidates as truth
[ ] prepare a short list of possible positive sources
[ ] for each possible positive source, answer ownership / permission / method / independence / redaction questions
```

## Final rule

```text
No positive independent evidence -> no real H3.
No approved H3 model -> no real H4.
```
