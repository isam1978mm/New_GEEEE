# Plan D D8 Closeout — 2026-07-21

Status: Plan D8 lower-severity reliability cleanup is complete.

## Completed items

```text
D8.1 compatibility-only classifier IDs are explicitly quarantined
D8.2 core class reachability and compatibility boundaries are test-protected
D8.3 categorical WorldCover class codes are not averaged
D8.4 worldcover_class is reduced with categorical mode
D8.5 unsupported notebook-only raster families are explicitly registered as missing, partial, deferred, or unverified
```

## Classifier vocabulary boundary

The shared neutral compatibility vocabulary remains `Class_A` through `Class_N` because private parity and experimental modules rely on it.

The normal core selector is now explicitly limited to:

```text
Class_A through Class_J
```

Compatibility-only IDs are:

```text
Class_K through Class_N
```

The module validates that the two groups are disjoint and cover the declared vocabulary. The normal core classifier fails safely if a compatibility-only ID is ever selected.

Verification:

```text
pull_request = 10
head_commit = cb0a6aea0763a8d5c696355768083f1115b29471
merge_commit = c36d0ebb258369ff61b755352d14297c78e2770f
ci_run = 1341
ci_conclusion = success
```

CI passed the full suite and all repository safety scanners.

## Categorical WorldCover boundary

Continuous V6 feature bands use mean reduction. `worldcover_class` uses categorical mode and is merged by stable cell identity. Missing, duplicate, unexpected, or grid-inconsistent rows fail safely.

Verification:

```text
pull_request = 9
merge_commit = 89336dd6e97bcacceb00dce4ba00babfa4bdbbd0
ci_run = 1338
ci_conclusion = success
```

## Unsupported notebook-only behavior

`app/pipeline/parity/missing_rasters.py` and `docs/MISSING_RASTER_FAMILIES_CONTRACT.md` already provide the D8.5 contract. Missing or partial notebook families are recorded with explicit implementation status, blocker, and next action. No synthetic default raster is silently substituted.

## Boundary

This closeout improves software truthfulness and reliability only. It does not validate physical-world conclusions, fit a depth model, or enable depth output.

```text
app_depth_enabled = false
```

## Next phase

Continue Plan D7 data-quality handling, beginning with per-pixel Sentinel-2 cloud masking and valid-observation QA.
