# Depth Private Record Intake Execution Plan

Status: implementation complete on `main`; targeted and full-suite execution are pending on the owner checkout.

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

## Verification commands

Run from an updated `main` checkout:

```powershell
python -m pytest tests/unit/test_depth_calibration_record_intake.py -v
python -m pytest tests/unit/test_depth_calibration_pack_tools.py -v
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
python -m pytest tests/unit -q
```

This execution environment could not clone the repository because outbound network access was unavailable. The committed files received a source-level review, but the owner checkout remains the authoritative test runner.

## First real-record workflow

After tests pass:

```powershell
python .\scripts\add_depth_calibration_record.py --create-template
```

Edit the private `record_intake.json` file locally, then dry-run:

```powershell
python .\scripts\add_depth_calibration_record.py
```

Only after a successful dry-run:

```powershell
python .\scripts\add_depth_calibration_record.py --write
```

Then validate the whole private pack. Do not use `--write` with invented, guessed, app-derived, or notebook-derived depth labels.

## Completion gate

The software slice is complete when its targeted tests and the full unit suite pass. Depth estimation remains blocked until real records are entered, the pack is finalized, and the relative-depth scientific experiment passes untouched-site validation.

## Checklist

- [x] Confirm calibration-data population is the next rollout step.
- [x] Define a local-only, dry-run-first intake workflow.
- [x] Implement the intake utility.
- [x] Add unit tests.
- [x] Document the owner-local workflow.
- [x] Complete source-level review.
- [ ] Run targeted intake tests.
- [ ] Run existing depth-pack and C1 privacy tests.
- [ ] Run the full unit suite.
- [ ] Record results.
- [ ] Create the first blank private intake payload.
- [ ] Enter real private records outside Git.
- [ ] Finalize and validate the populated pack.
