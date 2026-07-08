# Plan D Output Reliability Hardening

## Date

2026-07-07

## Status

Docs-only planning change.

```text
active_proposed_track: Plan D - private-local output reliability and enhancement
behavior_changed: yes, only when reliability/output-quality fixes are implemented
public_private_boundary_changed: yes, plan is now private-local/operator-first
external_rerun_required: no
```

Plan D exists because review found code paths that can produce misleading app outputs even when a run finishes successfully. This document turns those findings into a staged fix plan.

This plan is now scoped for a private/local operator app. The priority is to improve local output quality, diagnostic depth, and correctness. Do not add public-safe redaction, coordinate suppression, neutralization, or artifact hiding as Plan D work unless the operator explicitly asks for it. Local runtime outputs may be rich and detailed. Do not commit private sample values, exact private targets, or local-only data into the repository.

This plan is about software correctness, data-quality handling, and artifact consistency. It does not validate any physical-world conclusion.

## Operating rules

```text
1. Keep each fix small and reviewable.
2. Add or update tests before each behavior change where practical.
3. Treat the app as private/local: improve operator-visible local outputs; do not commit private sample values or local-only data into the repository.
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
D3.6 Keep rich private-local diagnostic labels/features; avoid unsupported certainty, but do not neutralize or hide useful operator evidence.
```

Acceptance gate:

```text
Negative, zero, and positive synthetic feature cases remain distinguishable.
Class distribution is not collapsed by construction.
Cluster dominant labels match the most frequent object labels.
```

## Phase D4 - Single source of truth for REPORT_640 and thermal scaling

Goal: remove contradictory `REPORT_640` source usage and raw-DN thermal bugs without breaking notebook-parity outputs.

Implementation status:

```text
D4.1 Done. Canonical root REPORT_640_*.tif owner is report_640.py.
D4.2 Done. REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy remains a separate cell-099 stack from s2_indices.py, not the canonical root REPORT_640 owner.
D4.3 Done by ownership lock. Root REPORT_640 rasters are not rebuilt from the cell-099 fusion stack.
D4.4 Done. REPORT_640_Mass_Report metadata records source_family, formula_version, parity_category, correction_reason, thermal_input_units, and thermal_scaling_applied.
D4.5 Done. Kelvin scaling is used where Kelvin is intended. REPORT_640_Mass_Report intentionally remains raw-ST_B10 notebook parity.
D4.6 Done. Thermal QA masking is applied consistently to notebook L9 and AIX/fusion Landsat ST_B10 sources.
D4.7 Done. Zero_Point thermal condition compares scaled Kelvin to the 310 K threshold.
D4.8 Done. AIX thermal Norm01 scales Landsat ST_B10 to Kelvin before unitScale(280, 320).
D4.9 Done. Focus-mask analysis now consumes canonical root REPORT_640_*.tif rasters, not cell-099 NPY_RADAR_BANDS report-name arrays.
D4.10 Done. This section locks the final REPORT_640 source ownership decision.
```

Ownership lock:

```text
Canonical root REPORT_640 rasters:
  owner: app/pipeline/stages/report_640.py
  outputs:
    REPORT_640_Pottery_Report.tif
    REPORT_640_Mass_Report.tif
    REPORT_640_FINAL_Zero_Point_Targets.tif

Notebook cell-099 fusion stack:
  owner: app/pipeline/stages/s2_indices.py
  output:
    NPY_STACKS/REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy
  status:
    kept as a separate notebook stack alias; it is not the canonical root REPORT_640 source.

Downstream consumers:
  hypercube.py uses canonical root REPORT_640_*.tif rasters.
  focus_mask.py uses canonical root REPORT_640_*.tif rasters.
```

Acceptance gate:

```text
No two stages write the same canonical root REPORT_640_*.tif output.
Cell-099 fusion-stack outputs may keep notebook band names, but they are not treated as root REPORT_640 owners.
Thermal thresholds are applied only after ST_B10 scaling.
REPORT_640_Mass_Report is explicitly documented as raw-ST_B10 notebook parity, not Kelvin thermal anomaly.
Focus analysis uses the canonical root REPORT_640 rasters.
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

Implementation status:

```text
D6.1 Done. The focus-mask contract now documents 17 m as a radius.
D6.2 Done. focus_mask.py now uses FOCUS_RADIUS_M, while keeping FOCUS_SIZE_M as a backward-compatible alias.
D6.3 Done for focus_mask output metadata. Summary and StageResult metadata expose focus_radius_m, focus_diameter_m, focus_size_m_legacy_meaning, and focus_mask_contract.
D6.4 No active 2 m super-resolution metadata patch was needed in this slice.
D6.5 No active 2 m super-resolution metadata patch was needed in this slice.
D6.6 Done. Field-operation KML joins now use real newline characters instead of literal backslash-n text.
D6.7 Done. Focus-mask tests assert KML contains real newlines and no literal backslash-n text.
```

Acceptance gate:

```text
Focus-mask radius meaning is explicit: 17 m radius, 34 m diameter.
Backward-compatible focus_size_m is retained but marked as radius_m.
Generated focus KML has real XML line breaks.
Focused reliability tests passed: focus_mask, report_640, s2_indices, and hypercube.
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

## Private-local output policy update

```text
Plan D is not a public-safe/redaction track.
Do not add future tasks whose only purpose is public exposure hardening, coordinate suppression, HTTP hiding, or neutralized wording.
Keep reliability and truthfulness fixes: nodata handling, scoring correctness, valid-mask gating, thermal scaling, geometry consistency, data-quality blocking, and richer diagnostics.
If a future change would reduce private/local output detail, mark it out of scope unless the operator explicitly requests it.
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
