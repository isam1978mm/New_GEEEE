# H3 feature matrix build plan

Status: plan ready for feature matrix builder design

This document defines the plan for creating a private H3 training feature matrix after the I2 readiness validator passed.

No private I2 row contents are included.

No private identifiers are included.

No source payload contents are included.

No feature matrix is written by this document.

No model is trained by this document.

No model artifact is written by this document.

No inference is started by this document.

## Current H3 status

The private I2 pack passed readiness validation.

H3 training was explicitly approved to proceed.

The first H3 feature matrix readiness check found:

```text
status: feature_matrix_not_ready
readiness_decision: not_ready_pending_feature_references
i2_rows_loaded: 868
pending_feature_ref_count: 868
pending_metadata_ref_count: 868
feature_matrix_status: missing
join_missing_feature_rows: 868
training_started: false
inference_started: false
model_artifact_written: false
```

## Current item checklist

Current item:

```text
H3 training path
```

Checklist:

```text
[x] H3 explicit approval
[x] private I2 readiness validator passed
[x] H3 feature matrix readiness check
[x] H3 feature matrix build plan
[ ] H3 feature matrix builder script       ← NEXT
[ ] H3 feature matrix build dry-run
[ ] H3 feature matrix written outside Git
[ ] H3 baseline training design
[ ] H3 local training script
[ ] H3 training dry-run
[ ] H3 private training run
[ ] H3 evaluation report
[ ] H3 model artifact write outside Git
[ ] H4 decision gate
```

## Goal

Create a private, numeric training matrix that can join one-to-one with the 868 private I2 rows.

The matrix must stay outside Git.

The initial matrix may be a baseline tabular matrix, but it must be explicit and reproducible.

## Private input

Private I2 pack:

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE\i2_training_examples.private.jsonl
```

Optional future private feature source folders:

```text
C:\Dev\New_GEE_PRIVATE\FEATURES
C:\Dev\New_GEE_PRIVATE\H3_TRAINING
```

## Private output folder

Feature matrix outputs must stay outside Git under:

```text
C:\Dev\New_GEE_PRIVATE\H3_TRAINING
```

Recommended files:

```text
training_matrix.private.csv
training_matrix.private.summary.json
feature_matrix_lineage.private.json
```

## Required feature matrix columns

The feature matrix must include:

```text
sample_id
split
label
source_id
```

It must also include at least one numeric feature column.

Recommended first baseline numeric features are safe row-level metadata-derived features that do not expose private identifiers:

```text
source_pos01_indicator
source_c05_indicator
source_c06_indicator
source_c07_indicator
label_family_positive_indicator
label_family_background_indicator
label_family_hard_negative_indicator
split_train_indicator
split_val_indicator
split_test_indicator
split_holdout_indicator
```

These are not enough for a meaningful final model, but they can test the local H3 training pipeline safely.

A later stronger feature matrix should replace or extend these with real remote-sensing or semantic feature summaries.

## Builder behavior

The future builder should:

```text
1. Read the private I2 JSONL file outside Git.
2. Validate 868 rows are present.
3. Validate sample_id, split, label, and source_id are present.
4. Create deterministic numeric baseline features.
5. Write the private matrix only when --write is explicitly provided.
6. Print aggregate-only JSON summary.
7. Never write matrix contents to Git.
```

## Default dry-run behavior

Default command:

```text
python scripts/h3_build_feature_matrix.py
```

Expected behavior:

```text
dry-run only
write zero files
print aggregate JSON summary
```

Dry-run summary should include:

```text
status
i2_rows_loaded
expected_i2_rows
planned_matrix_rows
planned_feature_column_count
rows_by_label
rows_by_split
rows_by_source
missing_required_field_counts
feature_matrix_written
training_started
inference_started
model_artifact_written
```

## Write behavior

Write command, only after dry-run passes and explicit approval:

```text
python scripts/h3_build_feature_matrix.py --write
```

Expected behavior:

```text
write C:\Dev\New_GEE_PRIVATE\H3_TRAINING\training_matrix.private.csv
write C:\Dev\New_GEE_PRIVATE\H3_TRAINING\training_matrix.private.summary.json
write C:\Dev\New_GEE_PRIVATE\H3_TRAINING\feature_matrix_lineage.private.json
```

## Baseline limitation

A metadata-derived baseline feature matrix is only a pipeline smoke-test matrix.

It can validate that H3 local training code works end-to-end.

It should not be treated as a strong scientific model.

Any final model claim requires real predictive features and evaluation against the untouched holdout.

## Stop conditions

Stop before any step that would:

```text
commit private I2 files
commit private feature matrices
commit model artifacts
run inference
connect model output to API/frontend
create public overlays
change app/API/frontend code
```

## Decision

```text
h3_feature_matrix_build_plan_ready
```

## Next step

```text
Create H3 feature matrix builder script
```
