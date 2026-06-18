# H4 private offline inference design

Status: design ready

This document defines the first H4 private offline inference design after the H4 gate was conditionally reopened for design only.

No inference is run by this document.

No prediction files are created by this document.

No API, frontend, or overlay work is started by this document.

No private rows, feature values, model artifacts, or prediction outputs are included.

## Current status

```text
H3 scientific path: complete
H3 holdout evaluation: recorded
H4 gate: conditionally reopened for private offline design only
H4 inference: not started
Prediction files: not created
API/frontend: unchanged
```

## Current H4 checklist

```text
H4 private offline inference path

[x] H4 gate conditionally reopened for design only
[x] H4 private offline inference design
[ ] H4 inference input contract       <- NEXT
[ ] H4 local inference script
[ ] H4 inference dry-run
[ ] H4 private prediction write approval gate
[ ] H4 private prediction write outside Git
[ ] H4 aggregate prediction review
[ ] H5 serving/API/frontend decision gate
```

## Purpose

H4 private offline inference should prove that the local model can score a private feature matrix safely without exposing private data or creating public outputs.

The first H4 implementation must remain local-only and private-only.

## Inputs

Required private inputs outside Git:

```text
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\real_feature_matrix.private.csv
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_model.private.pkl
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_training_summary.private.json
```

Expected input summary:

```text
rows: 868
feature_column_count: 8
feature_set_type: real_i2_source_context_v1
model_type: h3_scientific_real_feature_baseline
```

## Output folder

Recommended private output folder:

```text
C:\Dev\New_GEE_PRIVATE\H4_INFERENCE
```

Potential future files, only after explicit write approval:

```text
h4_predictions.private.csv
h4_prediction_summary.private.json
h4_prediction_lineage.private.json
```

## Dry-run requirements

The first H4 script must default to dry-run only.

Default command:

```text
python scripts/h4_run_private_offline_inference.py
```

Dry-run must:

```text
load model metadata or model file safely
load feature matrix header and aggregate counts
validate row count
validate feature columns match the trained model input contract
validate finite numeric features
report planned prediction row count
write no files
run no prediction scoring unless explicitly allowed by design
start no API/frontend/overlay work
```

## Write requirements

Write command, only after dry-run and approval gate:

```text
python scripts/h4_run_private_offline_inference.py --write
```

Write mode may:

```text
score the private feature matrix locally
write private prediction CSV outside Git
write aggregate prediction summary outside Git
write private lineage JSON outside Git
```

Write mode must not:

```text
commit predictions
serve predictions
create overlays
change API/frontend
publish model outputs
```

## Required aggregate reporting

Dry-run and write summaries should include:

```text
status
feature_matrix_rows
feature_column_count
model_artifact_present
training_summary_present
planned_prediction_rows
prediction_rows_written
rows_by_split
rows_by_label
rows_by_source
score_min
score_max
score_mean
inference_started
prediction_files_written
api_frontend_changed
```

## Safety gates

H4 must stop if:

```text
model artifact is missing
feature matrix is missing
feature columns do not match expected training inputs
any non-finite feature values are present
row count is not 868
private output path is inside Git
```

## H5 boundary

H4 offline inference does not approve serving.

H5 serving/API/frontend remains blocked until a separate decision gate.

## Decision

```text
h4_private_offline_inference_design_ready
```

## Next step

```text
H4 inference input contract
```
