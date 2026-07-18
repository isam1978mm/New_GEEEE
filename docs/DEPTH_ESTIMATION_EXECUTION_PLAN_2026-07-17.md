# Depth Estimation Execution Plan — 2026-07-17

## Status

Planning document only. No numerical depth capability is approved or implemented by this document.

## Required reading order

Future audits and implementation sessions must read these documents first:

1. `AUDIT_DO_NOT_BREAK_CONTRACTS.md`
2. `docs/LOCAL_PRIVATE_CORE_CLASSIFIER_EXECUTION_PLAN_2026-07-15.md`
3. `docs/DEPTH_ESTIMATION_EXECUTION_PLAN_2026-07-17.md`
4. `docs/PRD_v0.5.md` as historical context only

## Owner objective

Add a depth-estimation capability for the private local app so that, after the classifier identifies a candidate finding, the app can estimate how deep the candidate may be.

The preferred final output is easy English, for example:

> The strongest candidate appears shallow, with an estimated depth range of 1.5 to 3 metres. Depth quality is low because the estimate is based on limited calibration data.

A single exact depth number must not be shown unless the method can support it. A range is preferred.

## Current capability

The current app does not measure physical depth in metres.

Some existing SAR-derived features have depth-related names or may react differently to shallow and deeper structures. These are signal proxies only. They are not calibrated depth measurements and must not be relabeled as metres.

Examples of current inputs that may be investigated:

- Sentinel-1 VV and VH values
- VV/VH ratios and differences
- incidence angle
- SAR coherence or temporal stability, when available
- optical and thermal anomaly strength
- DEM and terrain derivatives
- object size, shape, compactness, and connected-component features
- classifier score and finding family
- valid-pixel and data-quality metrics

## Hard boundary

Until calibration and validation are complete, the app may report only:

- `depth_not_available`, or
- an explicitly experimental relative category such as `shallow-looking`, `medium-looking`, or `deep-looking`

The app must not report `2.4 m`, `5 m`, or any other numerical depth merely by converting a radar ratio or classifier score.

## Target output contract

Each candidate may eventually include:

```text
candidate_id
depth_status
estimated_depth_min_m
estimated_depth_max_m
estimated_depth_best_m
depth_category
depth_quality
depth_method_version
calibration_dataset_version
supporting_features
warnings
```

Allowed `depth_status` values:

```text
not_available
insufficient_data
relative_only
calibrated_range
validated_range
```

The final area summary may include depth only when `depth_status` is `calibrated_range` or `validated_range`.

## Phase 0 — Scope lock

Goal: define exactly what the feature estimates.

Tasks:

1. Decide whether depth refers to the top of the anomaly, centre of the anomaly, or total vertical extent.
2. Define the supported finding families.
3. Define the expected depth range.
4. Define the required output resolution.
5. Decide whether the first release uses broad categories or metre ranges.

Recommended first target:

- Estimate depth to the top of the candidate.
- Use three broad classes: shallow, medium, deep.
- Add metre ranges only after calibration proves they are meaningful.

Acceptance:

- One written depth definition.
- One supported depth range.
- One list of supported finding families.
- One agreed first-release output type.

## Phase 1 — Existing signal inventory

Goal: identify which current app outputs contain independent depth information.

Tasks:

1. Inventory all depth-related notebook cells and app features.
2. Separate genuine sensor measurements from derived names and heuristics.
3. Trace each feature to its source band and formula.
4. Record spatial resolution, acquisition date, nodata behavior, and normalization.
5. Remove any circular inputs derived from classifier labels or target decisions.

Required artifact:

```text
docs/DEPTH_FEATURE_INVENTORY.md
```

Acceptance:

- Every proposed depth feature has a source, formula, unit, and limitation.
- No target label, classifier output, or depth estimate is reused as an input feature.

## Phase 2 — Calibration dataset

Goal: create examples where the true depth is already known.

A numerical model requires known-depth reference cases. These may come from controlled test sites, engineering records, published benchmark datasets, or other independently documented sources.

Each calibration record should include:

```text
site_id
finding_family
known_depth_top_m
known_depth_bottom_m
target_size
target_material_or_structure
soil_or_surface_type
moisture_or_season
terrain
observation_dates
sensor_sources
quality_notes
```

Tasks:

1. Define inclusion and exclusion rules.
2. Keep training and validation locations separate.
3. Include examples with no target.
4. Include different soils, terrain, moisture, seasons, and target sizes.
5. Version and hash the calibration dataset.
6. Record uncertainty in the reference depth itself.

Acceptance:

- Known depths are traceable to a source.
- Validation sites are not used for model fitting.
- Dataset limitations are documented.

## Phase 3 — Relative-depth baseline

Goal: test whether the existing signals can distinguish broad depth categories before attempting metres.

Tasks:

1. Define category boundaries from the supported depth range.
2. Train or fit a simple, interpretable baseline.
3. Compare against a majority-class and random baseline.
4. Measure category accuracy and confusion.
5. Test stability across locations, seasons, and target families.
6. Abstain when data quality is weak.

Recommended first models:

- threshold/rule baseline
- ordinal logistic regression
- shallow decision tree
- calibrated gradient-boosted model only if simpler models fail

Acceptance:

- Better than baseline on held-out sites.
- Error and abstention rates are reported.
- No claim of metre accuracy.

## Phase 4 — Numerical depth-range model

Goal: estimate a depth interval only after the relative-depth baseline succeeds.

Tasks:

1. Predict a depth range, not only a single point.
2. Use grouped validation by physical site.
3. Calculate median absolute error and interval coverage.
4. Evaluate errors separately by finding family, soil type, and depth band.
5. Add out-of-distribution detection.
6. Return `insufficient_data` when the candidate is unlike calibration examples.

Possible methods:

- robust linear or nonlinear regression
- quantile regression for lower and upper depth bounds
- calibrated tree ensemble
- Bayesian regression where reference uncertainty is available

Acceptance thresholds must be chosen after dataset inspection. They must not be invented before seeing calibration quality.

## Phase 5 — Confounder controls

Goal: prevent the model from confusing depth with unrelated conditions.

Required controls:

- target size
- target family or material
- soil and surface type
- moisture and season
- terrain slope and roughness
- SAR incidence angle and orbit geometry
- sensor resolution
- observation count and temporal dispersion
- nodata and valid-pixel coverage

Tests must determine whether the model is merely learning one of these variables instead of depth.

Acceptance:

- Confounder sensitivity report exists.
- Large unstable shifts cause abstention or block release.

## Phase 6 — App architecture

Goal: add depth estimation without weakening existing pipeline contracts.

Recommended implementation:

```text
app/pipeline/stages/depth_estimation.py
tests/unit/test_depth_estimation.py
tests/integration/test_depth_estimation_outputs.py
docs/DEPTH_METHOD_CARD.md
```

Inputs:

- completed classifier candidates
- connected-component masks
- approved independent sensor features
- run-quality metadata
- calibration model and method manifest

Outputs:

```text
depth/depth_estimates.csv
depth/depth_summary.json
depth/depth_method_manifest.json
```

The stage must:

1. Refuse incomplete runs.
2. Refuse missing required features.
3. Refuse unsupported finding families.
4. Preserve GRID alignment.
5. Write model, feature, and calibration versions.
6. Never silently substitute a proxy ratio for metres.
7. Remain compatible with old runs that have no depth output.

## Phase 7 — Easy-English presentation

Goal: explain depth without requiring technical knowledge.

Example when calibrated:

> The strongest candidate has an estimated depth range of 1.5 to 3 metres. The estimate quality is medium. The main uncertainty comes from limited calibration for this soil type.

Example when only relative:

> The candidate looks shallow compared with other candidates in this run. A depth in metres is not available.

Example when unsupported:

> Depth could not be estimated because the required radar coverage was not usable.

Required UI fields:

- estimated range or relative category
- depth quality
- one short reason for uncertainty
- method version
- no false precision

## Phase 8 — Validation gates

Required validation:

1. Unit tests for feature extraction and missing-data behavior.
2. Frozen calibration fixtures.
3. Grouped site-level cross-validation.
4. Holdout-location evaluation.
5. Negative/no-target examples.
6. Threshold sensitivity tests.
7. Repeated-run stability tests.
8. Legacy-run compatibility tests.
9. Output schema and download tests.
10. Easy-English wording tests.

Release gates:

- No numerical depth without held-out validation.
- No single exact number when uncertainty is wide.
- No depth output when quality gates fail.
- No regression to classifier or artifact compatibility.
- No use of generated target layers as depth inputs.

## Phase 9 — Rollout order

1. Inventory current depth-related features.
2. Produce a relative-depth research report.
3. Build the known-depth calibration dataset.
4. Validate broad categories.
5. Validate metre ranges.
6. Implement backend stage and artifacts.
7. Add frontend summary.
8. Run full compatibility and regression suite.
9. Enable numerical depth only after acceptance gates pass.

## Non-goals

This plan does not:

- claim that satellite imagery directly measures burial depth
- convert a named depth proxy into metres
- guarantee target identity
- guarantee physical confirmation
- replace known-depth calibration
- modify the classifier before the depth method is validated

## Completion definition

Depth estimation is complete only when:

- the target depth definition is fixed
- the calibration dataset is versioned and traceable
- held-out validation results are documented
- uncertainty ranges are produced
- unsupported cases abstain
- the app presents the result in easy English
- old runs without depth remain fully usable
- all required tests pass
