# Private split group leakage rules

Status: rules defined for split-policy design

This document defines the group and leakage rules for later private split assignment.

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
[ ] train/val/test/holdout policy       ← NEXT
[ ] private split assignment script design
[ ] private split assignment dry-run
[ ] private split assignment write outside Git
[ ] I2 assembly plan
```

## Core rule

The split unit is:

```text
group_id
```

Every row with the same `group_id` must be assigned to exactly one split.

A `group_id` must never appear in more than one split.

## Required no-leakage rules

A later private split assignment step must enforce:

```text
1. No group_id may cross train, val, test, or holdout.
2. No sample_id may appear in more than one split.
3. No chip_id may appear in more than one split.
4. No feature reference may appear in more than one split once real features exist.
5. Rows derived from the same private source reference must remain in one split if they share a group_id.
6. Split assignment must be deterministic from seed plus group_id.
7. Split assignment must be written only outside Git.
8. Repo-visible reporting must remain aggregate-only.
```

## Source balancing rule

The split policy should preserve source-family balance as much as possible.

Source families:

```text
POS-01 positive
C05 background
C06 hard-negative
C07 hard-negative
```

Each source should be split independently by group, then combined into the final private I2 split manifest.

This prevents one source family from being overrepresented in a single split.

## Positive and negative separation rule

Labels must not be changed by split assignment.

Split assignment must not convert negatives or hard negatives into positives.

Split assignment must not create new labels.

## Holdout protection rule

The holdout split is reserved for final private evaluation.

Holdout rows must not be used for training.

Holdout group identifiers must not appear in train, validation, or test.

## Determinism rule

The split assignment must use:

```text
seed = 20260616
```

The algorithm must be repeatable.

Running the same script on the same private I1 files with the same seed must produce the same split counts and the same private assignments.

## Aggregate-only reporting rule

Repo-visible docs may report only:

```text
total row count
row count by source
row count by label
row count by split
row count by source and split
leakage check pass/fail
missing field counts
```

Repo-visible docs must not include:

```text
sample_id
group_id
chip_id
features_ref
metadata_ref
source_record_ref
coordinates
polygon geometry
private row contents
```

## Validation checks required before write

The dry-run split assignment must check:

```text
required I1 files exist
required I1 fields exist
row counts match expected inventory
all rows have group_id
all rows have sample_id
all rows have label
all rows have source family
no duplicate sample_id
no duplicate chip_id unless intentionally grouped
no group_id crosses planned splits
all splits have at least one row from each source if feasible
```

Dry-run must create zero private outputs.

## Write boundary

A later approved write step may create private split-assigned files only outside Git.

Recommended private output family:

```text
C:\Dev\New_GEE_PRIVATE\SPLITS
```

Recommended files:

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
private_split_group_leakage_rules_defined
```

## Next step

```text
Define train/val/test/holdout policy
```
