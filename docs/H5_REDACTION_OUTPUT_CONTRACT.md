# H5 redaction/output contract

Status: ready.

No API code was changed.

No frontend code was changed.

No overlays were created.

No serving was started.

## Current status

```text
H4 offline result: complete
Private outputs: outside Git
API/frontend: unchanged
Overlays: not created
H5 serving: blocked pending approval
```

## Allowed output level

Only aggregate, redacted output is allowed at this stage.

Allowed fields:

```text
total_row_count
score_min
score_max
score_mean
score_band_counts
rows_by_source
rows_by_split
model_status
pipeline_status
```

## Blocked output level

Still blocked:

```text
sample_id
row-level scores
private file paths
private source references
feature values
model files
raw CSV downloads
map overlays
```

## Redaction rule

Any future H5 surface must expose only safe aggregate values unless a later approval gate explicitly allows more.

## Serving rule

No endpoint or UI may serve private prediction files directly.

## Current H5 checklist

```text
[x] H5 serving/API/frontend decision gate
[x] H5 serving risk review plan
[x] H5 redaction/output contract
[ ] H5 operator-only serving design       <- NEXT
[ ] H5 API/frontend implementation plan
[ ] H5 implementation approval gate
```

## Decision

```text
h5_redaction_output_contract_ready
```
