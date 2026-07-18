# Public Depth-Calibration Evidence Search — 2026-07-18

Status: first online evidence-screening pass complete. No public dataset found in this pass satisfies the full app requirement of real benign buried features, independently documented depth, Sentinel-1-compatible observations, and enough group-separated sites for train/validation/holdout.

This document does not approve a depth model or enable app depth output.

## Screening criteria

A candidate is potentially usable only when it provides:

1. benign physical reference features;
2. independently documented or simulated depth labels with known provenance;
3. enough metadata to separate physical groups;
4. sensor and preprocessing information;
5. a usable licence;
6. no app-generated or notebook-generated labels;
7. no requirement to expose private coordinates or local paths in Git.

For direct scientific calibration of this app, the candidate must also support comparison with the approved Sentinel-1/Sentinel-2/Landsat/terrain feature inventory. GPR-only or simulated datasets can support method development but cannot by themselves prove Sentinel-1 buried-feature depth estimation.

## Candidate shortlist

### A. Guangzhou University GPR Dataset

Source: Zenodo DOI `10.5281/zenodo.14637589`

What it contains:

- real-world GPR data;
- underground pipeline layouts at different depths;
- tunnel-lining and reinforced-concrete data;
- raw IDS GeoRadar `.dt` files;
- CC BY 4.0 licence;
- approximately 3.8 GB archive.

Current assessment:

```text
real_field_data = yes
benign_targets = yes
numeric_depth_labels_confirmed_from_public_metadata = not_yet
sentinel_1_observations_included = no
direct_app_calibration = not_approved
method_development_candidate = yes
```

Next check: inspect archive documentation for an explicit per-scan depth table, acquisition dates, site grouping, and non-sensitive georeferencing suitable for separate satellite feature extraction.

### B. Hacimusalar Geophysical Survey Dataset

Source: Mendeley Data DOI `10.17632/27wsdn3mc2.1`

What it contains:

- real field ERT, GPR, and magnetometry;
- a shallow buried ancient wall;
- integrated multi-sensor interpretation;
- CC BY 4.0 licence.

Current assessment:

```text
real_field_data = yes
benign_target = yes
numeric_depth_ground_truth_confirmed = not_yet
sentinel_1_observations_included = no
direct_app_calibration = not_approved
method_development_candidate = possible
```

Risk: the related article and detailed reproduction notes were not yet available in the public metadata. The dataset must not be used as a known-depth label until excavation, engineering, or independently reviewed depth evidence is confirmed.

### C. Morocco Utilities and Voids GPR Dataset

Source: Mendeley Data DOI `10.17632/ww7fd9t325.1`; related open data article DOI `10.1016/j.dib.2025.111338`.

What it contains:

- 2,239 GPR images;
- buried utilities, voids, and intact zones;
- real infrastructure-project data collected from 2019 to 2024;
- 200 MHz and 400 MHz GPR;
- CC BY 4.0 licence.

Current assessment:

```text
real_field_data = yes
benign_targets = yes
numeric_depth_labels_confirmed_from_public_metadata = no
sentinel_1_observations_included = no
direct_app_calibration = not_approved
classification_or_detection_benchmark = yes
```

This is useful for detection research, but the public description does not establish independently documented numerical depths for each image.

### D. MERL-GPR

Source: Zenodo DOI `10.5281/zenodo.8145084`

What it contains:

- 400 simulated two-dimensional underground structures;
- exact generated layer-depth parameters;
- two embedded cylinders in simulated ground;
- gprMax-based electromagnetic simulation;
- CC BY-SA 4.0 licence.

Current assessment:

```text
real_field_data = no
exact_depth_parameters = yes
sentinel_1_observations_included = no
direct_scientific_calibration = prohibited
software_and_algorithm_testing = suitable
```

This can test parsers, feature-order handling, abstention, and synthetic baseline code. It cannot count as independent real calibration evidence.

### E. Ngozumpa Glacier Debris-Thickness GPR Dataset

Source: Zenodo DOI `10.5281/zenodo.1451560`

What it contains:

- field GPR transects;
- measured debris thickness;
- a known-depth calibration target used to estimate signal velocity;
- radar and supporting position data.

Current assessment:

```text
real_field_data = yes
independent_thickness_reference = yes
same_target_definition_as_app = no
sentinel_1_buried_feature_calibration = no
method_sanity_check = possible
```

This is not a buried-structure dataset. It may help test depth-reference provenance and uncertainty handling, but not the app's target claim.

### F. Sentinel-1 SnowEx Depth Evaluation

Source: NASA SnowEx publication and open-source evaluation work.

What it contains:

- direct Sentinel-1 depth-retrieval evaluation;
- independent lidar snow-depth measurements;
- multiple sites and winters.

Current assessment:

```text
direct_sentinel_1 = yes
independent_depth_reference = yes
same_physical_problem = no
buried_feature_calibration = no
negative_or_limitations_benchmark = useful
```

The published evaluation found weak agreement for snow depth across the tested sites. This reinforces the need for independent holdout validation and prevents treating a radar ratio as a general depth meter.

## Sentinel-1 compatibility finding

Sentinel-1 provides C-band SAR backscatter with common land-product resolutions around 10–40 m. Public official documentation describes the products as calibrated backscatter imagery for land and maritime monitoring. The public calibration candidates found in this pass are mostly local GPR datasets at much finer spatial scale.

Therefore:

```text
direct_transfer_from_gpr_depth_to_sentinel_1 = not_valid
```

A real candidate would require either:

1. public benign sites with independently documented depths and enough spatial scale for Sentinel-1 pixels; or
2. public site metadata that permits extracting matched Sentinel-1 time series while preserving group separation and provenance.

## Decision

No candidate is approved yet for direct app calibration.

Recommended next action:

1. inspect the Guangzhou archive documentation for explicit pipeline depth tables and acquisition/site metadata;
2. inspect the Hacimusalar files for independent depth evidence;
3. inspect the Morocco dataset labels to determine whether any numerical depths exist;
4. keep MERL-GPR as synthetic software-test material only;
5. use SnowEx only as a methodological warning and validation example, not as buried-feature calibration.

## Checklist

- [x] Search public institutional repositories.
- [x] Exclude app/notebook-generated labels.
- [x] Separate real, simulated, and wrong-phenomenon datasets.
- [x] Record licensing and sensor mismatch.
- [x] Identify three real benign field-data leads.
- [ ] Inspect candidate archives for per-record numerical depth labels.
- [ ] Confirm acquisition dates and physical grouping.
- [ ] Determine whether matched Sentinel-1 extraction is possible.
- [ ] Add only verified candidates to the private source index.
- [ ] Keep app depth output `not_available` until scientific gates pass.
