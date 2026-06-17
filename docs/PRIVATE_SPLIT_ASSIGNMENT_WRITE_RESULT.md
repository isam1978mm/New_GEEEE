# Private split assignment write result

Status: private local write completed

This document records aggregate-only output from `scripts/assign_private_splits.py --write`.

No private split assignment rows are included.

No private row contents are included.

No private identifiers are included.

No source payload contents are included.

No I2 pack was assembled.

No validator was run on real data.

No model or inference step was started.

## Command

```text
python scripts/assign_private_splits.py --write
```

## Private output folder family

```text
C:\Dev\New_GEE_PRIVATE\SPLITS
```

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| split_assignments.private.jsonl | .jsonl | 210828 |
| split_assignments.private.summary.json | .json | 1682 |
| split_leakage_report.private.json | .json | 331 |

## Summary result

| Metric | Value |
| --- | ---: |
| Status | private_split_assignments_written |
| Total rows | 868 |
| Expected total rows | 868 |
| Real split assignments written | 868 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Group leakage detected | false |
| Duplicate sample ID count | 0 |
| Duplicate chip ID count | 0 |

## Rows by source

| Source | Rows |
| --- | ---: |
| POS-01 | 217 |
| C05 | 217 |
| C06 | 217 |
| C07 | 217 |

## Rows by label

| Label | Rows |
| --- | ---: |
| Class_A | 217 |
| Class_Background | 217 |
| Class_HardNegative | 434 |

## Rows by split

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |

## Decision

```text
private_split_assignments_written_outside_git
```

## Current item checklist

```text
Private split policy path

[x] kickoff
[x] split/group leakage rules
[x] train/val/test/holdout policy
[x] private split assignment script design
[x] private split assignment dry-run
[x] private split assignment write outside Git
[ ] I2 assembly plan       ← NEXT
```

## Current final status

Private split assignments exist outside Git.

The stronger I2 row set exists outside Git.

I2 assembly is not started.

The readiness validator has not been run on real data.

Next phase is I2 assembly planning.
