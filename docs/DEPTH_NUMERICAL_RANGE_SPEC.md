# Numerical Depth-Range Method Specification

Status: Phase 4 design artifact only. No numerical model has been fitted, no metre range has been validated, and no numerical depth output is approved for the app.

## Purpose

This document defines how a future private-local experiment may estimate a depth interval after the relative-depth baseline has passed its held-out validation gates.

The target remains:

```text
known_depth_top_m
```

The intended result is a range, not false precision from one exact number.

Example future structure:

```text
estimated_depth_min_m
estimated_depth_max_m
estimated_depth_best_m
depth_quality
depth_status
warnings
```

This specification does not authorize those fields in the current app.

## Current gate

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
relative_depth_holdout_status = not_passed
phase_4_design_status = defined
phase_4_fitting_status = blocked
numerical_depth_app_output = not_available
```

Phase 4 fitting must not begin until:

1. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md` passes its readiness checklist;
2. `docs/DEPTH_RELATIVE_BASELINE_SPEC.md` is fitted on a valid private dataset;
3. the relative-depth method beats its preregistered baselines on untouched physical sites;
4. category errors and abstention behavior are acceptable;
5. the exact dataset, features, splits, preprocessing, and baseline versions are frozen.

## Output contract

A numerical prediction may eventually use:

```text
depth_status = calibrated_range | validated_range | insufficient_data
estimated_depth_min_m
estimated_depth_max_m
estimated_depth_best_m
depth_quality = low | medium | high
depth_method_version
calibration_dataset_version
feature_manifest_version
support_distance
supporting_features
warnings
```

Rules:

- `estimated_depth_min_m` must be less than or equal to `estimated_depth_best_m`.
- `estimated_depth_best_m` must be less than or equal to `estimated_depth_max_m`.
- All values refer to depth to the top of the reference feature.
- The range must not extend below zero metres.
- An unsupported case must return `insufficient_data`, not a guessed interval.
- A single exact number must never replace the interval in user-facing output.
- `validated_range` is allowed only after untouched physical-site holdout evaluation passes.

## Eligible records

A record may enter Phase 4 only when:

- `reference_status=known_depth_positive`;
- the label quality is independently measured or independently reviewed;
- `known_depth_top_m` is present and traceable;
- reference uncertainty is recorded;
- the record passes the calibration-contract inclusion rules;
- the physical site and feature grouping are known;
- the sensor observation is matched to the reference case;
- the feature manifest excludes circular and target-derived values;
- the case belongs to a supported finding family;
- the known depth lies within the supported calibration range.

Records with uncertain, guessed, proxy-derived, or unknown-provenance depths cannot be used for fitting.

Confirmed no-target/background cases remain useful for false-positive and abstention testing, but they do not receive artificial metre labels.

## Unit of analysis

The first numerical model should use one row per independently documented physical reference feature.

Sensor and context values should be summarized over an independently defined reference footprint. The footprint must not be created from the same target mask or classifier result later evaluated as evidence.

All dates and observations belonging to the same physical feature remain linked through one `group_id` and stay in one split.

## Split and evaluation policy

The split unit is the physical site or stronger physical-feature group.

Required behavior:

1. all records sharing a `group_id` remain in one split;
2. related features from one local site remain together unless independence is documented;
3. repeated dates for one site remain together;
4. the final holdout contains physical sites unseen during fitting, model selection, interval tuning, and threshold selection;
5. preprocessing statistics are fitted on training data only;
6. model and interval choices use training and validation data only;
7. the holdout is evaluated once the method is frozen;
8. deterministic split rules and seeds are versioned;
9. a temporal holdout is added when the data supports a separated acquisition period.

No result may be called site-independent when nearby or related sites leak across splits.

## First model order

Models should be tested from simplest to more complex:

1. median-depth baseline;
2. depth-band midpoint baseline derived from the accepted relative class;
3. robust linear regression;
4. constrained nonlinear or spline regression when justified;
5. quantile regression for lower and upper bounds;
6. calibrated tree ensemble only when simpler methods fail and the dataset size supports it;
7. Bayesian regression only when reference uncertainty and priors are documented clearly.

A neural network is not the first numerical-depth method.

Every candidate must be compared with the median-depth and accepted relative-class baselines.

## Interval construction

The preferred first interval method is direct lower- and upper-quantile prediction.

A future method may estimate, for example, a lower and upper conditional quantile. The exact quantiles must be selected before holdout evaluation and documented in the experiment manifest.

Alternative interval methods may include:

- conformal intervals calculated without holdout contamination;
- bootstrap intervals using site-group resampling;
- Bayesian posterior intervals when the model and priors are justified.

Rules:

- the interval method must be fitted or calibrated using training/validation data only;
- reference-depth uncertainty must be preserved rather than treated as exact truth;
- interval widths must widen for weak support or higher uncertainty;
- intervals must be checked for empirical coverage on unseen physical sites;
- narrow intervals with poor coverage fail validation;
- very wide intervals must be reported honestly and may trigger `insufficient_data`.

## Best estimate

`estimated_depth_best_m` may be the conditional median or another preregistered central estimate.

It must not be presented without the lower and upper range.

It must not be rounded to a precision unsupported by calibration quality. Display rounding must be defined after observed error and reference uncertainty are known.

## Allowed feature families

Only versioned features approved by `docs/DEPTH_FEATURE_INVENTORY.md` may be considered.

Initial candidate families include:

- raw Sentinel-1 `VV_dB` and `VH_dB` summaries;
- incidence-angle and orbit-geometry controls;
- a small nonduplicative set of neutral SAR ratios or differences;
- Sentinel-2 surface and context bands or indices;
- canonical Landsat LST and clearly named thermal context features;
- DEM, slope, roughness, and terrain controls;
- valid-pixel, alignment, observation-count, and temporal-quality metadata;
- independently documented physical size, material, structure, soil, moisture, season, and terrain metadata.

Prohibited inputs include:

- classifier probability, class, or final finding summary;
- app-generated depth labels;
- target masks or connected components derived from the same decision pipeline;
- PCA outputs used to define the candidate;
- `NANO_Depth_Penetration` treated as metres or truth;
- `UGS_DeepStruct_RVI`, `UGS_BaseDeep`, or simulated geophysical names treated as measured depth;
- `REPORT_640`, `TGT_*`, `ARCH_TARGETS_*`, `AI_BEH_*`, secret, or AI tensor layers;
- unknown-provenance `depth_file` arrays;
- display-only normalized values when measured values are available.

## Confounder controls

The numerical method must not be released until it is tested for dependence on:

- target size;
- target family, material, or structure;
- soil and surface type;
- moisture and season;
- terrain slope and roughness;
- SAR incidence angle and orbit geometry;
- sensor resolution and resampling;
- observation count and temporal dispersion;
- valid-pixel and nodata coverage;
- site identity.

Required checks include:

1. performance by each sufficiently represented subgroup;
2. leave-one-site-group-out sensitivity;
3. feature ablation for major confounder families;
4. residual plots against confounders;
5. comparison of results with and without physical metadata;
6. detection of site memorization or near-duplicate leakage.

Large unstable shifts block release or require abstention for the affected group.

## Out-of-distribution and support checks

The model must know when a candidate is unlike its calibration data.

Potential support checks include:

- range checks for every required feature;
- multivariate distance from the training distribution;
- unsupported categorical metadata values;
- depth extrapolation beyond the calibrated depth range;
- missing sensor families;
- poor valid-pixel coverage;
- acquisition geometry outside the supported envelope;
- terrain, soil, moisture, season, target family, or size outside supported coverage.

A failed support check must return:

```text
depth_status = insufficient_data
```

The model must not clamp an unsupported candidate to the nearest numerical depth and present it as valid.

## Metrics

Report at minimum:

- median absolute error;
- mean absolute error;
- root mean squared error as a secondary metric;
- signed bias;
- interval coverage;
- median and mean interval width;
- coverage-width trade-off;
- percentage within agreed metre tolerances, chosen before holdout evaluation;
- performance by physical site;
- performance by depth band;
- performance by finding family, target size, soil/surface, moisture/season, and terrain when counts permit;
- abstention rate;
- coverage among non-abstained cases;
- repeated-run stability for deterministic inputs.

A single overall error number is not sufficient.

## Acceptance criteria

Numerical thresholds must not be invented before the dataset distribution, uncertainty, depth range, and supported use are known.

Phase 4 may pass only when:

1. the model beats median-depth and relative-class midpoint baselines on untouched physical sites;
2. interval coverage meets a preregistered target without unusably wide intervals;
3. error and bias are acceptable across supported depth bands and major groups;
4. performance is not driven by one site, soil, season, target family, or target size;
5. unsupported and out-of-distribution cases abstain reliably;
6. results remain stable under reasonable preprocessing, split, and feature-ablation checks;
7. reference-depth uncertainty is included in interpretation;
8. the exact dataset, feature manifest, split policy, preprocessing pipeline, model, interval method, and thresholds are versioned;
9. no app-generated label or downstream target decision is used as calibration truth;
10. user-facing wording reports a range, quality, and uncertainty reason without claiming physical confirmation.

Failure of any critical gate keeps numerical depth disabled.

## Required private experiment artifacts

A future experiment should produce locally outside Git:

```text
numerical_depth_experiment_manifest.json
numerical_depth_metrics.json
numerical_depth_predictions_holdout.csv
numerical_depth_intervals_holdout.csv
numerical_depth_abstentions.csv
numerical_depth_group_metrics.csv
numerical_depth_feature_manifest.json
numerical_depth_model_manifest.json
numerical_depth_support_manifest.json
NUMERICAL_DEPTH_RESEARCH_REPORT.md
```

Files containing source references, site identifiers, coordinates, feature rows, predictions, or model artifacts remain in private local storage.

Only a redacted methodology and aggregate evaluation report may later be committed.

## Stop conditions

Stop and do not progress when:

- the relative-depth baseline has not passed;
- known-depth records are missing or too few for physical-site holdout evaluation;
- the supported depth range cannot be defined from real records;
- active splits share a `group_id` or related site family;
- reference uncertainty is missing or incompatible;
- depth labels are generated from notebook or app outputs;
- the holdout influenced feature, model, interval, or threshold selection;
- simple baselines perform equally well or better;
- interval coverage is poor;
- intervals are too wide to provide useful information;
- subgroup performance collapses;
- unsupported cases receive confident numerical ranges;
- a proxy ratio is converted directly into metres.

## App boundary

This specification adds no backend stage, API field, frontend field, downloadable output, model dependency, or numerical depth estimate.

Until a future Phase 4 experiment passes all gates, the app remains:

```text
depth_status = not_available
```

## Phase 4 decision

```text
Numerical-range design: complete
Supported metre range: blocked pending real known-depth distribution
Model fitting: blocked pending Phase 3 success and valid calibration records
Interval calibration: blocked
Physical-site holdout evaluation: blocked
Numerical app output: not approved
Backend implementation: blocked
```
