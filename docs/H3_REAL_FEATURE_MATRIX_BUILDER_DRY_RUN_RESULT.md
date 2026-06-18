# H3 real feature matrix builder dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/h3_build_real_feature_matrix.py`.

No private rows are included.

No private identifiers are included.

No feature matrix was written.

No model was trained.

No model artifact was written.

No inference was started.

## Command

```text
python scripts/h3_build_real_feature_matrix.py
```

## Aggregate result

```text
status: dry_run_ready
readiness_decision: ready_to_write_real_feature_matrix
feature_set_type: real_i2_source_context_v1
scientific_training_ready: true
expected_rows: 868
i2_rows_loaded: 868
planned_matrix_rows: 868
feature_column_count: 8
join_matched_feature_rows: 868
join_missing_feature_rows: 0
duplicate_sample_id_count: 0
non_finite_value_count: 0
feature_matrix_written: false
training_started: false
inference_started: false
model_artifact_written: false
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

## Decision

```text
h3_real_feature_matrix_builder_dry_run_ready
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
[ ] H3 real feature matrix written outside Git       <- NEXT
[ ] H3 scientific training design
[ ] H3 scientific training dry-run
[ ] H3 scientific training run
[ ] H3 holdout evaluation
[ ] H4 gate reopen decision
```

## Current status

The real feature matrix builder dry-run passed.

The matrix has not been written yet.

Training has not started.

Inference has not started.

Next step is writing the private real feature matrix outside Git using `--write`.
