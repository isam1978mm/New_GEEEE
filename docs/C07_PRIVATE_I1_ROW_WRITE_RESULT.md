# C07 private I1 row write result

Status: private local write completed

This document records only aggregate output from the C07 private I1 row writer.

No private sample rows are included.

No private I1 JSONL contents are included.

No private identifiers are included.

No I2 pack was assembled.

No validator was run on real data.

No model step was started.

## Command

```text
python scripts/c07_write_private_i1_rows.py --write
```

## Private output folder family

```text
C:\Dev\New_GEE_PRIVATE\I1_C07
```

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| exclusions.c07.private.summary.json | .json | 129 |
| source_lineage.c07.private.json | .json | 219 |
| training_examples.c07.private.jsonl | .jsonl | 247814 |
| training_examples.c07.private.summary.json | .json | 1106 |

## Summary result

| Metric | Value |
| --- | ---: |
| Status | private_i1_rows_written |
| Requested count | 217 |
| Candidate count | 217 |
| Eligible count | 217 |
| Selected count | 217 |
| Held back count | 0 |
| Real I1 rows created | 217 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Model step started | false |
| Inference started | false |

## Decision

```text
c07_private_i1_rows_created_outside_git
```

## Current row inventory

| Source | Role | Private I1 rows | Status |
| --- | --- | ---: | --- |
| POS-01 | positive | 217 | created outside Git |
| C05 | background | 217 | created outside Git |
| C06 | hard-negative | 217 | created outside Git |
| C07 | hard-negative | 217 | created outside Git |

## Current final status

The stronger I2 source row set now exists outside Git.

I2 assembly is not started.

The readiness validator has not been run on real data.

Next phase is private split policy planning.
