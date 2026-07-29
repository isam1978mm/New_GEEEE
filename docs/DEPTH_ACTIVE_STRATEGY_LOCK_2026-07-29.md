# Numerical depth active strategy lock — 2026-07-29

## Authority

This document records the user-approved active strategy after a session incorrectly described Option 3 as active.

It is the controlling strategy-status document for future sessions unless the user explicitly changes the plan.

## Active plan

```text
Active Track A = Option 5 — Change Measurement Target
Active Track B = Option 1 — Global Numerical Depth
Standby Track C = Option 4 — Local AOI Calibration
Option 3 — Complete Candidates = NOT ACTIVE
Option 2 — Radar Ordering Test = completed and closed as inconsistent
```

## What each active track means

### Track A — Option 5 now

The app may provide useful radar outputs such as:

- anomaly score;
- surface-change or comparison indicators when actually measured;
- settlement or disturbance indicators when supported;
- zone comparison.

Every such output must remain clearly labelled **not depth**.

The implemented output is `Radar anomaly review — NOT DEPTH`.

### Track B — Option 1 continues

Continue the evidence-first search for independent measured sites needed for a future transferable numerical-depth model.

Option 1 requires:

- final measured numerical depths;
- numerical uncertainty, tolerance, or survey accuracy;
- coordinate-tied polygons;
- comparable radar-facing surfaces;
- confirmed controls where required;
- stable Sentinel-1 periods;
- independent train, validation, and holdout site groups.

Until enough evidence passes:

```text
Global numerical depth = disabled
Training = not started
Usable calibration rows = 0
```

### Track C — Option 4 waits

Option 4 remains available but inactive.

It may start only when one AOI has a complete local calibration package containing:

- measured shallow and deep polygons;
- a confirmed control;
- exact coordinates;
- comparable surfaces;
- sufficient clean support;
- a stable observation period.

## Critical interpretation rule

Completing, recovering, or reviewing a strong candidate does **not** activate Option 3.

Candidate work such as Tyrone, Aurora, Aitik, Faro, Detour, or another evidence site is classified as **Option 1 evidence research** when its purpose is to contribute measured evidence toward the global transferable-depth model.

Option 3 becomes active only if the user explicitly says to switch to or proceed with `Option 3 — Complete Candidates`.

Historical filenames, PR titles, or documents containing `Option 3` do not override this rule. Tyrone records can remain pending or under review without making Option 3 an active track.

## Prohibited future misstatement

Do not report any of the following unless the user explicitly changes the strategy:

- `Option 3 is the foreground route`;
- `Option 1 is being executed through Option 3`;
- `the active plan is Option 1 + Option 3`;
- `candidate recovery automatically means Option 3 is active`.

The correct wording is:

> The approved plan is Option 5 now plus Option 1 continuing, with Option 4 available but inactive. Option 3 is not active. Candidate evidence reviews are part of Option 1 unless the user explicitly changes the plan.

## Current combined result

```text
App provides useful anomaly/change results now = yes
App claims anomaly is depth = no
Option 1 depth research continues = yes
Option 4 remains available = yes
Option 3 active = no
Tyrone records request continues = yes
Numerical depth enabled now = no
```

## Required startup check for every next session

Before continuing depth work, the next session must:

1. read this document;
2. state the active strategy exactly;
3. classify the current candidate work under Option 1 unless the user explicitly selected Option 3;
4. preserve Option 5's no-depth labels;
5. keep Option 4 inactive until a complete AOI package exists;
6. never change the selected strategy by inference.

## Change control

Only an explicit user instruction may activate, pause, replace, or combine canonical options.

A handoff, PR title, candidate name, or assistant interpretation cannot change the selected strategy.
