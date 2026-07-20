# Depth Matched Sentinel-1 Descriptive Screen Plan — 2026-07-20

Status: ready for implementation after the private completeness audit explained all 30 missing statistics by one post-period acquisition with zero valid pixels.

## Plain-language purpose

The Earth Engine extraction reached all 162 exact matched Sentinel-1 acquisitions. One post-period acquisition contained no usable pixels in either the site or background polygon after the existing quality mask. That row cannot produce real percentiles and must not be filled with invented values.

The next step therefore excludes only that unusable row and compares the remaining 161 rows:

```text
clean pre rows = 80
clean post rows = 81
excluded zero-valid rows = 1
```

## Comparison

For each neutral Sentinel-1 feature:

```text
vv_db
vh_db
incidence_deg
vv_minus_vh_db
vh_to_vv_linear_ratio
```

use the per-image site-minus-background median. Summarize that quantity separately for pre and post using:

```text
count
p25
median
p75
site-higher fraction
```

Then calculate:

```text
post median minus pre median
change direction: positive, negative, or zero
Cliff's delta as a descriptive distribution-shift measure
```

These are descriptive screening statistics only. They are not a causal test, significance test, target confirmation, physical-depth estimate, calibration result, or app output.

## Exclusion rule

Exclude a complete acquisition row only when at least one required feature has a valid-pixel count of zero on either polygon side.

Do not exclude or repair an unexplained missing value. Any missing statistic with a positive valid-pixel count must stop the screen for investigation.

## Privacy contract

The input and numeric output remain outside Git.

The private numeric output contains aggregate feature statistics but no image identities, coordinates, or geometry. Console output contains only:

```text
input row count
usable pre/post counts
excluded counts by period
feature count
positive/negative/zero shift counts
change direction by feature
```

No exact feature values, image identities, coordinates, geometry, or private paths are printed.

## Completion decision

Successful local execution returns:

```text
matched_s1_descriptive_screen_complete
```

This means only that a descriptive site-versus-background pre/post comparison was produced from 161 usable acquisitions.

## Checklist

- [x] Complete exact site/background acquisition matching.
- [x] Extract all 162 matched rows.
- [x] Explain 30 missing statistics by one zero-valid row.
- [ ] Implement strict zero-valid-row exclusion.
- [ ] Implement descriptive pre/post comparison.
- [ ] Add focused privacy and numeric tests.
- [ ] Run the local private screen.
- [ ] Interpret only as exploratory signal behavior.
