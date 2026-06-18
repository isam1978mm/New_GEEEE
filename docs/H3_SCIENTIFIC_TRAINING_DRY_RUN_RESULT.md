# H3 scientific training dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/h3_train_scientific.py`.

No private rows are included.

No private identifiers are included.

No feature matrix contents are included.

No model was trained.

No model artifact was written.

No inference was started.

## Command

```text
python scripts/h3_train_scientific.py
```

## Aggregate result

```text
status: dry_run_ready
mode: dry_run
training_type: h3_scientific_real_feature_baseline
feature_set_type: real_i2_source_context_v1
scientific_training_ready: true
target_policy: binary_class_a_vs_other
rows_loaded: 868
expected_rows: 868
feature_column_count: 8
numeric_feature_column_count: 8
non_numeric_feature_column_count: 0
non_finite_value_count: 0
duplicate_sample_id_count: 0
missing_required_column_count: 0
unknown_label_count: 0
unknown_split_count: 0
sklearn_available: true
training_started: false
model_artifact_written: false
evaluation_report_written: false
inference_started: false
```

## Rows by label

| Label | Rows |
| --- | ---: |
| Class_A | 217 |
| Class_Background | 217 |
| Class_HardNegative | 434 |

## Rows by source

| Source | Rows |
| --- | ---: |
| POS-01 | 217 |
| C05 | 217 |
| C06 | 217 |
| C07 | 217 |

## Rows by split

| Split | Rows |
| --- | ---: |
| train | 608 |
| val | 88 |
| test | 88 |
| holdout | 84 |

## Positive rows by split

| Split | Positive rows |
| --- | ---: |
| train | 152 |
| val | 22 |
| test | 22 |
| holdout | 21 |

## Decision

```text
h3_scientific_training_dry_run_ready
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
[x] H3 scientific training script
[x] H3 scientific training dry-run
[ ] H3 scientific training run       <- NEXT
[ ] H3 holdout evaluation
[ ] H4 gate reopen decision
```

## Current status

The H3 scientific training dry-run passed.

Training has not started.

No model artifact has been written.

No evaluation report has been written.

Inference has not started.

Next step is running the local H3 scientific training with `--write`.
