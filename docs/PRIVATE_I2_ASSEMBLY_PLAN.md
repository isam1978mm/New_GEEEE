# Private I2 assembly plan

Status: plan ready for private I2 assembler design

This document defines the plan for assembling the private I2 dataset pack from existing private I1 rows and private split assignments.

No private rows are included.

No private identifiers are included.

No source payload contents are included.

No I2 pack is assembled by this document.

No validator is run by this document.

No model or inference step is started.

## Current private inputs already created outside Git

| Input family | Private row count | Status |
| --- | ---: | --- |
| POS-01 positive I1 rows | 217 | created outside Git |
| C05 background I1 rows | 217 | created outside Git |
| C06 hard-negative I1 rows | 217 | created outside Git |
| C07 hard-negative I1 rows | 217 | created outside Git |
| private split assignments | 868 | created outside Git |

Total private I1 rows available:

```text
868
```

## Current item checklist

Current item:

```text
I2 assembly path
```

Checklist:

```text
[x] private I1 rows ready
[x] private split assignments ready
[x] I2 assembly plan
[ ] private I2 assembler script       ← NEXT
[ ] private I2 assembler dry-run
[ ] private I2 pack assembled outside Git
[ ] dataset readiness validator design/check
[ ] dataset readiness validator dry-run or run on private I2 pack
```

## Planned private input folders

The assembler should read only from private local folders outside Git:

```text
C:\Dev\New_GEE_PRIVATE\I1_POS01
C:\Dev\New_GEE_PRIVATE\I1_C05
C:\Dev\New_GEE_PRIVATE\I1_C06
C:\Dev\New_GEE_PRIVATE\I1_C07
C:\Dev\New_GEE_PRIVATE\SPLITS
```

Expected private input files:

```text
training_examples.pos01.private.jsonl
training_examples.c05.private.jsonl
training_examples.c06.private.jsonl
training_examples.c07.private.jsonl
split_assignments.private.jsonl
split_assignments.private.summary.json
split_leakage_report.private.json
```

## Planned private output folder

The assembler should write only outside Git under:

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE
```

Recommended output files:

```text
i2_training_examples.private.jsonl
i2_manifest.private.json
i2_summary.private.json
i2_source_inventory.private.json
i2_split_summary.private.json
i2_leakage_report.private.json
```

## Assembly behavior

The future assembler should:

```text
1. Load all four private I1 JSONL files.
2. Load private split assignments.
3. Validate that every I1 sample has exactly one split assignment.
4. Validate that every split assignment maps to exactly one I1 sample.
5. Replace or set each I1 row split using the private split assignment.
6. Preserve labels and evidence fields.
7. Preserve source family information where available.
8. Write combined I2 files outside Git only when --write is explicitly used.
9. Print aggregate-only JSON summary.
```

## Default dry-run behavior

Default command:

```text
python scripts/assemble_private_i2_pack.py
```

Expected behavior:

```text
dry-run only
write zero private I2 files
print aggregate JSON summary
```

Dry-run must report:

```text
status
total_i1_rows_loaded
total_split_assignments_loaded
matched_assignment_count
missing_assignment_count
extra_assignment_count
rows_by_source
rows_by_label
rows_by_split
rows_by_source_and_split
rows_by_label_and_split
leakage_check_passed
i2_rows_written
validator_run_on_real_data
training_started
inference_started
```

Dry-run must always report:

```text
i2_rows_written: 0
validator_run_on_real_data: false
training_started: false
inference_started: false
```

## Write behavior

Write command, only after explicit approval:

```text
python scripts/assemble_private_i2_pack.py --write
```

Expected behavior:

```text
write private I2 pack files under C:\Dev\New_GEE_PRIVATE\I2_PRIVATE
print aggregate JSON summary
```

## Planned aggregate output counts

Expected total:

```text
868 rows
```

Expected rows by source:

| Source | Rows |
| --- | ---: |
| POS-01 | 217 |
| C05 | 217 |
| C06 | 217 |
| C07 | 217 |

Expected rows by label:

| Label | Rows |
| --- | ---: |
| Class_A | 217 |
| Class_Background | 217 |
| Class_HardNegative | 434 |

Expected rows by split:

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |

## Required validation checks before writing

The assembler must refuse write mode if:

```text
any private I1 input file is missing
split assignment file is missing
row count is not 868
split assignment count is not 868
any I1 row lacks a matching split assignment
any split assignment lacks a matching I1 row
any sample_id is duplicated
any group_id crosses splits
any required I2 field is missing
any output path would be inside Git
```

## Required fields retained in I2 rows

The assembled I2 rows should retain at least:

```text
schema_version
sample_id
dataset_id
area_id
group_id
chip_id
split
label
label_quality
label_evidence_source
evidence_source_type
evidence_source_version
evidence_review_method
reviewer_or_source_reference
acquisition_window
sensor_sources
grid_version
preprocessing_commit
features_ref
metadata_ref
redaction_class
notes
```

## Repo-visible reporting rule

Repository-visible docs may report only aggregate counts and pass/fail checks.

They must not contain:

```text
private sample_id values
private group_id values
private chip_id values
private feature references
private metadata references
source record references
coordinates
geometry
private row contents
```

## Boundary

I2 assembly is a dataset packaging step only.

It does not run the readiness validator.

It does not start model training.

It does not start inference.

H3 and H4 remain blocked until a later explicit approval after validator success.

## Stop conditions

Stop before any step that would:

```text
commit private I2 files
commit private row files
commit source datasets
run validator before I2 exists
start model work
start inference work
change app/API/frontend code
```

## Decision

```text
private_i2_assembly_plan_ready
```

## Next step

```text
Create private I2 assembler script
```
