# Depth Calibration Dataset Contract

Status: Phase 2 design artifact. No calibration records were found in the repository, no dataset has been populated, and no depth model is approved by this document.

## Purpose

This contract defines the minimum evidence, schema, storage, split, quality, and provenance requirements for a future depth-calibration dataset.

The dataset will support research into depth to the **top of a reference feature**. It must not be populated from notebook predictions, classifier results, target masks, PCA outputs, generated depth labels, or visual guesses from the same app signals.

Numerical depth in metres remains unavailable until a populated dataset passes this contract and later held-out validation.

## Current repository finding

A focused repository search found no traceable records containing known physical depth, known-depth site identifiers, excavation or engineering depth references, borehole records, or an existing depth calibration dataset.

The only current depth-related values are signal proxies, heuristic labels, visualization fields, or unknown-provenance notebook references. They cannot serve as calibration truth.

Therefore:

```text
depth_dataset_status = not_populated
training_status = blocked_missing_independent_known_depth_records
numerical_depth_status = not_available
```

## Definition of one calibration example

One calibration example represents one physical reference feature or one independently confirmed no-target/background case at one physical site.

Repeated observations of the same physical feature are linked through the same `site_id`, `feature_id`, and `group_id`. They must never be split across training, validation, and holdout sets.

The primary target is:

```text
known_depth_top_m
```

`known_depth_bottom_m` may be included when independently documented. It is not required for the first relative-depth research baseline.

## Required record schema

```text
schema_version
record_id
site_id
feature_id
group_id
reference_status
finding_family
known_depth_top_m
known_depth_bottom_m
depth_reference_uncertainty_m
depth_reference_method
evidence_source_type
evidence_source_reference
evidence_source_version
evidence_review_method
label_quality
target_size_length_m
target_size_width_m
target_size_height_m
target_material_or_structure
soil_or_surface_type
moisture_or_season
terrain_class
observation_start
observation_end
sensor_sources
sensor_acquisition_ids
pipeline_commit
feature_manifest_version
split
split_policy_version
include_for_relative_depth
include_for_numerical_depth
exclusion_reason
quality_notes
created_at
reviewed_at
reviewer_reference
```

## Field rules

### Identifiers

- `record_id` must be unique and stable.
- `site_id` identifies one physical site.
- `feature_id` identifies one physical reference feature within a site.
- `group_id` must group all records capable of leaking information about the same physical feature or local site.
- Identifiers must not encode raw coordinates.

### Reference status

Allowed values:

```text
known_depth_positive
confirmed_no_target
uncertain_reference
excluded
```

For `known_depth_positive`:

- `known_depth_top_m` is required.
- The value must be finite and greater than or equal to zero.
- `known_depth_bottom_m`, when present, must be greater than or equal to `known_depth_top_m`.
- `depth_reference_uncertainty_m` is required unless the source explicitly provides a bounded interval.

For `confirmed_no_target`:

- depth fields must remain empty.
- the independent source must establish that the case is a valid negative/background example.

`uncertain_reference` records may be retained for audit but cannot be used for model fitting or threshold selection.

### Depth reference method

Allowed examples include:

```text
controlled_test_site_measurement
engineering_record
survey_or_excavation_record
authoritative_external_dataset
documented_geophysical_or_construction_record
expert_adjudication_with_independent_evidence
```

The method must describe how physical depth was established. The method cannot be an app prediction, a notebook heuristic, or a visual interpretation of the same satellite features used as model inputs.

## Independent evidence policy

A record may count as calibration truth only when the depth evidence is independent of the feature pipeline being evaluated.

Allowed evidence sources may include:

- controlled lawful test sites with measured placement depth;
- engineering or construction records with documented depth;
- authoritative external benchmark datasets;
- documented survey or excavation records;
- independently produced reference labels with a traceable source and method;
- expert adjudication using evidence not available to the app pipeline.

Not sufficient by itself:

- `NANO_Depth_Penetration` or another depth-named proxy;
- classifier probability, class, or final finding summary;
- PCA anomaly values;
- target masks or connected-component outputs;
- `REPORT_640`, `TGT_*`, `ARCH_TARGETS_*`, `AI_BEH_*`, secret, or AI tensor layers;
- `UGS_DeepStruct_RVI`, `UGS_BaseDeep`, or simulated geophysical layers;
- cell 214 `depth_file` without recovered provenance;
- a person agreeing with a notebook or app result without independent evidence;
- estimated depth inferred only from the same Sentinel-1, Sentinel-2, Landsat, or DEM inputs being evaluated.

Every usable record must include `evidence_source_reference`, `evidence_source_type`, `evidence_source_version`, and `evidence_review_method`.

## Label quality levels

Allowed values:

```text
measured_independent
reviewed_independent
reviewed_adjudicated
weak_or_proxy
uncertain
excluded
```

Only `measured_independent`, `reviewed_independent`, and `reviewed_adjudicated` may enter a future calibration fit.

`weak_or_proxy` records may be used only for exploratory analysis clearly separated from calibration truth.

## Inclusion rules

A positive reference record is eligible only when:

1. the physical feature and its depth reference are traceable;
2. the depth definition is depth to the top of the feature;
3. the site and feature grouping are known;
4. required sensor observations can be matched to the reference case;
5. soil/surface, season/moisture, terrain, and target-size metadata are present or explicitly marked unknown;
6. the source date and observation dates are recorded;
7. the feature manifest excludes circular and target-derived layers;
8. the record passes independent review;
9. the record is not a near duplicate of a record in another split.

## Exclusion rules

Exclude from fitting when any of the following applies:

- physical depth is guessed, inferred, rounded without source support, or missing;
- the source cannot be identified or reviewed;
- the reference feature cannot be matched reliably to the sensor observation;
- site grouping is unknown and leakage cannot be prevented;
- the record is based only on an app or notebook output;
- depth units or vertical datum are ambiguous;
- depth refers to centre, bottom, or total extent without a top-depth conversion supported by the source;
- the feature changed, was removed, or was disturbed before the observation and this cannot be resolved;
- sensor coverage fails the quality gates;
- the case is outside the supported finding family or eventual calibrated depth range.

Excluded records remain in an exclusion ledger with a reason; they are not silently deleted.

## Negative and background cases

The dataset must include independently supported negative/background records.

Useful negative families include:

- confirmed no-target test areas;
- visually similar surface features;
- different soil, terrain, vegetation, and moisture conditions;
- urban or infrastructure features likely to produce radar contrast;
- cloud, shadow, nodata, layover, and sensor-edge cases;
- earlier heuristic false positives when an independent source confirms the negative status.

A heuristic false positive is not a confirmed negative until independent evidence establishes that status.

## Sensor and feature linkage

Each record must link to a versioned feature manifest derived from `docs/DEPTH_FEATURE_INVENTORY.md`.

Initial allowed research families are:

- raw Sentinel-1 `VV_dB` and `VH_dB`;
- Sentinel-1 incidence angle as a control;
- a small nonduplicative set of neutral SAR ratios or differences;
- core Sentinel-2 bands or indices as independent surface/context evidence;
- canonical Landsat LST and clearly named thermal context features;
- DEM and terrain derivatives as confounder controls;
- valid-pixel, acquisition, alignment, and observation-quality metadata.

Duplicate algebraic transforms must not be counted as independent evidence.

Classifier outputs, PCA scores, target masks, report layers, generated labels, and display-only normalization are prohibited from the calibration feature manifest.

## Relative-depth labels

Relative labels must not be manually invented before inspecting the supported known-depth distribution.

After a sufficient known-depth dataset exists, category boundaries may be derived and versioned as:

```text
shallow
medium
deep
```

Rules:

- boundaries must be recorded in metres in the dataset manifest;
- boundaries must be selected using training data only;
- holdout labels must be generated using frozen boundaries;
- class prevalence must be reported for every split;
- categories must represent depth to the top of the feature;
- category output remains experimental until held-out validation passes.

## Split policy

Required split unit:

```text
group_id, representing the physical site/feature family across all dates
```

Rules:

1. All observations of one physical feature remain in one split.
2. Nearby or related features from the same controlled site should remain in one split unless independence is documented.
3. The same site observed on multiple dates cannot cross splits.
4. A final physical-site holdout must remain untouched.
5. Thresholds, feature selection, normalization choices, category boundaries, and model selection use training/validation data only.
6. The holdout must not be used for manual cherry-picking or calibration tuning.
7. Split generation must be deterministic and record `split_policy_version` and seed when a seed is used.
8. A temporal holdout should be added when the dataset contains sufficiently separated observation periods.

Allowed split labels:

```text
train
validation
holdout
excluded
```

## Dataset package

A populated private dataset pack should contain:

```text
calibration_records.csv
calibration_manifest.json
feature_manifest.json
source_index.csv
exclusions.csv
DATASET_CARD.md
```

Optional evidence documents remain in a separate private evidence directory and are referenced by stable identifiers rather than copied into git.

## Calibration manifest requirements

```text
dataset_id
schema_version
created_at
updated_at
build_commit
build_procedure
record_count
positive_count
negative_count
excluded_count
label_quality_counts
evidence_source_counts
finding_family_counts
soil_surface_counts
season_moisture_counts
terrain_counts
depth_min_m
depth_max_m
depth_uncertainty_summary
split_policy_version
split_counts
site_counts_by_split
feature_manifest_version
data_source_list
content_hash
manifest_hash
storage_location_reference
artifact_class
filesystem_only
http_servable
frontend_visible
downloadable_via_api
redaction_policy
known_limitations
```

The manifest must verify that no `site_id`, `feature_id`, or `group_id` appears in more than one active split.

## Storage and privacy

The populated dataset, source documents, coordinate-bearing metadata, chips, arrays, and evidence must stay outside git under an owner-controlled private dataset root.

Required storage classification:

```text
artifact_class = LOCAL_SENSITIVE or FILESYSTEM_ONLY
filesystem_only = true
http_servable = false
frontend_visible = false
downloadable_via_api = false
```

Only this empty schema and policy document may be committed to the repository.

Exact coordinates, geometry, source-document paths, private identifiers, and coordinate proxies must not be written into repository documentation or normal logs.

## Hashing and versioning

- Dataset IDs and schema versions are immutable once used for an evaluation.
- Any record change creates a new dataset version.
- The manifest must include a deterministic content hash over the canonical record and source-index files.
- Feature values must record the pipeline commit and feature-manifest version.
- Evidence-source revisions must be recorded rather than overwritten silently.
- Calibration and holdout evaluation must name the exact dataset version.

## Dataset QA checklist

Before any relative-depth fitting:

- [ ] At least one lawful, traceable independent known-depth source has been identified.
- [ ] Positive known-depth records exist.
- [ ] Confirmed negative/background records exist.
- [ ] Every usable record has independent evidence metadata.
- [ ] Depth-to-top definition is consistent.
- [ ] Units and uncertainty are documented.
- [ ] Site and feature grouping prevents leakage.
- [ ] Train, validation, and untouched holdout sites are separated.
- [ ] Sensor observations and preprocessing versions are traceable.
- [ ] Soil/surface, moisture/season, terrain, target size, and finding family are recorded.
- [ ] Circular and target-derived features are excluded.
- [ ] Feature normalization is fit on training data only.
- [ ] Dataset and manifest hashes are recorded.
- [ ] Storage remains private and outside git.
- [ ] Limitations and missing coverage are documented.

Before numerical metre-range research, the relative-depth baseline must first beat preregistered baselines on held-out physical sites with acceptable stability and abstention behavior.

## Readiness decision

Current decision:

```text
Phase 2 schema: defined
Phase 2 records: absent
Calibration dataset: not ready
Relative-depth fitting: blocked
Numerical depth fitting: blocked
App implementation: blocked
```

The next valid action is to collect or identify lawful, documented, independently measured known-depth reference cases and enter them into a private dataset pack that follows this contract.

No model, backend stage, frontend field, relative-depth output, or numerical depth output is approved by this document.
