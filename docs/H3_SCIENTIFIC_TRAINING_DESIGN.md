# H3 scientific training design

Status: design ready

This document defines the H3 scientific training design after the private real feature matrix was written outside Git.

No private rows are included.

No private identifiers are included.

No feature matrix contents are included.

No model is trained by this document.

No model artifact is written by this document.

No inference is started by this document.

## Current status

```text
Private I2 readiness: complete
H3 smoke-test pipeline: complete
H3 real feature matrix: written outside Git
Feature set type: real_i2_source_context_v1
Scientific training ready: true
H4 inference: not started
```

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
[ ] H3 scientific training script       <- NEXT
[ ] H3 scientific training dry-run
[ ] H3 scientific training run
[ ] H3 holdout evaluation
[ ] H4 gate reopen decision
```

## Training goal

Train a local H3 binary classifier using the private real feature matrix.

Target policy:

```text
binary positive-vs-other
Class_A -> 1
Class_Background -> 0
Class_HardNegative -> 0
```

This keeps the first scientific H3 model directly comparable to the earlier smoke-test baseline while using the real feature matrix.

## Input matrix

Private matrix path:

```text
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\real_feature_matrix.private.csv
```

Expected matrix summary:

```text
feature_set_type: real_i2_source_context_v1
rows: 868
feature_column_count: 8
scientific_training_ready: true
join_missing_feature_rows: 0
```

## Split policy

The script must respect existing splits:

```text
train: fit model
val: tune threshold or select model only if needed
test: internal test report
holdout: protected final evaluation only after model and threshold are fixed
```

Holdout must not be used for fitting, feature selection, threshold tuning, or model selection.

## Recommended model

Recommended first model:

```text
LogisticRegression with StandardScaler
```

Fallback policy:

```text
If scikit-learn is missing, refuse training.
Do not silently switch to a different implementation.
```

Optional comparison baseline:

```text
DummyClassifier most_frequent
```

The dummy baseline may be reported for context, but the primary model should remain explicit.

## Required dry-run behavior

Future script:

```text
scripts/h3_train_scientific.py
```

Default command:

```text
python scripts/h3_train_scientific.py
```

Default behavior:

```text
load private real feature matrix
validate row counts and splits
validate numeric finite features
validate target mapping
print aggregate-only JSON summary
write no files
train no model
run no inference
```

## Write behavior

Write command, only after dry-run passes:

```text
python scripts/h3_train_scientific.py --write
```

Expected behavior:

```text
train local H3 scientific model
write local model artifact outside Git
write local evaluation report outside Git
write local training summary outside Git
run no H4 inference
```

Recommended local output files:

```text
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_model.private.pkl
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_evaluation_report.private.json
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_training_summary.private.json
```

## Required metrics

Report aggregate metrics for each split:

```text
rows
positive_rows
negative_rows
accuracy
precision
recall
f1
roc_auc if available
true_negative
false_positive
false_negative
true_positive
```

Also report:

```text
feature_column_count
rows_by_label
rows_by_split
positive_rows_by_split
non_finite_value_count
duplicate_sample_id_count
training_started
model_artifact_written
evaluation_report_written
inference_started
```

## H4 boundary

Even after H3 scientific training, H4 remains blocked until the H4 gate explicitly reopens.

The training script must not:

```text
run inference
create prediction files
serve model outputs
change API/frontend code
create overlays
```

## Stop conditions

Stop before any step that would:

```text
commit private feature matrices
commit private model artifacts
commit private evaluation outputs
run H4 inference
create prediction outputs
connect model to app/API/frontend
create map overlays
```

## Decision

```text
h3_scientific_training_design_ready
```

## Next step

```text
Create H3 scientific training script
```
