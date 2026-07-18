# Depth Private Record Intake Execution Plan

Status: active implementation on `main`.

## Purpose

The depth project is blocked because the private calibration pack contains no real independently measured or independently documented records. The next safe repository task is to make those records easier to enter without weakening the dataset contract or exposing private values.

This work does not fit a model, add a pipeline stage, enable a frontend panel, or produce a depth estimate.

## Scope

Add one local-only intake utility:

```text
scripts/add_depth_calibration_record.py
```

The utility will:

1. create a blank private JSON intake payload when requested;
2. read a completed payload from outside Git;
3. require a complete calibration record with the existing CSV schema;
4. require an evidence-source row when the source is not already indexed;
5. reuse the existing depth-pack validator rules for record, source, leakage, date, quality, and inclusion checks;
6. reject duplicate record identifiers and conflicting source references;
7. run as dry-run by default;
8. append only with an explicit `--write` flag;
9. invalidate stale manifest counts and hashes after a successful write so re-finalization is required;
10. print aggregate status only, never the private row, identifiers, coordinates, depths, or paths.

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
- A write must leave the pack requiring manifest finalization and full validation.
- The current app output remains `not_available`.

## Planned tests

- template creation writes only blank fields outside Git;
- dry-run validates but writes nothing;
- valid write appends one record and one new source;
- an existing identical source may be reused without duplication;
- duplicate record identifiers are rejected;
- missing source linkage is rejected;
- coordinate-like identifiers are rejected through the existing validator;
- manifest hashes and aggregate fields are invalidated after a write;
- output contains no record identifier, source reference, depth value, or private path.

## Completion gate

This slice is complete when its targeted tests and the full unit suite pass. Even then, depth estimation remains blocked until real records are entered, the pack is finalized, and the relative-depth scientific experiment passes untouched-site validation.

## Checklist

- [x] Confirm calibration-data population is the next rollout step.
- [x] Define a local-only, dry-run-first intake workflow.
- [ ] Implement the intake utility.
- [ ] Add unit tests.
- [ ] Run targeted tests.
- [ ] Run the full unit suite.
- [ ] Record results.
- [ ] Enter real private records outside Git.
- [ ] Finalize and validate the populated pack.
