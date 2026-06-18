# H3 baseline training dry-run result

Status: dry-run passed.

Command:

```text
python scripts/h3_train_baseline.py
```

Aggregate result:

```text
status: dry_run_ready
mode: dry_run
training_type: metadata_smoke_test_baseline
scientific_training_ready: false
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

Current checklist:

```text
[x] H3 explicit approval
[x] private I2 readiness validator passed
[x] H3 feature matrix readiness check
[x] H3 feature matrix build plan
[x] H3 feature matrix builder script
[x] H3 feature matrix build dry-run
[x] H3 feature matrix written outside Git
[x] H3 baseline training design
[x] H3 local training script
[x] H3 training dry-run
[ ] H3 private training run       <- NEXT
[ ] H3 evaluation report
[ ] H3 model artifact write outside Git
[ ] H4 decision gate
```

Next: H3 private training run.
