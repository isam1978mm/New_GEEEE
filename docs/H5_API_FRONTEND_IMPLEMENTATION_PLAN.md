# H5 API/frontend implementation plan

Status: plan ready.

No API code was changed.

No frontend code was changed.

No overlays were created.

No serving was started.

## Current status

```text
H4 offline result: complete
Private outputs: outside Git
H5 redaction/output contract: ready
H5 operator-only serving design: ready
Serving implementation: not approved yet
```

## Implementation scope

Future implementation may expose only redacted aggregate summaries to authorized operators.

Allowed response shape:

```text
total_row_count
score_min
score_max
score_mean
score_band_counts
rows_by_source
rows_by_split
pipeline_status
```

Still blocked:

```text
row-level scores
sample identifiers
private file paths
raw CSV downloads
feature values
model artifacts
map overlays
```

## Proposed backend plan

```text
add operator-only aggregate summary service
read only approved private summary JSON
return redacted aggregate JSON
reject direct private file serving
add unit tests for no row-level leakage
```

## Proposed frontend plan

```text
operator-only summary panel
show aggregate counts and score bands only
hide row-level data
no map overlay layer
no download button
```

## Required tests before approval

```text
operator auth required
no direct file streaming
no private paths in responses
no sample_id in responses
no row-level score output
redaction verifier passes
```

## Current H5 checklist

```text
[x] H5 serving/API/frontend decision gate
[x] H5 serving risk review plan
[x] H5 redaction/output contract
[x] H5 operator-only serving design
[x] H5 API/frontend implementation plan
[ ] H5 implementation approval gate       <- NEXT
```

## Decision

```text
h5_api_frontend_implementation_plan_ready
```
