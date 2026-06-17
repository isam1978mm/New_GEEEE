# Private train/val/test/holdout policy

Status: policy defined for private split assignment design

This document defines the planned train/validation/test/holdout split policy for the stronger private I2 path.

No private rows are included.

No private identifiers are included.

No source payload contents are included.

No split assignment is written by this document.

No I2 pack is assembled by this document.

No validator is run by this document.

No model or inference step is started.

## Current row inventory

| Source | Role | Private I1 rows | Status |
| --- | --- | ---: | --- |
| POS-01 | positive | 217 | created outside Git |
| C05 | background | 217 | created outside Git |
| C06 | hard-negative | 217 | created outside Git |
| C07 | hard-negative | 217 | created outside Git |

Total private I1 rows available for stronger I2 planning:

```text
868
```

## Current item checklist

Current item:

```text
Private split policy path
```

Checklist:

```text
[x] kickoff
[x] split/group leakage rules
[x] train/val/test/holdout policy
[ ] private split assignment script design       ← NEXT
[ ] private split assignment dry-run
[ ] private split assignment write outside Git
[ ] I2 assembly plan
```

## Split names

The allowed split names are:

```text
train
val
test
holdout
```

No other split names should be introduced without a separate policy update.

## Split unit

The split unit is:

```text
group_id
```

All rows sharing the same `group_id` must remain in one split.

No `group_id` may appear in more than one split.

## Ratio policy

Planned split ratio:

| Split | Planned ratio | Purpose |
| --- | ---: | --- |
| train | 70% | model fitting later, after explicit approval |
| val | 10% | tuning/selection later |
| test | 10% | internal evaluation later |
| holdout | 10% | protected final private evaluation |

Because each current source has 217 rows, the initial per-source target is:

| Source | train | val | test | holdout | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| POS-01 | 152 | 22 | 22 | 21 | 217 |
| C05 | 152 | 22 | 22 | 21 | 217 |
| C06 | 152 | 22 | 22 | 21 | 217 |
| C07 | 152 | 22 | 22 | 21 | 217 |

Planned aggregate target:

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |
| total | 868 |

These counts are targets for the current 868-row inventory.

If group sizes later prevent exact matching, the split assignment script must preserve no-leakage rules first and report aggregate deviations.

## Source balancing rule

Each source family should be split independently before combining:

```text
POS-01
C05
C06
C07
```

This keeps each source family represented in every split where feasible.

## Label balancing rule

The split assignment must preserve label family balance as much as possible.

Current planned label families:

```text
Class_A
Class_Background
Class_HardNegative
```

The script must not change labels.

The script must not create new labels.

The script must not convert hard negatives into positives.

## Holdout rule

The holdout split is protected.

Holdout rows must not be used for model fitting or tuning.

Holdout rows must remain separate through later I2 readiness validation and any future model steps.

## Determinism rule

The split assignment must use:

```text
seed = 20260616
```

For the same input rows and same seed, the script must produce the same split assignment.

## Dry-run reporting rule

A dry-run split assignment may report only aggregate values:

```text
total rows
rows by source
rows by label
rows by split
rows by source and split
rows by label and split
missing required field counts
leakage check result
planned output file names
```

The dry-run must write zero files.

## Write output rule

A later approved write step may create private split-assigned files only outside Git.

Recommended private output folder:

```text
C:\Dev\New_GEE_PRIVATE\SPLITS
```

Recommended private files:

```text
split_assignments.private.jsonl
split_assignments.private.summary.json
split_leakage_report.private.json
```

## Stop conditions

Stop before any step that would:

```text
write private split assignments without approval
commit private row files
commit source datasets
assemble I2 without explicit approval
run validator before I2 exists
start model work
start inference work
change app/API/frontend code
```

## Decision

```text
private_train_val_test_holdout_policy_defined
```

## Next step

```text
Create private split assignment script design
```
