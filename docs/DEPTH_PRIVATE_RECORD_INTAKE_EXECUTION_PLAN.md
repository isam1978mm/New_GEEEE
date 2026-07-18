# Depth Private Record Intake Execution Plan

Status: implementation and software verification complete on `main`; real private calibration records remain absent.

## Purpose

The depth project is blocked because the private calibration pack contains no real independently measured or independently documented records. The next safe repository task is to make those records easier to enter without weakening the dataset contract or exposing private values.

This work does not fit a model, add a pipeline stage, enable a frontend panel, or produce a depth estimate.

## Implemented scope

Added one local-only intake utility:

```text
scripts/add_depth_calibration_record.py
```

The utility now:

1. creates a blank private JSON intake payload when requested;
2. reads a completed payload from outside Git;
3. requires a complete calibration record with the existing CSV schema;
4. requires an evidence-source row when the source is not already indexed;
5. reuses the existing depth-pack validator rules for record, source, leakage, date, quality, and inclusion checks;
6. rejects duplicate record identifiers and conflicting source references;
7. runs as dry-run by default;
8. appends only with an explicit `--write` flag;
9. invalidates stale manifest counts and hashes after a successful write so re-finalization is required;
10. prints aggregate status only, never the private row, identifiers, coordinates, depths, or paths.

The calibration-pack README now contains the exact template, dry-run, write, validation, and finalization commands.

## Input payload

The private JSON payload has two top-level fields:

```json
{
  "record": {},
  "source": {}
}
```

`record` must contain every field from `validator.REQUIRED_COLUMNS`.

`source` must contain every field from `validator.SOURCE_COLUMNS` when the record's evidence source is new. It may be `null` when the same source reference already exists in `source_index.csv`.

The tool supplies no depth defaults. A known-depth positive must contain a user-provided independently supported depth and uncertainty. A confirmed negative must leave depth fields empty.

## Safety rules

- Dataset and payload paths must remain outside the repository.
- Default execution is dry-run.
- No app/notebook output may be used as the true depth label.
- Identifier fields must not contain coordinate-like values.
- The tool must not print private values.
- A write leaves the pack requiring manifest finalization and full validation.
- The current app output remains `not_available`.

## Added tests

`tests/unit/test_depth_calibration_record_intake.py` covers:

- template creation with blank private fields;
- dry-run validation with no writes;
- valid record and source append;
- existing-source reuse without duplication;
- duplicate record rejection;
- missing source-link rejection;
- coordinate-like identifier rejection;
- manifest invalidation after write;
- aggregate-only results containing no record identifier, source reference, depth value, or private path.

## Owner verification

The owner ran the targeted and complete unit suites on Windows with Python 3.13.5.

Observed results:

```text
private intake tests: 8 passed
existing depth-pack tests: 19 passed
C1 redaction-risk tests: 3 passed
full unit suite: 933 passed
failures: 0
warnings: 4 non-blocking
```

The warnings were existing numerical/raster warnings plus pytest cache-write access warnings. They did not affect the passing result.

The owner also created the blank private intake payload successfully. The following dry-run and write attempts returned:

```text
intake supports only known-depth positives and confirmed negatives
```

That refusal is expected because the newly created payload is blank. No record or source was written.

## First real-record workflow

The blank private payload now exists. Edit `record_intake.json` in the private calibration folder with one real independently supported positive or confirmed-negative record, then run:

```powershell
python .\scripts\add_depth_calibration_record.py
```

Only after a successful dry-run:

```powershell
python .\scripts\add_depth_calibration_record.py --write
```

Then validate the whole private pack. Do not use `--write` with invented, guessed, app-derived, or notebook-derived depth labels.

## Completion gate

The software slice is complete because its targeted tests and the full unit suite passed. Depth estimation remains blocked until real records are entered, the pack is finalized, and the relative-depth scientific experiment passes untouched-site validation.

## Checklist

- [x] Confirm calibration-data population is the next rollout step.
- [x] Define a local-only, dry-run-first intake workflow.
- [x] Implement the intake utility.
- [x] Add unit tests.
- [x] Document the owner-local workflow.
- [x] Complete source-level review.
- [x] Run targeted intake tests: 8 passed.
- [x] Run existing depth-pack and C1 privacy tests: 22 passed.
- [x] Run the full unit suite: 933 passed.
- [x] Record results.
- [x] Create the first blank private intake payload.
- [ ] Enter real private records outside Git.
- [ ] Finalize and validate the populated pack.
- [ ] Run the relative-depth scientific experiment.
