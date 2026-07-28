# Combined Option 1 + Option 5 plan start — 2026-07-28

## User-selected plan

Proceed on three controlled tracks:

1. **Option 5 now:** expose a defensible radar anomaly result already produced by the app.
2. **Option 1 continues:** keep collecting strict independent calibration evidence for possible future global numerical depth.
3. **Option 4 remains available:** activate only if one AOI supplies measured shallow and deep references, a confirmed control, exact geometry, comparable surfaces, sufficient clean support, and a stable observation period.

Option 3 remains on hold pending New Mexico EMNRD request `N000019-070026` for Tyrone Dam 3X records.

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
Option 5 anomaly UI source = implemented on isolated branch
Option 5 temporal change output = not implemented
Option 1 evidence search = active in parallel
Option 3 Tyrone records = pending
Option 4 local AOI = available but inactive
usable calibration rows = 0
training started = no
numerical depth ready = no
app depth enabled = no
```

## Verification required before merge

1. Frontend production build passes.
2. Python contract tests pass.
3. Existing full CI passes.
4. The built SPA is regenerated if the repository requires committed `frontend-v2/dist` assets.
5. Review confirms every visible anomaly statement preserves the no-depth boundary.
