# Depth Matched Sentinel-1 Angle-and-Season Adjusted Screen — 2026-07-20

Status: implemented on `main`; local verification and private execution remain.

## Plain-language purpose

The first descriptive comparison found that the controlled site changed relative to the reviewed background after the transition. Four radar features moved in the negative direction and one moved in the positive direction.

The site-minus-background incidence-angle feature also moved. Therefore the descriptive result cannot yet separate a site-specific radar change from a change associated with radar viewing geometry.

This final local screen asks one narrow question:

```text
After adjusting for site-minus-background incidence angle and month-of-year,
does any pre/post shift remain in the four radar signal features?
```

## Inputs

The tool reads the private matched-feature table outside Git. It uses the existing 161 usable rows:

```text
usable pre rows = 80
usable post rows = 81
excluded zero-valid rows = 1
```

It performs no Earth Engine query and does not re-extract imagery.

## Features tested

The incidence-angle difference is used as a control, not as a tested signal.

The tested features are:

```text
vv_db
vh_db
vv_minus_vh_db
vh_to_vv_linear_ratio
```

## Controls and test

For each tested feature, the tool:

1. uses the per-image site-minus-background median;
2. removes the linear relationship with site-minus-background incidence angle;
3. removes a sine/cosine month-of-year seasonal pattern;
4. compares the adjusted post median with the adjusted pre median;
5. runs a deterministic month-stratified permutation test;
6. applies Holm correction across the four tested features.

The default contract is:

```text
permutations = 5000
alpha = 0.05
multiple testing correction = Holm
```

## Possible decisions

```text
no_angle_season_adjusted_shift_support
```

means the descriptive movement is not supported after the incidence and seasonal controls.

```text
angle_season_adjusted_shift_support
```

means at least one radar feature still shows a statistically supported pre/post shift after those controls.

Neither decision proves causation, a buried object, material identity, or depth.

## Privacy

Exact shifts, coefficients, p-values, and corrected p-values are written only to a private output outside Git.

Console output contains only:

- usable and excluded row counts;
- tested feature count;
- whether incidence and season controls were applied;
- support booleans and directions by feature;
- no image identities, coordinates, geometry, paths, exact feature values, or p-values.

## Hard boundaries

```text
causal_test_run = false
scientific_validation_run = false
depth_claim_made = false
training_started = false
app_depth_enabled = false
```

This screen does not estimate depth and does not enable app depth output.

## Completion gate

- [x] Explain the incidence-angle blocker in plain English.
- [x] Implement the local adjusted screen.
- [x] Add synthetic false-shift and true-shift regression tests.
- [ ] Run the seven focused tests.
- [ ] Execute the private adjusted screen.
- [ ] Report the final controlled-screen decision in plain English.
