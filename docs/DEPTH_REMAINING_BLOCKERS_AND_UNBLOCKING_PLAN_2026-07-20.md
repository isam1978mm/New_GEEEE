# Remaining Depth Blockers and Unblocking Plan — 2026-07-20

Status: authoritative blocker note for the private local depth-research workflow.

This document records what is now verified, what remains blocked, and the evidence required to unblock each item. It must be read together with:

- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
- `docs/DEPTH_VALIDATION_GATES_SPEC.md`
- `docs/DEPTH_MATCHED_S1_ANGLE_SEASON_ADJUSTED_RESULT_2026-07-20.md`

## Current verified position

The private matched Sentinel-1 workflow completed with:

```text
input rows = 162
excluded zero-valid-pixel rows = 1
usable pre rows = 80
usable post rows = 81
usable total rows = 161
```

After incidence-angle control, month-of-year seasonal control, month-stratified permutation testing, and Holm correction:

```text
supported adjusted radar shifts = 3 of 4 tested signal features
```

This is evidence of an unexplained site-specific radar change relative to the reviewed background.

It is not evidence of:

- a specific physical cause;
- a buried object;
- target material or structure;
- physical depth;
- a confirmation percentage;
- scientific validation of notebook labels;
- readiness to enable app depth output.

The current app boundary remains:

```text
app_depth_enabled = false
app_depth_output = not_available
```

## Plain-English blocker summary

The software can now extract and compare the available radar data. The remaining blockers are not solved by rerunning the same satellite analysis.

The project is blocked by missing independent physical evidence and missing known-depth calibration data.

## Blocker 1 — Cause of the current radar change is unknown

### Current state

Three radar-feature shifts remain after the implemented angle and seasonal controls. Those controls reduce two important explanations, but they do not identify what physically caused the remaining difference.

### Evidence required to unblock cause attribution

At least one independent source that does not reuse the same satellite signals, such as:

- traceable engineering, construction, utility, survey, or archaeological records;
- a professionally conducted ground-penetrating-radar survey;
- a professionally conducted magnetometer or electromagnetic survey;
- another independently documented physical-site investigation.

No excavation is required merely to begin independent verification.

### Pass condition

The evidence must be traceable, reviewable, spatially matchable to the private site, and strong enough to support a specific physical interpretation.

### Prohibited shortcuts

Do not identify the cause using only:

- the current Sentinel-1 shifts;
- notebook labels or depth-named proxies;
- classifier classes or probabilities;
- PCA or anomaly scores;
- visual agreement with the app result;
- an invented confirmation percentage.

## Blocker 2 — Relative-depth research is blocked by missing known-depth calibration records

### Current state

The repository contains no populated, independently sourced known-depth calibration dataset. The current unknown site cannot teach the system its own depth.

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
training_status = blocked_missing_independent_known_depth_records
```

### Evidence required to unblock relative-depth research

Build a private calibration pack containing multiple physical sites and including:

- `known_depth_positive` records with traceable depth to the top of the feature;
- independently supported `confirmed_no_target` records;
- source method and uncertainty for every depth reference;
- target size, material or structure, soil or surface, season or moisture, and terrain metadata;
- matched sensor-acquisition references;
- stable `site_id`, `feature_id`, and `group_id` values;
- a frozen neutral feature manifest;
- explicit inclusion and exclusion decisions.

The current unknown research site must not be labeled from its app or notebook output and used as calibration truth.

### Split rule

Split by whole physical site or leakage group:

```text
training sites
validation sites
untouched holdout sites
```

Repeated observations, nearby linked features, or records from the same physical site must remain in one split.

### Pass condition

The private pack passes the dataset contract and contains eligible positive and negative records in every required split, including unseen physical sites in holdout.

### Prohibited shortcuts

Do not:

- invent shallow, medium, or deep labels from the current signals;
- use notebook predictions as known depth;
- split images from one site across train, validation, and holdout;
- treat an unverified background as a confirmed negative;
- train while the holdout is empty or research-ineligible.

## Blocker 3 — Numerical depth and confidence are blocked by missing held-out scientific validation

### Current state

No numerical depth model has been fitted or scientifically validated.

```text
numerical_depth_model_status = not_fitted
scientific_validation_status = not_run
numerical_depth_status = not_available
```

### Evidence required to unblock numerical ranges

After the calibration pack exists:

1. freeze the feature set and preprocessing;
2. fit only on training sites;
3. select thresholds and model choices only with training and validation sites;
4. evaluate once on untouched holdout sites;
5. compare against simple frozen baselines;
6. test confounders and unsupported-condition abstention;
7. report depth error, bias, interval coverage, interval width, and subgroup performance.

### Pass condition

A numerical method must beat the frozen baselines on unseen physical sites, provide honest uncertainty intervals, meet preregistered acceptance thresholds, and abstain outside supported conditions.

### Confidence rule

No confidence or confirmation percentage is allowed until held-out results establish how often the method is correct and how well its uncertainty is calibrated.

A model score by itself is not a validated confidence percentage.

## Blocker 4 — App depth output is blocked by implementation and release gates

### Current state

Exploratory research scripts exist, but the normal application depth stage remains unavailable.

### Requirements to unblock app depth

Only after the evidence blockers above are passed:

- implement the frozen depth stage and schemas;
- package the approved model and support matrix locally;
- add unit and integration tests for refusal, abstention, privacy, and compatibility;
- prove that depth does not alter existing classifier or legacy artifacts;
- enforce private filesystem-only detailed artifacts;
- pass relative or numerical scientific-validation gates for the requested mode;
- pass release validation for the private local workflow.

### Pass condition

The applicable contract, software, scientific, support, privacy, wording, and legacy-compatibility gates all pass.

Until then:

```text
depth mode = off
visible depth result = not_available
```

## Finite execution sequence

The remaining work should proceed in this order:

1. Keep the current site as an unknown research case.
2. Seek independent evidence if cause attribution for the current anomaly is required.
3. Acquire private known-depth positive and confirmed-negative records from several physical sites.
4. Validate the calibration pack for provenance, eligibility, privacy, and site-group splits.
5. Extract the frozen neutral feature set for eligible calibration records.
6. Fit and validate a relative-depth research baseline.
7. Test on untouched holdout sites and run confounder/support checks.
8. Consider numerical depth ranges only if relative-depth evidence succeeds.
9. Implement and release app depth only after all applicable gates pass.

## What is not a blocker anymore

The following items are complete for the current exploratory site-background screen:

- Sentinel-1 coverage qualification;
- reviewed background selection;
- exact acquisition matching;
- private matched feature extraction;
- zero-valid-row classification and honest exclusion;
- descriptive site-background comparison;
- incidence-angle and seasonal controlled screen;
- focused software verification for the adjusted screen.

Repeating those completed steps will not create ground truth or unblock depth.

## Current decision

```text
current_site_status = unexplained_radar_anomaly_research_case
cause_attribution = blocked_missing_independent_physical_evidence
relative_depth = blocked_missing_known_depth_calibration_pack
numerical_depth = blocked_missing_model_and_holdout_validation
confidence_percentage = blocked_missing_calibration_and_holdout_evidence
app_depth_enabled = false
```
