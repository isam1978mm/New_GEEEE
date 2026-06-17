# Private I2 readiness validator result

Status: validation passed

This document records aggregate-only output from `scripts/validate_private_i2_readiness.py`.

No private I2 row contents are included.

No private identifiers are included.

No source payload contents are included.

No model step was started.

No inference step was started.

## Command

```text
python scripts/validate_private_i2_readiness.py
```

## Aggregate validator result

| Metric | Value |
| --- | ---: |
| Status | validation_passed |
| Readiness decision | ready_for_private_training_later |
| Total rows | 868 |
| Expected total rows | 868 |
| Validator run on real data | true |
| Training started | false |
| Inference started | false |
| Duplicate sample ID count | 0 |
| Duplicate chip ID count | 0 |
| Group leakage detected | false |
| Unknown label count | 0 |
| Unknown split count | 0 |

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

## Count checks

All count checks passed:

```text
total_rows_match
rows_by_source_match
rows_by_label_match
rows_by_split_match
summary_status_match
summary_i2_rows_written_match
manifest_row_count_match
source_inventory_total_match
split_summary_present
leakage_report_present
```

## Decision

```text
ready_for_private_training_later
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
[x] dataset readiness validator design/check
[x] dataset readiness validator run on private I2 pack
```

## Current final status

Private I2 readiness phase is complete.

The private I2 pack passed the readiness validator.

H3 training has not started.

H4 inference has not started.

Any model work requires a separate explicit approval.
