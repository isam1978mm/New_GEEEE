# H3 baseline training design

Status: design ready

This document defines the first H3 local baseline training design after the smoke-test feature matrix was written outside Git.

No feature matrix rows are included.

No model is trained by this document.

No model artifact is written by this document.

No inference is started by this document.

## Current item checklist

```text
H3 training path

[x] H3 explicit approval
[x] private I2 readiness validator passed
[x] H3 feature matrix readiness check
[x] H3 feature matrix build plan
[x] H3 feature matrix builder script
[x] H3 feature matrix build dry-run
[x] H3 feature matrix written outside Git
[x] H3 baseline training design
[ ] H3 local training script       <- NEXT
[ ] H3 training dry-run
[ ] H3 private training run
[ ] H3 evaluation report
[ ] H3 model artifact write outside Git
[ ] H4 decision gate
```

## Baseline purpose

The first H3 baseline is a local pipeline smoke test.

It checks that the project can:

```text
load the local feature matrix
respect train, val, test, and holdout splits
map labels to training targets
fit a small baseline model locally
evaluate aggregate metrics
write local-only reports and model files only after explicit write mode
```

## Feature matrix status

Current feature matrix summary:

```text
feature_set_type: metadata_smoke_test_only
rows: 868
feature_columns: 8
pipeline_smoke_test_ready: true
scientific_training_ready: false
```

This means the first model is only a plumbing check.

It must not be treated as a final scientific model.

## Recommended first baseline

Use a small scikit-learn baseline if available locally.

Recommended model family:

```text
LogisticRegression or DummyClassifier fallback
```

If scikit-learn is unavailable, the script should refuse real training and report the missing dependency rather than silently changing behavior.

## Target policy

Initial baseline target:

```text
binary positive-vs-other
```

Mapping:

```text
Class_A -> 1
Class_Background -> 0
Class_HardNegative -> 0
```

This keeps the first H3 baseline simple.

## Split policy

Training script must use:

```text
train: fit model
val: report validation metrics
test: report internal test metrics
holdout: final protected check only after fit and threshold are fixed
```

The training script must not use holdout rows for fitting, tuning, feature selection, or threshold selection.

## Required metrics

Aggregate metrics should include:

```text
row counts by split
row counts by label
positive rate by split
accuracy
precision
recall
f1
roc_auc if available
confusion matrix counts
```

## Local output folder

All H3 outputs must stay outside Git under:

```text
C:\Dev\New_GEE_PRIVATE\H3_TRAINING
```

Recommended future outputs:

```text
h3_training_summary.private.json
h3_evaluation_report.private.json
h3_baseline_model.private.pkl
```

## Training script behavior

Future script:

```text
scripts/h3_train_baseline.py
```

Default command:

```text
python scripts/h3_train_baseline.py
```

Default behavior:

```text
dry-run only
load and validate matrix
report planned training summary
write no model
write no report
run no inference
```

Write command after dry-run passes:

```text
python scripts/h3_train_baseline.py --write
```

Write behavior:

```text
train local baseline
write local report
write local model artifact
run no H4 inference
```

## Stop conditions

Stop before any step that would:

```text
commit feature matrices
commit model artifacts
run H4 inference
connect model output to API or frontend
create overlays
change app/API/frontend code
```

## Decision

```text
h3_baseline_training_design_ready
```

## Next step

```text
Create H3 local training script
```
