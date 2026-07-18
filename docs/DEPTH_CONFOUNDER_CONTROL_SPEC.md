# Depth Confounder-Control Specification

Status: Phase 5 design artifact only. No confounder experiment has been run, no model has been approved, and no depth output is enabled by this document.

## Plain-English purpose

A future depth model could appear accurate for the wrong reason.

For example, it might learn that one test site has dry soil, that deeper examples happened in winter, or that large structures usually received one label. In that case, it would be predicting soil, season, site, or object size instead of depth.

This specification defines the checks required to detect that problem.

The core question is:

> Does the model still estimate depth when soil, moisture, season, terrain, target size, target type, radar angle, data quality, and physical site change?

If the answer is no, the affected case must be blocked or returned as `insufficient_data`.

## Current gate

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
numerical_depth_model_status = not_fitted
phase_5_design_status = defined
phase_5_testing_status = blocked
app_depth_output = depth_not_available
```

Phase 5 testing cannot start until real independently measured or independently documented known-depth records exist and the earlier model phases have produced a frozen candidate method.

## What is a confounder?

A confounder is a variable that changes alongside depth and can mislead the model into learning the wrong relationship.

Example:

```text
All shallow examples happen on flat dry ground.
All deep examples happen on steep wet ground.
```

A model could then predict `shallow` from dry flat ground and `deep` from wet steep ground, even if the radar signal contains no reliable depth information.

That would fail this specification.

## Required confounder families

Every future relative or numerical depth experiment must record and evaluate the following families when applicable.

### 1. Target size

Required fields may include:

```text
target_size_length_m
target_size_width_m
target_size_height_m
target_area_m2
size_source
size_uncertainty
```

Reason:

A larger structure may create a stronger signal than a smaller structure at the same depth. The model must not interpret signal strength caused by size as depth.

### 2. Target family, material, or structure

Required fields may include:

```text
finding_family
target_material_or_structure
structure_shape_family
structure_source
```

Reason:

Different materials and structures can react differently in radar, optical, and thermal data. A model trained on one family cannot automatically be trusted on another.

### 3. Soil and surface type

Required fields may include:

```text
soil_or_surface_type
surface_cover
soil_source
soil_quality
```

Reason:

Sand, clay, rock, pavement, vegetation, and disturbed soil may change the observed signal independently of depth.

### 4. Moisture and season

Required fields may include:

```text
moisture_or_season
observation_season
recent_precipitation_context
moisture_source
```

Reason:

Wet and dry conditions can change radar and thermal behavior. The model must not confuse moisture changes with depth changes.

### 5. Terrain

Required fields may include:

```text
terrain_class
slope_mean
slope_max
roughness_mean
aspect_summary
elevation_range
```

Reason:

Slope, roughness, shadow, layover, drainage, and elevation can affect sensor values without any change in physical depth.

### 6. SAR acquisition geometry

Required fields may include:

```text
incidence_angle_mean
incidence_angle_range
orbit_direction
relative_orbit
acquisition_geometry_version
```

Reason:

Radar values can change with incidence angle, orbit direction, and viewing geometry. These changes must not be mistaken for depth.

### 7. Sensor resolution and resampling

Required fields may include:

```text
native_resolution_m
working_grid_resolution_m
resampling_method
alignment_version
source_pixel_count
```

Reason:

A small target can appear different after resampling. The model must not learn processing artifacts as depth evidence.

### 8. Observation count and temporal spread

Required fields may include:

```text
observation_count
observation_start
observation_end
temporal_span_days
temporal_dispersion_summary
```

Reason:

A record built from many observations may be more stable than one built from a single acquisition. The model must not treat data quantity as depth.

### 9. Valid-pixel and nodata coverage

Required fields may include:

```text
valid_pixel_fraction
nodata_fraction
cloud_shadow_fraction
sar_quality_fraction
coverage_quality_class
```

Reason:

Poor coverage can create unstable summaries. Weak data should cause abstention, not a confident depth result.

### 10. Physical site identity

Required fields include:

```text
site_id
feature_id
group_id
```

Reason:

A model can memorize a site instead of learning a general relationship. All related observations must remain in one split, and performance must be tested on unseen physical sites.

## Required tests

### Test A — Group coverage table

Before fitting, produce a table showing counts by:

```text
depth category or depth band
site
finding family
target size band
soil or surface type
moisture or season
terrain class
orbit or incidence band
sensor-resolution group
```

The table must identify empty or severely underrepresented combinations.

A model must not claim support for groups that do not exist in the calibration data.

### Test B — Correlation and association scan

On the training split only, inspect whether depth is strongly associated with:

- one site;
- one soil type;
- one season;
- one target family;
- one target-size band;
- one incidence-angle band;
- one data-quality class.

Strong association is not automatic proof of failure, but it must be documented and tested before release.

### Test C — Single-family baselines

Fit simple baselines using only one confounder family at a time, such as:

```text
soil only
season only
target size only
site identity only
terrain only
incidence angle only
data quality only
```

If a confounder-only baseline performs as well as the proposed depth model, the proposed model has not demonstrated independent depth information.

### Test D — Feature-family ablation

Repeat evaluation after removing one feature family at a time.

Examples:

```text
remove target-size metadata
remove soil and surface metadata
remove moisture and season metadata
remove terrain controls
remove SAR geometry controls
remove thermal features
remove optical features
remove SAR-derived ratios
```

The purpose is to identify whether the model depends too heavily on one family.

Large unexplained performance changes must be investigated.

### Test E — Leave-one-site-group-out check

When dataset size permits, repeatedly hold out one physical site group and evaluate on it.

This tests whether performance survives when the model sees a truly new place.

If performance is strong only on sites already represented during fitting, the model is not site-independent.

### Test F — Subgroup evaluation

Report errors separately for every sufficiently represented group.

For relative depth:

- balanced accuracy;
- macro F1;
- per-class recall;
- shallow-versus-deep confusion;
- abstention rate.

For numerical depth:

- median absolute error;
- signed bias;
- interval coverage;
- interval width;
- abstention rate.

Groups with too few records must be marked `insufficient_sample`, not silently combined into a general claim.

### Test G — Residual checks

For a future numerical model, inspect prediction errors against:

```text
target size
soil or surface type
moisture or season
slope and roughness
incidence angle
resolution
observation count
valid-pixel fraction
site
known depth
```

A clear trend means the model may be systematically biased.

Example:

```text
error grows as slope increases
```

That may require a slope-specific abstention rule or may block use on steep terrain.

### Test H — Metadata removal comparison

Compare:

1. sensor features only;
2. sensor features plus confounder controls;
3. confounder metadata only.

Interpretation:

- If confounder-only performs strongly, the dataset may be biased.
- If adding controls improves stability, controls may be useful.
- If sensor-only collapses while metadata-only remains strong, the model may not contain meaningful depth signal.

### Test I — Matched or balanced comparisons

When enough records exist, compare cases with similar:

```text
target family
target size
soil
moisture or season
terrain
sensor geometry
```

but different known depths.

This is one of the clearest tests of whether the model can distinguish depth while other conditions remain similar.

### Test J — Out-of-support checks

For every candidate, determine whether its confounder values are represented in the training data.

Unsupported conditions may include:

- unseen soil or surface type;
- unseen target family;
- target much larger or smaller than calibration examples;
- incidence angle outside the trained range;
- terrain outside the trained range;
- season or moisture state absent from training;
- much poorer data coverage;
- sensor resolution or preprocessing version not represented.

A failed check must return:

```text
depth_status = insufficient_data
```

## Leakage prevention

The following are required:

1. All rows sharing a `group_id` remain in one split.
2. Related nearby features remain together unless physical independence is documented.
3. Repeated dates for one site remain together.
4. Preprocessing parameters are fitted using training data only.
5. Confounder thresholds and abstention rules are selected using training and validation data only.
6. The final physical-site holdout cannot influence feature selection, subgroup definitions, thresholds, or release decisions before final evaluation.
7. Site identifiers cannot be used as model input.
8. Coordinates and coordinate proxies cannot be used as model inputs.

## Required support matrix

Before release, create a support matrix such as:

```text
finding_family × depth_band
soil_type × depth_band
season_or_moisture × depth_band
terrain_class × depth_band
target_size_band × depth_band
incidence_band × depth_band
```

Each cell should record:

```text
record_count
site_count
usable_count
holdout_count
error_summary
abstention_rate
support_status
```

Allowed `support_status` values:

```text
supported
limited_support
unsupported
insufficient_sample
```

The model may only claim support for combinations that pass the agreed minimum coverage and stability requirements.

## Release behavior

A future model must not return a depth result solely because all technical fields exist.

It must also verify that the candidate is within supported conditions.

Possible outcomes:

```text
depth_status = relative_only
depth_status = calibrated_range
depth_status = validated_range
depth_status = insufficient_data
```

Examples of required warnings:

```text
Limited calibration for this soil type.
This target size is outside the main calibration range.
Radar viewing geometry differs from the calibration data.
Depth is unavailable because this terrain type is unsupported.
```

No unsupported case may receive a confident numerical range.

## Acceptance criteria

Phase 5 may pass only when:

1. confounder coverage is documented;
2. physical-site leakage is absent;
3. confounder-only baselines do not explain the claimed model performance;
4. matched or balanced comparisons provide evidence beyond simple dataset bias when data permits;
5. subgroup performance is reported honestly;
6. major groups do not show unacceptable error, bias, or interval failure;
7. unstable groups trigger abstention or remain unsupported;
8. out-of-support checks are implemented and validated;
9. performance is not driven by one site, target family, soil type, season, or size band;
10. the exact dataset, feature manifest, preprocessing, split, confounder policy, model, and thresholds are versioned.

Numerical acceptance thresholds must be chosen only after the real dataset distribution and uncertainty are inspected.

## Required private experiment artifacts

Future confounder testing should produce locally outside Git:

```text
confounder_coverage_table.csv
confounder_support_matrix.csv
confounder_single_family_baselines.json
confounder_ablation_results.json
confounder_subgroup_metrics.csv
confounder_residual_checks.csv
confounder_ood_rules.json
confounder_test_manifest.json
DEPTH_CONFOUNDER_REPORT.md
```

Files containing site identifiers, coordinates, source references, feature rows, predictions, or model artifacts remain private and local.

Only redacted methodology and aggregate findings may later be committed.

## Stop conditions

Stop and do not approve depth output when:

- known-depth records are absent;
- important depth bands occur only at one site;
- one soil, season, target family, or target size is tied almost completely to one depth class;
- train and holdout locations overlap;
- a confounder-only model performs as well as the depth model;
- subgroup errors are large or unstable;
- interval coverage fails for a major supported group;
- unsupported conditions receive confident output;
- the model depends on site identity or coordinate proxies;
- the model uses classifier outputs, target masks, generated depth labels, or other circular inputs.

## App boundary

This specification adds no backend stage, API field, frontend field, model, or depth result.

Until the calibration data, earlier model phases, and these confounder checks pass:

```text
depth_status = not_available
```

## Phase 5 checklist

- [x] Define confounder families.
- [x] Define leakage-prevention rules.
- [x] Define subgroup and ablation tests.
- [x] Define site-generalization checks.
- [x] Define out-of-support behavior.
- [x] Define private experiment artifacts.
- [ ] Populate real known-depth calibration records.
- [ ] Fit the Phase 3 relative-depth baseline.
- [ ] Validate the Phase 3 baseline on untouched sites.
- [ ] Fit a Phase 4 numerical range model, only if Phase 3 passes.
- [ ] Run the Phase 5 confounder tests.
- [ ] Approve supported groups and abstention rules.
- [ ] Implement any app depth output.

## Phase 5 decision

```text
Confounder-control design: complete
Confounder data coverage: unknown
Confounder testing: blocked
Site-generalization testing: blocked
Supported groups: not defined
App depth output: not approved
Backend implementation: blocked
```
