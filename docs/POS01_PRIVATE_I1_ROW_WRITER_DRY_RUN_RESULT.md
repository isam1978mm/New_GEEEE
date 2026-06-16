# POS-01 private I1 row writer dry-run result

Status: dry-run passed

This document records the aggregate-only dry-run output from `scripts/pos01_write_private_i1_rows.py`.

No private source rows are included.

No private I1 JSONL rows were created.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Dry-run command

```text
python scripts/pos01_write_private_i1_rows.py
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_only |
| Accepted total | 233 |
| I1 rows ready total | 217 |
| Held back total | 16 |
| Real I1 rows created | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Training started | false |
| Inference started | false |

## File-level aggregate result

| Source file | Accepted count | I1 candidate count | Held back count |
| --- | ---: | ---: | ---: |
| unesco.csv | 211 | 195 | 16 |
| science-at-risk.csv | 22 | 22 | 0 |

## Planned aggregate mapping

| Planned mapping | Count |
| --- | ---: |
| Class_A | 217 |
| reviewed_independent | 217 |
| authoritative_external_dataset | 217 |
| LOCAL_SENSITIVE | 217 |
| unassigned split | 217 |

## Interpretation

The private row writer dry-run matches the earlier manual aggregate review.

Expected candidate count:

```text
217
```

Expected held-back count:

```text
16
```

Actual real rows created:

```text
0
```

## Decision

Decision:

```text
pos01_private_i1_writer_dry_run_passed
```

## Current final status

POS-01 actual review passed with exclusions.

POS-01 I1 mapping dry-run aggregate check passed.

POS-01 private I1 row writer dry-run passed.

Real private I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
