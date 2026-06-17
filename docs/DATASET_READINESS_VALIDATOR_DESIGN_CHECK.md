# Dataset readiness validator design/check

Status: validator design/check ready

This document defines the dataset readiness validator checks for the private I2 pack.

No private I2 row contents are included.

No private identifiers are included.

No source payload contents are included.

No validator is run by this document.

No model or inference step is started.

## Current private I2 status

Private I2 pack exists outside Git:

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE
```

Expected private I2 files:

```text
i2_training_examples.private.jsonl
i2_manifest.private.json
i2_summary.private.json
i2_source_inventory.private.json
i2_split_summary.private.json
i2_leakage_report.private.json
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
[x] private I2 assembler script
[x] private I2 assembler dry-run
[x] private I2 pack assembled outside Git
[x] dataset readiness validator design/check
[ ] dataset readiness validator dry-run or run on private I2 pack       ← NEXT
```

## Validator purpose

The readiness validator must decide whether the private I2 pack is structurally ready for a later training decision.

A validator pass does not start training.

A validator pass does not start inference.

A validator pass only changes readiness state to:

```text
ready_for_private_training_later
```

## Required validator input

The validator should read only private local files outside Git:

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_training_examples.private.jsonl
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_summary.private.json
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_manifest.private.json
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_split_summary.private.json
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_leakage_report.private.json
```

## Required expected counts

Expected total rows:

```text
868
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

## Required row-field checks

Every I2 row must include:

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

## Required split checks

The validator must confirm:

```text
all split values are one of train, val, test, holdout
train row count is 608
val row count is 88
test row count is 88
holdout row count is 84
no group_id appears in more than one split
no sample_id appears more than once
no chip_id appears more than once
```

## Required label checks

The validator must confirm:

```text
Class_A count is 217
Class_Background count is 217
Class_HardNegative count is 434
no unknown label is present
labels are not changed by validation
```

## Required source checks

The validator must confirm:

```text
POS-01 count is 217
C05 count is 217
C06 count is 217
C07 count is 217
all four source families are present
```

## Required evidence and redaction checks

The validator must confirm:

```text
evidence_source_type is populated for every row
evidence_source_version is populated for every row
label_quality is populated for every row
redaction_class is populated for every row
no row is marked for repository publication
```

## Required output behavior

Default validator command should be dry-run/check-only:

```text
python scripts/validate_private_i2_readiness.py
```

It should write no private files unless a later explicit write/report flag is introduced.

It may print aggregate JSON only.

The aggregate JSON should include:

```text
status
total_rows
rows_by_source
rows_by_label
rows_by_split
required_field_missing_counts
duplicate_sample_id_count
duplicate_chip_id_count
group_leakage_detected
unknown_label_count
unknown_split_count
readiness_decision
training_started
inference_started
```

## Readiness decisions

Allowed readiness decisions:

```text
ready_for_private_training_later
not_ready_missing_required_fields
not_ready_bad_counts
not_ready_split_leakage
not_ready_duplicate_ids
not_ready_unknown_labels_or_splits
not_ready_input_files_missing
```

## Passing decision

The only passing decision is:

```text
ready_for_private_training_later
```

If the validator returns this, the I2 readiness phase is complete.

H3 still requires separate explicit approval.

H4 remains blocked until after a later approved model and inference gate.

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

## Stop conditions

Stop before any step that would:

```text
commit private I2 files
commit private row files
commit source datasets
start model work
start inference work
change app/API/frontend code
```

## Decision

```text
dataset_readiness_validator_design_check_ready
```

## Next step

```text
Create and run dataset readiness validator on the private I2 pack
```
