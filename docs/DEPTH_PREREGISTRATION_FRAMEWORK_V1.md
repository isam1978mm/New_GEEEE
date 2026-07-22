# Depth Scientific Validation Preregistration Framework — v1

Status: `framework_frozen_threshold_values_pending`.

This document freezes the decision process for future private-local depth research. It does not open the holdout, fit a model, validate depth, or enable an app result.

## Current gate

```text
calibration_pack = not_contract_ready
feature_manifest = not_frozen
training_started = false
holdout_opened = false
scientific_validation_run = false
relative_depth_approved = false
numerical_depth_approved = false
app_depth_enabled = false
```

The holdout must remain closed until every required value in the final freeze record is complete and versioned.

## Scope

The framework covers two separate experiments:

1. relative depth classes: `shallow`, `medium`, `deep`;
2. numerical depth ranges with calibrated uncertainty.

Passing the relative experiment does not approve metre output. Numerical work may start only after the relative gate passes and a support range is justified.

## Dataset and split freeze

Before any model fitting, record privately:

- dataset ID and version;
- calibration-record hash;
- source-index hash;
- exclusions hash;
- feature-manifest hash;
- split-policy version and seed;
- train, validation, and holdout group counts;
- positive and confirmed-negative counts by split;
- supported finding families and context groups;
- the exact definition of depth to top;
- reference-uncertainty policy.

One physical site or leakage group must remain in one split. The current unknown research site is excluded from fitting and threshold selection.

## Holdout prohibition

The untouched holdout must not influence:

- relative-class boundaries;
- feature selection;
- preprocessing or imputation;
- support envelopes;
- model family or hyperparameters;
- abstention thresholds;
- interval construction;
- rounding precision;
- acceptance thresholds;
- subgroup definitions.

Opening the holdout before the final freeze record exists invalidates the run.

## Relative-depth experiment

### Primary metrics

- balanced accuracy;
- macro F1;
- shallow-versus-deep confusion rate;
- abstention rate;
- non-abstained coverage.

### Required secondary reporting

- per-class precision and recall;
- one-class-off and two-class-off error rates;
- confusion matrix;
- site-level results;
- subgroup results where minimum counts permit;
- repeated-run stability;
- support and refusal counts.

### Frozen comparisons

The accepted method must be compared with:

1. majority-class baseline;
2. stratified-random baseline using training prevalence and a frozen seed;
3. one-feature threshold baseline selected without holdout access;
4. confounder-only baseline.

### Acceptance structure

Before holdout use, the final freeze record must set numeric values for:

- minimum balanced-accuracy improvement over every simple baseline;
- minimum macro-F1 improvement over every simple baseline;
- maximum shallow-versus-deep confusion rate;
- minimum non-abstained coverage;
- maximum tolerated performance drop for any supported major subgroup;
- deterministic repeat tolerance;
- minimum supported sample and group counts.

Those values may be chosen only from dataset-size analysis, reference uncertainty, training results, and validation results. They must not be back-filled after viewing holdout results.

Relative depth passes only when the frozen accepted method meets every frozen rule on unseen holdout sites and does not depend on one site or confounder group.

## Numerical-depth experiment

### Entry condition

Relative depth has passed, the numerical support range is justified, and the numerical feature and interval method are frozen.

### Primary metrics

- median absolute error;
- mean absolute error;
- signed bias;
- interval coverage;
- median interval width.

### Required secondary reporting

- RMSE;
- mean interval width;
- coverage-width trade-off;
- percentage within each frozen metre tolerance;
- site-level and depth-band results;
- subgroup results where supported;
- abstention rate and non-abstained coverage.

### Frozen comparisons

The proposed method must be compared with:

1. median training-depth baseline;
2. relative-class midpoint baseline.

### Acceptance structure

Before numerical holdout use, the final freeze record must set numeric values for:

- maximum median and mean absolute error;
- maximum absolute signed bias;
- minimum interval coverage;
- maximum acceptable median and mean interval width;
- required success percentages for frozen metre tolerances;
- minimum non-abstained coverage;
- subgroup and support requirements;
- refusal rules for unsupported conditions.

Narrow intervals with poor coverage fail. Unusably wide intervals fail or trigger refusal. A single exact depth without an interval is prohibited.

## Confounder and support checks

Both experiments require:

- confounder-only comparison;
- sensor-only versus sensor-plus-controls comparison;
- feature-family ablation;
- leave-one-site-group-out sensitivity;
- residual checks against size, soil, moisture, season, terrain, incidence angle, resolution, and observation quality;
- out-of-support refusal tests;
- coordinate, site-identity, and group leakage checks.

## Abstention and refusal

Unsupported cases must return no depth result. Abstention thresholds are selected using training and validation only. The holdout may measure abstention behavior but may not tune it.

## Final freeze record

Before opening the holdout, create a private immutable record containing:

```text
preregistration_version
experiment_mode
frozen_at
repository_commit
private_dataset_manifest_hash
feature_manifest_hash
split_policy_version
split_seed
relative_class_boundaries_m
model_candidates
selected_model_rule
preprocessing_definition
support_definition
abstention_rule
baseline_definitions
primary_metrics
numeric_acceptance_thresholds
subgroup_minimum_counts
holdout_access_authorization
```

Any missing field keeps `holdout_opened=false`.

## Amendment policy

Before holdout access, an amendment is allowed only when it is versioned with a reason and a diff. After holdout access, no change may rescue a failed result. A revised method requires a new untouched holdout or an explicitly labelled exploratory study.

## Output boundary

Repository synthetic-fixture results prove software behavior only. Private physical-site results remain outside Git. Until all applicable scientific and release gates pass:

```text
depth_mode = off
visible_depth_result = not_available
```
