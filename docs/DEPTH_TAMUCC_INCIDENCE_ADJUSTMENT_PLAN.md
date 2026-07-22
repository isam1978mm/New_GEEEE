# TAMUCC Sentinel-1 Incidence-Adjusted Effect Assessment

Status: completed; focused tests and private execution passed.

## Why this step is required

The first descriptive whole-site comparison found that the incidence-angle
site-minus-background feature changed more strongly than the radar-amplitude
features. Therefore, the raw radar shifts cannot yet be interpreted as a
site-specific construction response.

This step tests whether the four radar-feature shifts remain after accounting for
their pre-period relationship with incidence angle.

## Method

For each radar feature median:

1. Use only usable pre-construction acquisitions.
2. Fit a simple linear baseline:

```text
radar site-minus-background = intercept + slope × incidence site-minus-background
```

3. Calculate residuals for every usable pre and post acquisition.
4. Compare the median residual in the post period with the median residual in the
   pre period.
5. Express the residual shift using the pooled pre/post residual IQR.
6. Report how many post incidence values lie inside the pre-period incidence range.

The regression is a nuisance adjustment, not a physical radar model.

## Outputs

The console reports only:

- usable row counts;
- categorical adjusted direction;
- categorical adjusted magnitude;
- whether adjustment changed the direction;
- incidence-overlap category.

Numeric slopes, residuals, ranges, and shifts are written only to the private JSON
output.

## Limitations

This assessment does not:

- prove that construction caused a radar change;
- identify buried targets;
- establish known depth;
- estimate depth;
- supply target-level labels;
- perform hypothesis testing;
- enable depth output in the app.

A remaining adjusted radar shift would justify further feasibility work only. A
disappearing shift would indicate that the original raw change was explainable by
incidence geometry under this descriptive model.

## Files

```text
scripts/assess_depth_s1_incidence_adjusted_effect.py
tests/unit/test_depth_s1_incidence_adjusted_effect.py
```

## Dry run

```powershell
python .\scripts\assess_depth_s1_incidence_adjusted_effect.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_incidence_adjusted_effect.json"
```

## Execution

```powershell
python .\scripts\assess_depth_s1_incidence_adjusted_effect.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_incidence_adjusted_effect.json" `
  --execute
```

## Blocker status

Depth Blocker 2 remains open regardless of this result because target-level known
depths, uncertainties, confirmed negatives, and independent group splits are still
missing.
## Observed result

All four radar-feature directions remained after the pre-period incidence
adjustment. No direction reversed. The VH backscatter difference retained the
largest adjusted magnitude category; the other adjusted shifts remained small.

This supported continued whole-site feasibility checking, not depth calibration.
