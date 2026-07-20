# Matched Sentinel-1 Angle/Season Adjusted Result — 2026-07-20

Status: exploratory controlled screen completed; no depth claim.

## Software verification note

The first local test run produced one failed synthetic strong-shift test. Investigation found that the synthetic fixture collapsed to only two perfectly tied residual values, which is a pathological case for a median-based permutation statistic. The real analysis implementation was not changed. The fixture was corrected by adding a small deterministic second seasonal harmonic balanced across pre and post rows.

Fix commit:

```text
c0de34134a73d5c0d99502d1b89c78e2f0c1d613
```

The corrected focused suite was then confirmed locally:

```text
7 passed, 1 non-blocking pytest-cache warning
```

## Private controlled-screen execution

The private local screen completed using:

- 162 input rows;
- one zero-valid-pixel post row excluded without imputation;
- 80 usable pre rows;
- 81 usable post rows;
- incidence-angle control;
- month-of-year sine/cosine seasonal controls;
- month-stratified permutation testing;
- Holm multiple-testing correction across four signal features.

Aggregate result:

```text
decision = angle_season_adjusted_shift_support
supported_shift_feature_count = 3 of 4
```

Supported directions:

```text
VH dB = negative
VH/VV linear ratio = negative
VV−VH dB contrast = positive
```

Unsupported after correction:

```text
VV dB = negative direction, but not supported after Holm correction
```

## Meaning

This result says that three radar feature differences between the site and reviewed background remained after the implemented incidence-angle and seasonal controls.

It does not identify the cause of those changes. It does not prove a buried object, estimate depth, provide a probability of confirmation, validate the notebook labels, or enable app depth output.

Current app boundary remains:

```text
app_depth_enabled = false
depth_not_available
```
