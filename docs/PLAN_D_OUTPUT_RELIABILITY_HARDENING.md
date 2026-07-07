# Plan D Output Reliability Hardening

## Date

2026-07-07

## Status

Docs-only planning change.

```text
active_proposed_track: Plan D - output reliability hardening
behavior_changed: no
public_private_boundary_changed: no
external_rerun_required: no
```

Plan D exists because review found code paths that can produce misleading app outputs even when a run finishes successfully. This document turns those findings into a staged fix plan.

This plan is about software correctness, data-quality handling, and artifact consistency. It does not validate any physical-world conclusion.

## Operating rules

```text
1. Keep each fix small and reviewable.
2. Add or update tests before each behavior change where practical.
3. Keep private/local-only data out of public docs, UI, logs, and public artifacts.
4. Use one source of truth per artifact family.
5. If app behavior intentionally corrects a notebook bug, mark it PARITY_CORRECTS and document why.
6. Do not claim frozen numeric parity unless exact frozen reference outputs exist.
7. Prefer explicit QA-blocked status over silent success on weak or missing data.
```

## Problem classes to fix

```text
P0 direct output corruption
  - invalid pixels become finite hypercube signal
  - PCA consumes valid_mask as a numeric data channel
  - PCA, object extraction, and classifier do not share one valid-pixel policy
  - focus statistics allow nodata sentinel values into robust stats

P1 collapsed or misleading scores
  - classifier clamps features into [0, 1]
  - dominant_class_id is alphabetical, not most frequent
  - metal diagnostic mixes raw mass-scale values with ratio-scale values
  - metal diagnostic fallback headers contain corrupted strings

P1 contradictory products
  - multiple stages write REPORT_640-like products with the same names but different formulas
  - stack outputs and per-band outputs can disagree

P1 raw scaling bugs
  - Landsat ST_B10 is compared to Kelvin thresholds in some places before applying Collection 2 scale factors
  - AIX thermal norm bands scale raw ST_B10 directly
  - thermal QA masking is not applied consistently

P1 missing evidence paths
  - focus hard classifier references terrain and EM/magnetic evidence that is not loaded into analysis_bands
  - missing evidence is treated as zero-like input instead of unavailable input

P2 metadata and export consistency
  - 17 m focus geometry has radius-vs-width mismatch
  - reports hardcode 2 m super-resolution metadata on a 10 m grid
  - KML text is joined with literal backslash-n instead of real newlines

P2 data-quality fragility
  - low-valid-fraction optical composites can pass silently
  - date windows are pinned in code
  - DEM topography can use a single tile instead of a mosaic
  - SAR filter and incidence-angle validity need stronger guards
```

## Phase D0 - Tests and contracts first

Goal: write protective tests and contracts before broad behavior edits.

Target files:

```text
app/pipeline/stages/hypercube.py
app/pipeline/stages/pca_anomaly.py
app/pipeline/stages/object_extract.py
app/pipeline/stages/classifier.py
app/pipeline/stages/focus_mask.py
app/pipeline/stages/s2_indices.py
app/pipeline/stages/report_640.py
app/pipeline/stages/thermal.py
app/pipeline/stages/sar_rtc.py
tests/
```

Required test coverage:

```text
D0.1 hypercube invalid values do not become finite signal
D0.2 PCA excludes valid_mask from feature channels
D0.3 PCA scores only canonical valid pixels
D0.4 object extraction cannot create candidates from invalid-only areas
D0.5 classifier uses valid_mask, not only np.isfinite
D0.6 dominant_class_id uses most-common class with deterministic tie-break
D0.7 focus stats exclude NaN, inf, and nodata sentinel values
D0.8 duplicate REPORT_640 ownership is blocked, renamed, or explicitly documented
D0.9 Kelvin thresholds use scaled Landsat ST_B10
D0.10 focus geometry has one documented meaning
D0.11 KML output uses real newlines
```

Acceptance gate:

```text
New tests pass.
No private/local-only sample values are committed as fixtures.
```

## Phase D1 - Fix nodata and valid-mask chain

Goal: remove the largest direct false-output source.

Implementation steps:

```text
D1.1 Add one shared helper for valid arrays and nodata filtering.
D1.2 In hypercube assembly, preserve invalid source pixels as invalid until write time.
D1.3 Define one downstream valid-mask policy.
D1.4 Do not normalize invalid pixels by replacing them with 0.0 first.
D1.5 Persist valid_mask as metadata/support, not as a PCA feature channel.
D1.6 In PCA, fit and score only valid pixels.
D1.7 In PCA output, leave invalid pixels nodata or exclude them from thresholding.
D1.8 In object_extract, gate candidates by valid_mask.
D1.9 In classifier, compute features only from valid object pixels.
D1.10 In focus_mask, use the shared nodata-aware helper for core/ring/scene stats.
D1.11 In sar_rtc, explicitly reject nodata incidence angle before correction.
```

Acceptance gate:

```text
Synthetic nodata borders produce no detections in invalid-only regions.
Objects touching invalid pixels do not use invalid pixels in signal features.
PCA QA records feature_channel_count excluding valid_mask.
```

## Phase D2 - Correct PCA anomaly scoring and thresholds

Goal: make anomaly scoring statistical, not only display percentile based.

Implementation steps:

```text
D2.1 Keep legacy PCA only behind an explicit compatibility mode if needed.
D2.2 Add corrected PCA scoring using whitened PC distance or reconstruction error.
D2.3 Exclude valid_mask, all-nodata bands, near-constant bands, and degenerate-IQR bands from PCA fit.
D2.4 Record included and excluded band names with reasons in QA JSON.
D2.5 Keep display stretch separate from raw anomaly score.
D2.6 Threshold object candidates from raw score, for example robust z-score, not only p90/max(0.6).
D2.7 Add low-valid-fraction blocking.
```

Acceptance gate:

```text
Pure-noise synthetic scenes can produce zero objects.
Low-valid-fraction scenes cannot silently pass as normal success.
QA records raw threshold method and display stretch separately.
```

## Phase D3 - Repair classifier features

Goal: make classification output depend on meaningful object evidence.

Implementation steps:

```text
D3.1 Fix dominant_class_id to most-common class with deterministic tie-break.
D3.2 Remove raw feature clamps that erase negative z-score information.
D3.3 Compute features from valid pixels only.
D3.4 Robust-scale object features against scene or local background.
D3.5 Replace three mixed-unit features with a compact vector:
     - raw anomaly mean and peak
     - per-band local contrast
     - object area and compactness
     - valid pixel fraction
D3.6 Keep public-safe neutral labels if required, but avoid overclaiming physical meaning.
```

Acceptance gate:

```text
Negative, zero, and positive synthetic feature cases remain distinguishable.
Class distribution is not collapsed by construction.
Cluster dominant labels match the most frequent object labels.
```

## Phase D4 - Single source of truth for REPORT_640 and thermal scaling

Goal: remove contradictory named products and raw-DN thermal bugs.

Implementation steps:

```text
D4.1 Choose one canonical owner for REPORT_640 products, preferably report_640.py.
D4.2 Rename fusion-derived outputs if they are kept.
D4.3 Rebuild or rename REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy so name and formula match.
D4.4 Add source_family, formula_version, parity_category, and correction_reason to manifests.
D4.5 Use Landsat Collection 2 ST_B10 scale helper everywhere Kelvin is intended:
     Kelvin = 0.00341802 * DN + 149.0
D4.6 Apply thermal QA masking consistently.
D4.7 Fix Zero_Point thermal condition to compare scaled Kelvin.
D4.8 Fix AIX thermal Norm01 to scale Kelvin, not raw DN.
D4.9 Use DEM mosaic for AIX terrain products.
```

Acceptance gate:

```text
No two stages write the same canonical REPORT_640 name with different formulas.
Thermal thresholds are applied only after ST_B10 scaling.
AIX terrain products cover the intended grid or fail with QA-blocked status.
```

## Phase D5 - Fix focus evidence handling

Goal: make missing evidence explicit and make terrain gating real.

Implementation steps:

```text
D5.1 Load DEM_Slope, DEM_Roughness, and DEM_TPI into focus analysis_bands from existing DEM derivative products.
D5.2 If EM or magnetic products are unavailable, mark them unavailable and remove or renormalize their weights.
D5.3 Do not silently treat missing evidence as zero.
D5.4 Add evidence availability flags to hard-classifier JSON/TXT/CSV.
D5.5 Compute local z-scores against scene or ring background, not only against a tiny core.
D5.6 Fix metal diagnostic to use normalized/z-scored columns where available.
D5.7 Replace corrupted fallback header strings with valid UTF-8 names or explicit canonical English columns.
```

Acceptance gate:

```text
surface_exclusion_score varies in synthetic terrain cases.
Unavailable evidence is reported as unavailable.
Metal diagnostic is not dominated by raw mass scale in synthetic tests.
UTF-8 headers round-trip without mojibake fallback strings.
```

## Phase D6 - Fix geometry metadata and KML formatting

Goal: make exports internally consistent.

Implementation steps:

```text
D6.1 Decide whether 17 m means radius or full width.
D6.2 Rename constants to avoid ambiguity, for example FOCUS_RADIUS_M or FOCUS_WIDTH_M.
D6.3 Make focus_mask and location_exports use the same geometry contract.
D6.4 Remove or correct hardcoded 2 m super-resolution metadata.
D6.5 If no true super-resolution exists, report native 10 m analysis honestly.
D6.6 Replace literal backslash-n joins with real newline joins in KML output.
D6.7 Add a KML smoke test for basic XML structure.
```

Acceptance gate:

```text
Focus raster geometry and exported geometry agree.
Reports do not claim 2 m analysis unless a real documented step exists.
Generated KML has real XML line breaks.
```

## Phase D7 - Improve S2 and SAR data-quality handling

Goal: reduce stale, noisy, and silently weak inputs.

Implementation steps:

```text
D7.1 Make S1, S2, and Landsat date windows configurable per run.
D7.2 Keep deterministic defaults for tests.
D7.3 Add per-pixel S2 cloud masking instead of relying only on strict scene-level cloud percentage.
D7.4 Enforce valid observation count or valid fraction in QA.
D7.5 Replace constant additive Lee noise variance with a multiplicative Lee or Refined Lee approach.
D7.6 Record SAR orbit, pair, and date metadata for reproducibility.
D7.7 Mark intentional notebook corrections as PARITY_CORRECTS.
```

Acceptance gate:

```text
Run settings can override date windows.
Empty or mostly masked S2 composites cannot silently pass as normal outputs.
SAR filter tests show it does not degenerate into plain box blur on representative synthetic data.
```

## Phase D8 - Lower-severity cleanup

Goal: remove latent future traps.

Implementation steps:

```text
D8.1 Delete or quarantine dead classifier helpers that map non-existent class names.
D8.2 If dead helpers are kept, add tests before wiring them.
D8.3 Fix categorical WorldCover aggregation if exported rows use mean on class codes.
D8.4 Use categorical mode or one-hot/fraction bands instead of categorical mean.
D8.5 Document unsupported notebook-only behavior as not implemented instead of silent defaults.
```

Acceptance gate:

```text
Dead helpers cannot be reintroduced without tests.
Categorical class codes are not averaged into misleading numeric classes.
```

## Suggested PR breakdown

```text
PR D0: tests and contracts only
PR D1: nodata and valid-mask chain
PR D2: PCA anomaly and object thresholding
PR D3: classifier feature repair
PR D4: REPORT_640 ownership and thermal scaling
PR D5: focus evidence and metal diagnostic
PR D6: geometry metadata and KML formatting
PR D7: S2/SAR data quality and configurable dates
PR D8: cleanup and dead-code quarantine
```

Do not combine all phases into one large code PR. D1 should happen first because many later fixes depend on correct valid-pixel behavior.

## First implementation target

Start with D0 plus D1.

Minimum first patch:

```text
1. Add shared nodata-aware helper.
2. Patch hypercube invalid handling.
3. Patch PCA valid-mask handling.
4. Patch object_extract valid-mask gating.
5. Patch classifier valid-mask usage.
6. Patch focus stats sentinel filtering.
7. Add tests for changed behavior.
8. Add QA manifest fields that state the valid-mask policy.
```

## Completion definition

Plan D is complete when:

```text
- invalid pixels cannot create finite false signal
- PCA, object extraction, classifier, and focus analysis share one valid-pixel policy
- classifier labels and dominant cluster labels are test-backed
- canonical REPORT_640 names have one owner and one formula
- Landsat ST_B10 scale factors are used wherever Kelvin is intended
- missing focus evidence is explicit, not silently zero
- focus geometry and metadata are internally consistent
- low-valid-fraction inputs fail or are clearly QA-blocked
- public outputs keep the public/private artifact boundary intact
```
