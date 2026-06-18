# H3 holdout evaluation result

Status: protected holdout evaluation recorded

This document records aggregate-only holdout evaluation output from the completed H3 scientific training run.

No private rows are included.

No private identifiers are included.

No feature matrix contents are included.

No model artifact is included.

No inference was started.

No prediction files were created.

## Source training run

```text
script: scripts/h3_train_scientific.py --write
training_type: h3_scientific_real_feature_baseline
feature_set_type: real_i2_source_context_v1
scientific_training_ready: true
```

## Aggregate holdout result

```text
holdout_rows: 84
holdout_positive_rows: 21
holdout_negative_rows: 63
holdout_accuracy: 1.0
```

The training summary reported:

```text
train_accuracy: 1.0
val_accuracy: 1.0
test_accuracy: 1.0
holdout_accuracy: 1.0
```

## Boundary interpretation

The holdout result is recorded as a gate input, not as deployment approval.

The H4 gate still must explicitly decide whether inference remains blocked or can reopen under a limited scope.

## Current item checklist

```text
H3 real feature matrix path

[x] I2 private rows ready
[x] smoke-test feature matrix built
[x] smoke-test training pipeline proven
[x] CI repaired / green
[x] H3 real feature matrix plan
[x] H3 real feature source inventory script
[x] H3 real feature source inventory dry-run
[x] H3 real feature source inventory written outside Git
[x] H3 real feature builder script
[x] H3 real feature dry-run
[x] H3 real feature matrix written outside Git
[x] H3 scientific training design
[x] H3 scientific training script
[x] H3 scientific training dry-run
[x] H3 scientific training run
[x] H3 holdout evaluation
[ ] H4 gate reopen decision       <- NEXT
```

## Current status

```text
H3 scientific training: complete
H3 holdout evaluation: recorded
H3 model artifact: written outside Git
H3 evaluation report: written outside Git
H4 inference: not started
Prediction files: not created
```

## H4 gate input summary

```text
private_i2_rows: 868
real_feature_matrix_rows: 868
feature_column_count: 8
join_missing_feature_rows: 0
scientific_training_ready: true
model_artifact_written: true
evaluation_report_written: true
holdout_accuracy: 1.0
inference_started: false
```

## Stop conditions still active

Stop before any step that would:

```text
run inference
create prediction files
serve model output through API/frontend
create map overlays
commit private feature matrices
commit private model artifacts
commit private prediction outputs
```

## Decision

```text
h3_holdout_evaluation_recorded
```

## Next step

```text
H4 gate reopen decision
```
