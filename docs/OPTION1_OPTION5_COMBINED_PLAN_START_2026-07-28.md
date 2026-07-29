# Combined Option 1 + Option 5 plan start — 2026-07-28

## User-selected plan

Proceed on three controlled tracks:

1. **Option 5 now:** expose a defensible radar anomaly result already produced by the app.
2. **Option 1 continues:** keep collecting strict independent calibration evidence for possible future global numerical depth.
3. **Option 4 remains available:** activate only if one AOI supplies measured shallow and deep references, a confirmed control, exact geometry, comparable surfaces, sufficient clean support, and a stable observation period.

Option 3 remains on hold pending New Mexico EMNRD request `N000019-070026` for Tyrone Dam 3X records.

## Strategy interpretation lock — added 2026-07-29

The active plan is **Option 5 + Option 1**, with **Option 4 available but inactive**.

**Option 3 is not active.**

Reviewing, recovering, or completing a candidate such as Tyrone, Aurora, Aitik, Faro, or Detour is part of **Option 1 evidence research** when the purpose is to collect evidence for the global transferable-depth model. Candidate recovery does not automatically activate Option 3.

Option 3 may become active only after an explicit user instruction to switch to or proceed with `Option 3 — Complete Candidates`.

Do not describe the plan as `Option 1 through Option 3`, `Option 1 + Option 3`, or `Option 3 is the foreground route` unless the user explicitly changes the strategy.

The controlling strategy-status document is:

`docs/DEPTH_ACTIVE_STRATEGY_LOCK_2026-07-29.md`

## First Option 5 implementation slice

The app already computes PCA anomaly scores and writes these public-safe object summaries in `objects_index.csv`:

- `mean_anomaly`;
- `max_anomaly`;
- object and cluster identifiers;
- object area in pixels.

The first slice exposes those existing values in the run overview without changing the scientific pipeline.

### Approved wording

The output is labelled **Radar anomaly review — NOT DEPTH**.

It states that the score is:

- unitless;
- relative within the current run;
- useful only for ranking unusual objects for review;
- not a probability;
- not physical confirmation;
- not a measured change;
- not a depth estimate.

### Compatibility boundary

The established top-level panel heading remains exactly `Classifier Results`. The new radar-anomaly section is added inside that existing panel so older UI contracts and static-bundle checks continue to pass.

### Explicit exclusions

This slice does not:

- add a depth stage;
- create metres or centimetres;
- train a model;
- create calibration rows;
- claim that anomaly caused or reveals depth;
- claim temporal change where no temporal change measurement exists;
- expose geographic coordinates or private paths;
- modify Earth Engine processing.

## Option 1 parallel track

Option 1 remains a documentary and validation track. Its next work is a bounded candidate batch requiring:

- final measured depth;
- numerical uncertainty;
- coordinate-tied polygons;
- matched radar-facing surfaces;
- confirmed controls;
- stable Sentinel-1 periods;
- independent train, validation, and holdout site groups.

No training begins until a real calibration package passes the repository validator.

## Current status

```text
Option 5 anomaly UI source = implemented and merged
Option 5 production SPA build = passed and synchronized
Option 5 temporal change output = not implemented
Option 1 evidence search = active in parallel
Tyrone records request = pending; this does not activate Option 3
Option 3 complete-candidates strategy = not active
Option 4 local AOI = available but inactive
usable calibration rows = 0
training started = no
numerical depth ready = no
app depth enabled = no
full repository CI = passed at Option 5 merge
```

## Verification required before merge

1. Frontend production build passes.
2. Python contract tests pass.
3. Existing full CI passes.
4. The built SPA is regenerated if the repository requires committed `frontend-v2/dist` assets.
5. Review confirms every visible anomaly statement preserves the no-depth boundary.
