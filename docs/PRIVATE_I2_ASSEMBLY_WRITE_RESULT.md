# Private I2 assembly write result

Status: private local I2 pack assembled

This document records aggregate-only output from `scripts/assemble_private_i2_pack.py --write`.

No private I2 row contents are included.

No private identifiers are included.

No source payload contents are included.

No validator was run on real data.

No model or inference step was started.

## Command

```text
python scripts/assemble_private_i2_pack.py --write
```

## Private output folder family

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE
```

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| i2_leakage_report.private.json | .json | 208 |
| i2_manifest.private.json | .json | 234 |
| i2_source_inventory.private.json | .json | 200 |
| i2_split_summary.private.json | .json | 921 |
| i2_summary.private.json | .json | 1794 |
| i2_training_examples.private.jsonl | .jsonl | 979876 |

## Summary result

| Metric | Value |
| --- | ---: |
| Status | private_i2_pack_assembled |
| Total I1 rows loaded | 868 |
| Total split assignments loaded | 868 |
| Matched assignment count | 868 |
| Missing assignment count | 0 |
| Extra assignment count | 0 |
| I2 rows written | 868 |
| Validator run on real data | false |
| Training started | false |
| Inference started | false |
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

## Decision

```text
private_i2_pack_assembled_outside_git
```

## Current item checklist

```text
I2 assembly path

[x] private I1 rows ready
[x] private split assignments ready
[x] I2 assembly plan
[x] private I2 assembler script
[x] private I2 assembler dry-run
[x] private I2 pack assembled outside Git
[ ] dataset readiness validator design/check       ← NEXT
[ ] dataset readiness validator dry-run or run on private I2 pack
```

## Current final status

Private I2 pack exists outside Git.

The readiness validator has not been run on real data.

No model step has started.

No inference step has started.

Next phase is dataset readiness validator design/check.
