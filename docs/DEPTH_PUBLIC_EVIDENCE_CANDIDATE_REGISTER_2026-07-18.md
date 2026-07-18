# Depth Public Evidence Candidate Register — 2026-07-18

Status: active evidence acquisition. This register tracks public benign calibration candidates and the work required to convert them into independently traceable research records. It does not approve a model or enable app depth output.

## Screening states

```text
priority_1_verified_physical_depth = independently surveyed or installed depth is documented
priority_2_interpreted_depth = depth is reported by a geophysical interpretation but is not independently confirmed
method_only = useful for software or method research but not a real calibration label
rejected_for_depth = no usable numerical depth evidence
```

## Candidate P1 — TU1208 / IFSTTAR Nantes geophysical test site

Sources:

- article DOI `10.3390/rs10040530`
- raw supplementary archive DOI `10.5281/zenodo.1211173`

Verified source facts:

- full-size controlled geophysical test site;
- benign targets include pipes, artificial voids, masonry, rocks, cables, and other civil-engineering objects;
- targets were installed during construction and accurately geolocated with a theodolite;
- target depths were calculated from independently surveyed target and surface elevations, not estimated from the GPR response;
- multiple pipe layers occur at different depths and in different host materials;
- 67 GPR profiles were recorded along eleven parallel lines with several radar systems and antenna frequencies;
- raw files are publicly available under CC BY 4.0.

Current classification:

```text
physical_depth_provenance = independently_surveyed
real_field_data = yes
benign_targets = yes
raw_gpr_available = yes
multiple_depth_levels = yes
multiple_host_materials = yes
multiple_physical_sites = no_single_test_site
sentinel_1_included = no
direct_app_training_approval = pending_scale_and_feature_match
priority = 1
```

Required extraction work:

1. extract the numerical depth values shown in the test-site cross-section figures;
2. map each target or target layer to the corresponding radar profile and host-material region;
3. record whether the reported depth is depth-to-top, center depth, or another geometric reference;
4. assign one physical-site group to prevent line-level leakage across splits;
5. assess whether the 30 m by 5 m site and its closely spaced targets can produce any separable approved satellite feature window;
6. if satellite separation is impossible, retain this source for GPR method validation and uncertainty research only.

Important limitation:

The test site is one physical site with many closely spaced objects. Multiple radar profiles are not independent physical-site holdouts. The data must never be split by profile as though each line were a separate site.

## Candidate P2 — IAG/USP shallow geophysics controlled test site

Sources:

- depth study DOI `10.4236/ijg.2017.85040`
- controlled-site construction paper DOI `10.1590/S0102-261X2006000100004`

Verified source facts:

- controlled university test site with targets installed at known positions and depths;
- seven target lines contain benign archaeological, utility, concrete, drum, pipe, and cable analogues;
- published target depths span approximately 0.5 m to 2.5 m across the site;
- one published GPR depth study used precisely buried metallic drums at approximately 0.5 m to 2.0 m;
- the site is explicitly used to compare measured or installed depths with geophysical estimates.

Current classification:

```text
physical_depth_provenance = installed_known_depth
real_field_data = yes
benign_targets = yes
raw_public_dataset_confirmed = not_yet
multiple_depth_levels = yes
multiple_target_families = yes
multiple_physical_sites = no_single_test_site
sentinel_1_included = no
direct_app_training_approval = pending_data_access_and_scale_match
priority = 1
```

Required extraction work:

1. obtain the open paper tables containing actual target depths;
2. determine whether raw radargrams or machine-readable target maps are publicly downloadable;
3. extract target dimensions, depth-to-top definition, material, line, and host-soil context;
4. treat all seven lines as one physical-site group unless independent construction areas are documented;
5. assess satellite-pixel separability before creating any app calibration record.

## Candidate P3 — Guangzhou University GPR dataset

Source: DOI `10.5281/zenodo.14637589`

Verified source facts:

- real pipeline, tunnel-lining, and reinforced-concrete GPR data;
- public archive contains raw IDS and other radar formats;
- repository description states that pipeline layouts and depths vary;
- archive preview contains many raw scan files but no obvious README, CSV, spreadsheet, PDF, or per-scan depth table.

Current classification:

```text
physical_depth_provenance = not_yet_visible
real_field_data = yes
benign_targets = yes
raw_gpr_available = yes
numeric_per_scan_depth_table = not_found_in_archive_preview
sentinel_1_included = no
direct_app_training_approval = not_yet
priority = 2
```

Required extraction work:

1. inspect the complete archive for hidden metadata not shown by the previewer;
2. identify whether folder names, marker files, or project files encode known pipeline depths;
3. contact the dataset team for the pipeline layout and depth map if the archive lacks it;
4. obtain acquisition dates and grouping metadata;
5. reject depth labels that are derived only from the same GPR scans.

## Candidate P4 — Hacimusalar multi-method survey

Sources:

- dataset DOI `10.17632/27wsdn3mc2.1`
- 2024 conference publication DOI `10.3997/2214-4609.202420109`

Verified source facts:

- public real-field GPR, electrical-resistivity, and magnetometry data;
- the publication reports anomalies interpreted as wall remains at approximately 1.2 m below ground;
- the site and target are benign and the dataset is CC BY 4.0.

Current classification:

```text
reported_depth = approximately_1.2_m
physical_depth_provenance = geophysical_interpretation_not_independent
real_field_data = yes
multi_sensor_support = yes
independent_excavation_or_engineering_depth = not_confirmed
direct_app_training_approval = no_until_independent_confirmation
priority = 2
```

Use rule:

This may support cross-method consistency research. It must not be entered as a `known_depth_positive` unless excavation, survey, or another independently reviewed source confirms the depth-to-top reference.

## Candidate P5 — Morocco utilities and voids dataset

Source: DOI `10.17632/ww7fd9t325.1`

Current classification:

```text
real_field_data = yes
benign_targets = yes
detection_labels = yes
independent_numeric_depth_labels = not_confirmed
classification_benchmark = suitable
depth_calibration = not_approved
priority = 3
```

## Candidate P6 — MERL-GPR

Source: DOI `10.5281/zenodo.8145084`

Current classification:

```text
real_field_data = no
simulated_exact_depth = yes
software_and_method_testing = suitable
scientific_real_calibration = prohibited
priority = method_only
```

## Import rule

A source may enter the private calibration pack only after all of the following are recorded:

```text
source DOI and version
licence
independent depth provenance
depth reference definition
uncertainty or defensible uncertainty policy
target family and dimensions
host material or surface context
physical-site group
acquisition date or period
approved sensor feature availability
scale and support assessment
```

A public source can be useful without being a direct app-training source. The register keeps three separate decisions:

```text
source_evidence_usable
method_research_usable
direct_app_calibration_usable
```

## Immediate execution order

1. extract TU1208 numerical target depths from the published cross-section figures;
2. obtain the IAG/USP actual-depth table and public-data availability details;
3. inspect the complete Guangzhou archive metadata or contact the authors;
4. seek independent excavation confirmation for Hacimusalar;
5. perform satellite-scale separability checks before importing any target as an app calibration row;
6. continue searching for additional independent physical sites so holdout validation is possible.

## Checklist

- [x] Establish a structured candidate register.
- [x] Identify TU1208 as independently surveyed physical-depth evidence.
- [x] Identify IAG/USP as installed known-depth evidence.
- [x] Keep Hacimusalar as interpreted-depth evidence only.
- [x] Keep simulated data separate from real calibration.
- [ ] Extract TU1208 target-depth values and depth-reference definitions.
- [ ] Extract IAG/USP actual-depth values and target metadata.
- [ ] Confirm raw-data access and machine-readable mapping for IAG/USP.
- [ ] Complete Guangzhou metadata inspection or author inquiry.
- [ ] Add at least three independent physical-site groups.
- [ ] Run scale and approved-feature compatibility screening.
- [ ] Import only verified, supportable records into the private pack.
