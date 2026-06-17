# C06 private I1 row write result

Status: private local write completed

This document records only aggregate output from the C06 private I1 row writer.

No private sample rows are included.

No private I1 JSONL contents are included.

No private identifiers are included.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Command

```text
python scripts/c06_write_private_i1_rows.py --write
```

## Private output folder family

```text
C:\Dev\New_GEE_PRIVATE\I1_C06
```

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| exclusions.c06.private.summary.json | .json | 129 |
| source_lineage.c06.private.json | .json | 212 |
| training_examples.c06.private.jsonl | .jsonl | 240653 |
| training_examples.c06.private.summary.json | .json | 1097 |

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
| Training started | false |
| Inference started | false |

## Decision

Decision:

```text
c06_private_i1_rows_created_outside_git
```

## Boundary

This step created private local C06 hard-negative I1 rows only.

It did not create an I2 dataset pack.

It did not validate the dataset pack.

It did not start H3 training.

It did not start H4 inference.

## Current final status

POS-01 positive private I1 rows exist outside Git.

C05 negative/background private I1 rows exist outside Git.

C06 hard-negative private I1 rows exist outside Git.

C07 hard-negative private I1 rows are not created.

I2 assembly is not started.

Dataset readiness validator has not been run on real data.

H3 remains blocked.

H4 remains blocked.
