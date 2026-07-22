# TAMUCC Sentinel-1 Site/Background Effect Assessment

Status: completed; focused tests and private execution passed.

## Blocker status

Depth Blocker 2 remains open.

The completed TAMUCC extraction supplies a private descriptive Sentinel-1
site/background dataset with 80 usable pre-construction acquisitions and 81 usable
post-construction acquisitions. One post acquisition is retained in provenance but
excluded because both polygons had zero valid pixels after the common quality mask.

This dataset can test whether the provisional site area changed differently from
the nearby background. It cannot by itself calibrate depth because the public record
still lacks:

- an official surveyed site and target map;
- target-level depth labels tied to the satellite pixels;
- numerical reference uncertainty for those depths;
- contract-ready confirmed-negative calibration records;
- group-separated train, validation, and holdout depth records.

## Purpose

The utility reads the private matched-feature output and performs an offline,
descriptive pre/post comparison of the per-image site-minus-background values.

It does not:

- contact Earth Engine;
- select new satellite images;
- print image identities;
- print numeric effect values to the console;
- estimate depth;
- classify buried targets;
- perform causal inference;
- perform scientific validation;
- enable app depth output.

## Primary comparison

For each of the five neutral feature families, the primary series is the per-image
site-minus-background median.

The assessment reports privately:

- pre and post observation counts;
- pre and post medians;
- post-minus-pre median shift;
- pre and post interquartile ranges;
- the shift expressed in pooled-IQR units;
- the fraction of post observations above the pre median.

The same descriptive shift is also calculated for the p25 and p75 summaries.
Quantile-direction agreement means the p25, median, and p75 shifts all point in the
same non-zero direction.

## Screening buckets

The magnitude buckets are descriptive only:

```text
under_0_25_iqr
0_25_to_0_5_iqr
0_5_to_1_iqr
at_least_1_iqr
```

These are not probability statements, confidence levels, or evidence of depth.

## Files

```text
scripts/assess_depth_s1_site_background_effect.py
tests/unit/test_depth_s1_site_background_effect.py
```

Private input and output remain outside Git.

## First dry run

```powershell
python .\scripts\assess_depth_s1_site_background_effect.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_site_background_effect.json"
```

Expected:

```text
status = descriptive_effect_assessment_dry_run_ready
included_pre_count = 80
included_post_count = 81
input_rows_excluded_from_analysis = 1
private_output_written = false
```

## First execution

```powershell
python .\scripts\assess_depth_s1_site_background_effect.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_site_background_effect.json" `
  --execute
```

The console prints only counts and categorical screening summaries. Detailed numeric
effect values are written only to the private output.

## Completion gate

```text
focused tests pass
redaction-risk tests pass
full unit suite passes
private dry run passes
private execution completes
```

A completed effect assessment still does not close Depth Blocker 2. It only decides
whether the TAMUCC whole-site Sentinel-1 feasibility path shows a descriptive change
worth further investigation.
## Observed result

The private descriptive assessment completed with 80 usable pre-construction
acquisitions, 81 usable post-construction acquisitions, and one provenance-retained
zero-valid-pixel row excluded from analysis.

All five feature families showed a directional pre/post change. The incidence-angle
difference had the strongest shift, so the raw radar-feature changes were not treated
as independently interpretable and the incidence-adjustment step was required.
