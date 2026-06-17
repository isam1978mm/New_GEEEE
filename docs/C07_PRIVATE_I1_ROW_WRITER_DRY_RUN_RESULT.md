# C07 private I1 row writer dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/c07_write_private_i1_rows.py`.

No private I1 JSONL rows were created.

No private sample rows are included.

No private identifiers are included.

No I2 pack was assembled.

No validator was run on real data.

No H3 or H4 step was started.

## Command

```text
python scripts/c07_write_private_i1_rows.py
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_ready |
| Source id | C07 |
| Requested count | 217 |
| Candidate count | 217 |
| Eligible count | 217 |
| Selected count | 217 |
| Held back count | 0 |
| Sample manifest present | true |
| Sample manifest status | sample_manifest_valid |
| Seed | 20260616 |
| Real I1 rows created | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| H3 started | false |
| H4 started | false |

## Planned aggregate mapping

| Planned mapping | Count |
| --- | ---: |
| Class_HardNegative | 217 |
| reviewed_independent | 217 |
| independently_produced_reference | 217 |
| LOCAL_SENSITIVE | 217 |
| unassigned split | 217 |

## Decision

```text
c07_private_i1_writer_dry_run_ready
```

## Next possible phase

The next possible phase is to write C07 private I1 rows outside Git using `--write`.

That phase will create private local C07 hard-negative I1 rows only.

It will not assemble I2.

It will not run the validator.
