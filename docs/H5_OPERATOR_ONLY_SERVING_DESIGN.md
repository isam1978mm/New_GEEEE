# H5 operator-only serving design

Status: design ready.

No API code was changed.

No frontend code was changed.

No overlays were created.

No serving was started.

## Current status

```text
H4 offline result: complete
Private outputs: outside Git
H5 redaction/output contract: ready
Serving: blocked pending implementation approval
```

## Design scope

The first H5 surface must be operator-only and aggregate-only.

Allowed output:

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

Blocked output:

```text
row-level scores
private identifiers
raw prediction files
private paths
feature values
model artifacts
map overlays
```

## Access boundary

Any future endpoint or UI must require operator authorization.

The first design should not include public access.

## Serving boundary

No direct file streaming of private prediction files is allowed.

Any future response must be generated from approved aggregate summaries only.

## Current H5 checklist

```text
[x] H5 serving/API/frontend decision gate
[x] H5 serving risk review plan
[x] H5 redaction/output contract
[x] H5 operator-only serving design
[ ] H5 API/frontend implementation plan       <- NEXT
[ ] H5 implementation approval gate
```

## Decision

```text
h5_operator_only_serving_design_ready
```
