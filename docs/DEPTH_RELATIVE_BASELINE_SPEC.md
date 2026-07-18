# Relative-Depth Baseline Specification

Status: Phase 3 design artifact only. No model has been fitted, no category boundaries have been selected, and no depth result is approved for app output.

## Purpose

This document defines how the first relative-depth experiment will be run after a valid private calibration dataset exists.

The first experiment asks only:

> Can approved sensor and context features distinguish broad depth-to-top categories on physical sites that were not used for fitting?

It does not estimate metres and does not change the current app output.

## Current gate

```text
calibration_dataset_status = not_populated
known_depth_rows = 0
phase_3_design_status = defined
phase_3_fitting_status = blocked
app_depth_output = depth_not_available
```

Phase 3 fitting must not start until `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md` passes its readiness checklist.

## Target definition

The target remains depth to the top of the independently documented reference feature:

```text
known_depth_top_m
```

Relative classes will eventually be:

```text
shallow
medium
deep
```

These names are experimental research labels, not physical measurements.

## Category-boundary rule

No metre boundaries are chosen in this document because no known-depth distribution is available.

After valid training records exist:

1. inspect only the training split depth distribution;
2. select two boundaries that create useful, sufficiently represented categories;
3. record the exact metre boundaries and rationale in the dataset manifest;
4. freeze the boundaries before validation and holdout evaluation;
5. apply the same frozen boundaries to validation and holdout records;
6. never adjust boundaries after seeing holdout results.

The boundaries must not be derived from notebook proxies, classifier scores, or the holdout set.

## Eligible records

A record may enter Phase 3 fitting only when:

- `reference_status=known_depth_positive`;
- `label_quality` is `measured_independent`, `reviewed_independent`, or `reviewed_adjudicated`;
- `known_depth_top_m` and its uncertainty are present;
- the sensor observation can be matched to the reference case;
- `group_id` is available;
- the record passes the calibration-contract inclusion rules;
- the feature manifest excludes circular and target-derived fields.

`confirmed_no_target` records are retained for abstention and false-positive analysis. They are not assigned an artificial depth class.

## Allowed first feature families

Only versioned features approved by `docs/DEPTH_FEATURE_INVENTORY.md` may be considered.

Initial candidate families:

- raw Sentinel-1 `VV_dB` and `VH_dB` summaries;
- incidence-angle controls;
- a small nonduplicative set of neutral SAR ratios or differences;
- Sentinel-2 surface/context bands or indices;
- canonical Landsat LST and clearly named thermal context features;
- DEM and terrain derivatives as confounder controls;
- valid-pixel, observation-count, acquisition, alignment, and temporal-quality metadata;
- independently defined physical target-size or structure metadata when documented by the reference source.

Prohibited inputs:

- classifier class, probability, or finding summary;
- `NANO_Depth_Penetration` treated as a depth label;
- PCA anomaly values used to define the target;
- target masks or connected-component decisions derived from the same pipeline;
- generated depth labels;
- `REPORT_640`, `TGT_*`, `ARCH_TARGETS_*`, `AI_BEH_*`, secret, or AI tensor layers;
- unknown-provenance `depth_file` arrays;
- display-only normalized values when the underlying measured value is available.

## Unit of analysis

The initial baseline should use one tabular row per independently documented physical reference feature, with sensor summaries computed over an independently defined reference footprint.

Repeated dates for the same physical feature may be aggregated into versioned temporal summaries or retained as linked observations, but all related rows must remain under one `group_id` and in one split.

## Split policy

The split unit is the physical site/feature group, not individual pixels or dates.

Required behavior:

- all records sharing a `group_id` remain in one split;
- related features from the same local test site remain together unless independence is documented;
- all dates for one site remain together;
- the final holdout contains physical sites unseen during fitting and threshold selection;
- preprocessing statistics are fitted on training data only;
- split rules and seeds are deterministic and versioned.

Allowed split labels:

```text
train
validation
holdout
excluded
```

## Baselines

Every model must be compared with:

1. majority-class prediction;
2. stratified random prediction using training prevalence;
3. a one-feature threshold rule selected on training data only.

A more complex model is useful only when it improves on these baselines on unseen physical sites.

## Model order

Run models in this order:

1. threshold/rule baseline;
2. ordinal logistic regression;
3. shallow decision tree with constrained depth and minimum leaf size;
4. calibrated gradient-boosted model only when simpler models fail and the dataset size supports it.

Do not introduce a neural network for this phase.

## Preprocessing rules

- Missing values are represented explicitly; they are not silently converted to zero.
- Imputation parameters are learned from the training split only.
- Scaling or normalization parameters are learned from the training split only.
- Highly duplicated algebraic transforms are removed before fitting.
- Feature selection uses training and validation data only.
- The full preprocessing pipeline is versioned with the model.
- Sensor resolution and resampling provenance remain available as metadata.

## Abstention rules

The baseline must return `insufficient_data` rather than a relative class when any required quality gate fails.

Initial abstention causes include:

- missing required sensor family;
- insufficient valid-pixel coverage;
- unsupported finding family;
- acquisition or alignment failure;
- incidence angle or terrain outside calibrated support;
- missing critical confounder metadata;
- feature values outside the training support envelope;
- class probabilities too uncertain under a threshold selected on validation data.

No abstention threshold may be tuned on the final holdout.

## Metrics

Report at minimum:

- balanced accuracy;
- macro F1;
- per-class precision and recall;
- ordinal one-class-off and two-class-off error rates;
- confusion matrix;
- abstention rate;
- coverage among non-abstained records;
- performance by physical site;
- performance by finding family, soil/surface type, season/moisture, terrain class, and depth category when sample counts permit;
- repeated-run stability for deterministic inputs.

Overall accuracy alone is not sufficient.

## Success criteria

Numerical thresholds cannot be fixed before dataset size, prevalence, and reference uncertainty are known.

Phase 3 may pass only when all of the following are true:

1. the model beats the majority, stratified-random, and one-feature rule baselines on untouched holdout sites;
2. improvement is not caused by one site, one target family, or one soil condition;
3. shallow-versus-deep confusion is acceptably rare under a preregistered criterion;
4. abstention behavior is documented and prevents unsupported predictions;
5. results remain stable across reasonable preprocessing and split checks;
6. no metre-accuracy claim is made;
7. the exact dataset, feature manifest, split policy, preprocessing pipeline, and model versions are recorded.

If these conditions fail, Phase 4 numerical depth-range work remains blocked.

## Required experiment artifacts

When a valid dataset exists, one private experiment run should produce:

```text
relative_depth_experiment_manifest.json
relative_depth_metrics.json
relative_depth_confusion_matrix.csv
relative_depth_predictions_holdout.csv
relative_depth_abstentions.csv
relative_depth_feature_manifest.json
relative_depth_model_manifest.json
RELATIVE_DEPTH_RESEARCH_REPORT.md
```

Files containing site identifiers, coordinates, source references, feature rows, predictions, or model artifacts remain in private local storage outside Git.

Only a redacted methodology and aggregate evaluation report may later be committed.

## Stop conditions

Stop the experiment and do not progress when:

- known-depth records are absent or too few for site-level splitting;
- any active split shares a `group_id` with another split;
- depth labels are generated from app outputs;
- holdout data influenced boundaries, features, thresholds, or model selection;
- reference uncertainty is missing or incompatible across records;
- the model does not beat simple baselines;
- performance collapses for a major site, target, soil, terrain, or season group;
- results require converting a proxy directly into metres.

## App boundary

This specification adds no backend stage, API field, frontend field, downloadable artifact, or numerical depth output.

Until Phase 3 is fitted and passes held-out validation, the app remains:

```text
depth_status = not_available
```

## Phase 3 decision

```text
Baseline design: complete
Category boundaries: blocked pending training-depth distribution
Model fitting: blocked pending valid calibration records
Holdout evaluation: blocked pending independent physical sites
Relative-depth app output: not approved
Numerical depth work: blocked
```
