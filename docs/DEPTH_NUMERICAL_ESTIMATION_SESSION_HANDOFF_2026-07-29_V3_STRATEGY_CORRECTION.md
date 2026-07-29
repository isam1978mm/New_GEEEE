# Numerical depth estimation — session handoff — 2026-07-29 V3 strategy correction

## Read this first

This document corrects the strategy classification in `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29_V2.md`.

V2 remains useful for candidate evidence, workflow history, documentary gates, and operational details. However, any V2 wording that describes Option 3 as active or as the foreground strategy is superseded by this document.

The permanent strategy lock is:

`docs/DEPTH_ACTIVE_STRATEGY_LOCK_2026-07-29.md`

## Correct active plan

```text
Active Track A = Option 5 — Change Measurement Target
Active Track B = Option 1 — Global Numerical Depth
Standby Track C = Option 4 — Local AOI Calibration
Option 3 — Complete Candidates = NOT ACTIVE
Option 2 — Radar Ordering Test = completed and closed as inconsistent
```

## Correction to the previous handoff

The following V2 statement is incorrect and must not be repeated:

> Option 3 — Complete Candidates: Tyrone Dam 3X is the current foreground route.

The correct interpretation is:

> Tyrone, Aurora, Aitik, Faro, Detour, and similar candidate reviews are Option 1 evidence research when their purpose is to collect independent evidence for the global transferable-depth model. Reviewing a near-complete candidate does not activate Option 3.

Historical PR titles or filenames containing `Option 3` describe earlier work or naming. They do not make Option 3 part of the active plan.

## Approved combined plan

### Track A — Option 5 now

Keep the useful radar anomaly/change-oriented app output available, with all outputs clearly labelled **not depth**.

The implemented app wording remains:

`Radar anomaly review — NOT DEPTH`

Do not turn anomaly, PCA score, classifier output, or synthetic features into metres or centimetres.

### Track B — Option 1 continues

Continue the strict evidence-first search for independent measured calibration sites.

A site contributes only after passing the required gates for:

- final measured numerical depth;
- numerical uncertainty or survey accuracy;
- exact coordinate-tied geometry;
- comparable radar-facing surfaces;
- a second numerical condition or confirmed control as required;
- sufficient clean interior;
- a stable Sentinel-1 period;
- split isolation across train, validation, and holdout groups.

Current state:

```text
usable calibration rows = 0
training started = no
global numerical depth ready = no
app depth enabled = no
```

### Track C — Option 4 waits

Keep Option 4 available but inactive.

It can start only when one AOI has measured shallow and deep polygons, a confirmed control, exact coordinates, comparable surfaces, sufficient clean support, and a stable observation period.

## Option 3 change-control rule

Do not activate Option 3 by inference.

Option 3 becomes active only after the user explicitly says to proceed with, switch to, or activate `Option 3 — Complete Candidates`.

Until that happens:

```text
Option 3 active = no
candidate recovery under Option 1 = allowed
Tyrone records request = may continue
broad/global evidence research under Option 1 = active
```

## Required next-session opening

At the beginning of the next session, state:

> The approved plan is Option 5 now plus Option 1 continuing, with Option 4 available but inactive. Option 3 is not active. Candidate evidence work is classified under Option 1 unless the user explicitly changes the plan.

Then continue the current evidence task without renaming or changing the selected strategy.

## User action required

None. The strategy correction is documented in the repository.
