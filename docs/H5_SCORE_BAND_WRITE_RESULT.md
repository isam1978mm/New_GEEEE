# H5 score-band aggregate write result

Status: completed outside Git.

No private prediction rows are included in this document.

No sample identifiers are included.

No private paths are exposed through API or frontend responses.

No raw CSV serving was started.

No overlays were created.

## Source run

```text
script: scripts/h5_review_score_bands.py --write
status: h5_score_band_review_written
```

## Private local files

Written outside Git under:

```text
C:\Dev\New_GEE_PRIVATE\H5_AGGREGATE_REVIEW
```

Files:

```text
h5_score_band_summary.private.json
h5_score_band_lineage.private.json
```

## Aggregate result

```text
score_rows_loaded: 868
expected_score_rows: 868
h4_score_rows_written: 868
score_min: 0.00004185
score_max: 0.97847171
score_mean: 0.2499092531797235
score_band_counts_status: available_from_private_aggregate_review
review_written: true
row_level_output_included: false
private_paths_included: false
raw_prediction_file_served: false
api_frontend_changed: false
overlays_created: false
```

## Score bands

```text
score_0_00_to_0_10: 651
score_0_10_to_0_25: 0
score_0_25_to_0_50: 0
score_0_50_to_0_75: 0
score_0_75_to_1_00: 217
```

## Rows by source

```text
C05: 217
C06: 217
C07: 217
POS-01: 217
```

## Rows by split

```text
holdout: 84
test: 88
train: 608
val: 88
```

## Safety boundary

```text
allowed: aggregate score-band counts only
blocked: row-level scores
blocked: sample identifiers
blocked: raw prediction CSV download
blocked: private file paths in responses
blocked: feature values
blocked: model files
blocked: map overlays
blocked: public serving
```

## Current H5 checklist

```text
[x] H5 operator-only aggregate service
[x] H5 operator-only aggregate route
[x] H5 frontend aggregate summary panel
[x] H5 no-row-leak tests
[x] H5 score-band aggregate review script
[x] H5 score-band dry-run
[x] H5 score-band write outside Git
[x] H5 score-band write result recorded
[ ] R1 REPORT_640 real app-vs-reference parity plan       <- NEXT RECOMMENDED
```

## Interpretation

```text
The current private model output is concentrated in low and high score bands.
There are 651 rows in the 0.00-0.10 band and 217 rows in the 0.75-1.00 band.
No middle-band rows are present in this private aggregate review.
```
