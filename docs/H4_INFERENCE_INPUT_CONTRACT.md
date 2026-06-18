# H4 inference input contract

Status: ready.

No scoring was run.

No output rows were created.

No API, frontend, or overlay work was started.

## Required private inputs

```text
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\real_feature_matrix.private.csv
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\real_feature_matrix.private.summary.json
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_model.private.pkl
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES\h3_scientific_training_summary.private.json
```

## Required aggregate checks

```text
feature_set_type: real_i2_source_context_v1
row_count: 868
feature_column_count: 8
scientific_training_ready: true
duplicate_sample_id_count: 0
non_finite_value_count: 0
```

## Required row counts

```text
POS-01: 217
C05: 217
C06: 217
C07: 217
Class_A: 217
Class_Background: 217
Class_HardNegative: 434
train: 608
val: 88
test: 88
holdout: 84
```

## Future script contract

```text
scripts/h4_run_private_offline_inference.py
```

Default mode must be dry-run only.

Write mode must require explicit `--write`.

All private outputs must stay under:

```text
C:\Dev\New_GEE_PRIVATE\H4_INFERENCE
```

## Still blocked

```text
API/frontend integration
overlays
public serving
committing private outputs
```

## Current H4 checklist

```text
[x] H4 gate conditionally reopened for design only
[x] H4 private offline inference design
[x] H4 inference input contract
[ ] H4 local inference script       <- NEXT
[ ] H4 inference dry-run
[ ] H4 private prediction write approval gate
[ ] H4 private prediction write outside Git
[ ] H4 aggregate prediction review
[ ] H5 serving/API/frontend decision gate
```

## Decision

```text
h4_inference_input_contract_ready
```
