# Private I2 assembler dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/assemble_private_i2_pack.py`.

No private I2 files were written.

No private row contents are included.

No private identifiers are included.

No source payload contents are included.

No validator was run on real data.

No model or inference step was started.

## Command

```text
python scripts/assemble_private_i2_pack.py
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_ready |
| Total I1 rows loaded | 868 |
| Expected total I1 rows | 868 |
| Total split assignments loaded | 868 |
| Matched assignment count | 868 |
| Missing assignment count | 0 |
| Extra assignment count | 0 |
| I2 rows written | 0 |
| Validator run on real data | false |
| Group leakage detected | false |
| Duplicate sample ID count | 0 |
| Duplicate chip ID count | 0 |
| Split inputs passed | true |

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

## Rows by source and split

| Source | train | val | test | holdout | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| POS-01 | 152 | 22 | 22 | 21 | 217 |
| C05 | 152 | 22 | 22 | 21 | 217 |
| C06 | 152 | 22 | 22 | 21 | 217 |
| C07 | 152 | 22 | 22 | 21 | 217 |

## Rows by label and split

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
| Assembly errors | none |
| Missing required field counts | none |
| Leakage check passed | true |
| Split inputs passed | true |

## Decision

```text
private_i2_assembler_dry_run_ready
```

## Next possible phase

The next possible phase is to assemble the private I2 pack outside Git using `--write`.

That phase will create private I2 pack files only.

It will not run the validator.
