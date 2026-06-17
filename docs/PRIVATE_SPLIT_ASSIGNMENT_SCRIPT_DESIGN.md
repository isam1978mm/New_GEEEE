# Private split assignment script design

Status: design ready

This document defines the design for a later private split assignment script.

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

Total private I1 rows available:

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
[x] train/val/test/holdout policy
[x] private split assignment script design
[ ] private split assignment dry-run       ← NEXT
[ ] private split assignment write outside Git
[ ] I2 assembly plan
```

## Proposed script

```text
scripts/assign_private_splits.py
```

## Private input folders

The script should read private I1 rows from these local folders outside Git:

```text
C:\Dev\New_GEE_PRIVATE\I1_POS01
C:\Dev\New_GEE_PRIVATE\I1_C05
C:\Dev\New_GEE_PRIVATE\I1_C06
C:\Dev\New_GEE_PRIVATE\I1_C07
```

Expected input files:

```text
training_examples.pos01.private.jsonl
training_examples.c05.private.jsonl
training_examples.c06.private.jsonl
training_examples.c07.private.jsonl
```

## Private output folder

The script should write split assignment outputs only under:

```text
C:\Dev\New_GEE_PRIVATE\SPLITS
```

Planned private output files:

```text
split_assignments.private.jsonl
split_assignments.private.summary.json
split_leakage_report.private.json
```

## Default dry-run behavior

Default command:

```text
python scripts/assign_private_splits.py
```

Expected behavior:

```text
dry-run only
write zero private files
print aggregate JSON summary
```

Dry-run must report:

```text
status
seed
total_rows
rows_by_source
rows_by_label
planned_rows_by_split
planned_rows_by_source_and_split
missing_required_field_counts
duplicate_sample_id_count
duplicate_chip_id_count
group_leakage_detected
real_split_assignments_written
i2_pack_assembled
validator_run_on_real_data
```

Dry-run must always report:

```text
real_split_assignments_written: 0
i2_pack_assembled: false
validator_run_on_real_data: false
```

## Write behavior

Write command, only after explicit approval:

```text
python scripts/assign_private_splits.py --write
```

Expected behavior:

```text
write private split assignment files outside Git
print aggregate JSON summary
```

## Split policy

Allowed split names:

```text
train
val
test
holdout
```

Split unit:

```text
group_id
```

Seed:

```text
20260616
```

Planned aggregate split counts:

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |
| total | 868 |

Planned per-source split counts:

| Source | train | val | test | holdout | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| POS-01 | 152 | 22 | 22 | 21 | 217 |
| C05 | 152 | 22 | 22 | 21 | 217 |
| C06 | 152 | 22 | 22 | 21 | 217 |
| C07 | 152 | 22 | 22 | 21 | 217 |

## No-leakage checks

The script must fail write mode if:

```text
any group_id appears in more than one split
any sample_id appears in more than one split
required I1 fields are missing
expected source files are missing
expected row counts do not match
split totals cannot be produced safely
a private output path would be inside Git
```

## Required row fields

The script must require these I1 fields before assigning splits:

```text
sample_id
dataset_id
group_id
chip_id
split
label
label_quality
evidence_source_type
evidence_source_version
features_ref
metadata_ref
redaction_class
```

## Assignment method

The assignment method should:

```text
1. Load each source file separately.
2. Validate required fields.
3. Group rows by group_id within each source.
4. Deterministically order groups using seed plus group_id.
5. Assign groups to train, val, test, and holdout targets per source.
6. Confirm no group crosses splits.
7. Report aggregate counts only.
8. Write outputs only when --write is used.
```

## Repo-visible reporting rule

Repository-visible reports may contain only aggregate counts and pass/fail checks.

They must not contain:

```text
sample_id
group_id
chip_id
features_ref
metadata_ref
source_record_ref
coordinates
geometry
private row contents
```

## Stop conditions

Stop before any step that would:

```text
write private split assignments without explicit approval
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
private_split_assignment_script_design_ready
```

## Next step

```text
Create private split assignment script and run dry-run
```
