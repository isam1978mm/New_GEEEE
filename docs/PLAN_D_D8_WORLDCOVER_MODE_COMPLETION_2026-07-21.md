# Plan D D8 WorldCover Categorical Reduction Completion — 2026-07-21

Status: implemented, tested, and merged.

## Completed reliability items

```text
D8.3 categorical WorldCover class codes are no longer averaged
D8.4 worldcover_class is reduced with categorical mode
```

## Problem corrected

The V6 feature reducer previously applied `ee.Reducer.mean()` to every feature band. `worldcover_class` is an ESA WorldCover categorical code, so a mixed grid cell could produce an impossible intermediate value rather than a real class.

## Implementation

- continuous feature bands use `ee.Reducer.mean()`;
- `worldcover_class` uses `ee.Reducer.mode()`;
- the two reductions are merged using stable `cell_id` values;
- missing, duplicate, unexpected, or grid-inconsistent rows fail safely;
- output property names remain compatible with the existing row validator and scorer.

## Verification

```text
pull_request = 9
head_commit = 43c6a64cc71b0457cebfcc233ea3c0daacafa016
merge_commit = 89336dd6e97bcacceb00dce4ba00babfa4bdbbd0
ci_run = 1338
ci_conclusion = success
```

Successful workflow steps:

- dependency installation;
- focused safety tests;
- full test suite;
- forbidden `ee.Authenticate` scan;
- direct-file-streaming scan;
- notebook-safety scan.

## Boundary

This is a software reliability correction. It does not validate any physical interpretation, train a depth model, or enable depth output.

```text
app_depth_enabled = false
```
