# Private split assignment dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/assign_private_splits.py`.

No private split assignment file was written.

No private row contents are included.

No private identifiers are included.

No source payload contents are included.

No I2 pack was assembled.

No validator was run on real data.

No model or inference step was started.

## Command

```text
python scripts/assign_private_splits.py
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_ready |
| Seed | 20260616 |
| Total rows | 868 |
| Expected total rows | 868 |
| Real split assignments written | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Duplicate sample ID count | 0 |
| Duplicate chip ID count | 0 |
| Group leakage detected | false |

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

## Planned rows by split

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |

## Planned rows by source and split

| Source | train | val | test | holdout | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| POS-01 | 152 | 22 | 22 | 21 | 217 |
| C05 | 152 | 22 | 22 | 21 | 217 |
| C06 | 152 | 22 | 22 | 21 | 217 |
| C07 | 152 | 22 | 22 | 21 | 217 |

## Planned rows by label and split

| Label | train | val | test | holdout | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Class_A | 152 | 22 | 22 | 21 | 217 |
| Class_Background | 152 | 22 | 22 | 21 | 217 |
| Class_HardNegative | 304 | 44 | 44 | 42 | 434 |

## Check summary

| Check | Result |
| --- | --- |
| Load errors | none |
| Row count errors | none |
| Assignment errors | none |
| Missing required field counts | none |
| Duplicate sample IDs | none |
| Duplicate chip IDs | none |
| Group leakage | false |

## Decision

```text
private_split_assignment_dry_run_ready
```

## Next possible phase

The next possible phase is to write private split assignment files outside Git using `--write`.

That phase will create private split assignment files only.

It will not assemble I2.

It will not run the validator.
