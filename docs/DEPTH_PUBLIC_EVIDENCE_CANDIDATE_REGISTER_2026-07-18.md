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
- supporting pipe-depth application DOI `10.3390/rs15082114`

Verified source facts:

- full-size controlled geophysical test site;
- benign targets include pipes, artificial voids, masonry, rocks, cables, and other civil-engineering objects;
- targets were installed during construction and accurately geolocated with a theodolite;
- the source records points on the upper side or upper corners of targets and interpolates the local surveyed surface above them, so the resulting target depth is a surface-to-target-top or surface-to-target-upper-side reference rather than a GPR-derived center-depth estimate;
- target depths were calculated from independently surveyed target and surface elevations, not estimated from the GPR response;
- supporting literature explicitly reports the three Gneiss 14/20 pipe layers at approximately 0.9 m, 1.5 m, and 2.1 m;
- multiple pipe layers occur at different depths and in different host materials;
- 67 GPR profiles were recorded along eleven parallel lines with several radar systems and antenna frequencies;
- raw files are publicly available under CC BY 4.0;
- no numerical theodolite, installation, surface-interpolation, or final depth-reference uncertainty was found in the primary article or the public archive metadata reviewed during this pass.

Current classification:

```text
physical_depth_provenance = independently_surveyed
reference_definition = surveyed_local_surface_to_target_upper_side
verified_pipe_depth_subset_m = 0.9_1.5_2.1_gneiss_14_20
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
raw_gpr_available = yes
multiple_depth_levels = yes
multiple_host_materials = yes
multiple_physical_sites = no_single_test_site
sentinel_1_included = no
source_evidence_usable = yes_for_ground_method_truth
method_research_usable = yes
direct_app_calibration_usable = no_current_sentinel_1_scale
private_pack_import_approved = no_missing_uncertainty_and_complete_record_mapping
priority = 1
```

Qualification update — 2026-07-20:

1. The depth-reference ambiguity is resolved for surveyed targets: the paper describes upper-target survey points and local surface interpolation, which supports depth to the top or upper side of the feature.
2. The 0.9 m, 1.5 m, and 2.1 m values are retained as a verified subset for the Gneiss 14/20 pipe layers.
3. These three values do not create three independent Sentinel-1 calibration samples; they belong to one compact physical site and one mixed satellite-scale experiment unit.
4. The source remains strong for GPR and ground-method validation.
5. Private calibration-pack import remains blocked because a numerical reference-uncertainty value or defensible source-backed uncertainty policy is still missing, and the remaining target-level figure values have not yet been mapped into complete contract records.

Remaining extraction work:

1. extract the remaining target values from the published test-site cross-section figures;
2. map each retained target or target layer to the corresponding radar profile and host-material region;
3. recover a source-reported survey or installation uncertainty, or document why the source cannot supply one;
4. assign the full test site to one physical-site group to prevent line-level leakage across splits;
5. retain the completed scale-screen result: no target-level Sentinel-1 rows from this compact mixed site;
6. if uncertainty cannot be recovered, retain this source for GPR method validation and uncertainty research only.

Important limitation:

The test site is one physical site with many closely spaced objects. Multiple radar profiles are not independent physical-site holdouts. The data must never be split by profile as though each line were a separate site.

## Candidate P2 — IAG/USP shallow geophysics controlled test site

Sources:

- depth study DOI `10.4236/ijg.2017.85040`
- controlled-site construction paper DOI `10.1590/S0102-261X2006000100004`

Verified source facts:

- controlled university test site with targets installed at known positions and depths;
- seven target lines contain benign archaeological, utility, concrete, drum, pipe, and cable analogues;
- the construction source explicitly states that installed depths are measured relative to the top of each target;
- the installation workflow included a topographic survey while the excavation remained open to determine target position and depth relative to the ground surface;
- the Line 4 actual-depth table contains eight verified references: A `1.97 m`, B `0.50 m`, C `0.98 m`, D `0.50 m`, E `0.90 m`, F `0.97 m`, G `1.00 m`, and H `1.98 m`;
- targets A, B, C, E, and F are horizontal empty steel drums, D is a metallic reference pipe, and G and H are vertical empty steel drums;
- the site is explicitly used to compare installed depths with geophysical depth estimates;
- geophysical measurements were collected before and after target installation, creating useful ground-method background evidence;
- construction occurred in 2003, before Sentinel-1, so the pre-installation measurements cannot supply a same-sensor Sentinel-1 negative period;
- no numerical topographic, placement, or final depth-reference uncertainty was found in the reviewed papers;
- no public machine-readable raw-radar archive or target spreadsheet was found during this pass.

Current classification:

```text
physical_depth_provenance = installed_and_topographically_surveyed
reference_definition = ground_surface_to_target_top
verified_line4_depths_m = A_1.97_B_0.50_C_0.98_D_0.50_E_0.90_F_0.97_G_1.00_H_1.98
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
raw_public_dataset_confirmed = no
machine_readable_target_table = not_publicly_found
pre_installation_ground_data = yes
multiple_depth_levels = yes
multiple_target_families = yes
multiple_physical_sites = no_single_test_site
sentinel_1_included = no
sentinel_1_pre_installation_opportunity = no_site_predates_mission
source_evidence_usable = yes_for_ground_method_truth
method_research_usable = yes
direct_app_calibration_usable = no_current_sentinel_1_scale_and_missing_uncertainty
private_pack_import_approved = no_missing_reference_uncertainty
priority = 1
```

Qualification update — 2026-07-20:

1. The eight candidate rows already extracted in `controlled_site_depths_v1.json` are confirmed against the published actual-depth table.
2. The construction paper resolves the depth definition as depth to the top of the target, measured relative to the ground surface.
3. The source is strong installed-depth truth for ground-method research.
4. The site remains one physical group; its seven lines and repeated observations must not cross train, validation, and holdout splits.
5. Private-pack import remains blocked because the source does not provide a numerical reference uncertainty and the public raw-data or machine-readable construction package has not been recovered.
6. The pre-installation survey is useful ground-method background evidence but cannot be a same-sensor Sentinel-1 negative because it predates the mission.

Remaining extraction work:

1. recover a source-reported survey, placement, or topographic uncertainty;
2. seek the original target spreadsheet described by the construction paper;
3. seek any public or author-provided raw radargrams and acquisition metadata;
4. complete source-version and evidence-review fields for each retained target record;
5. retain the completed scale-screen result: no individual target-level Sentinel-1 calibration rows from this compact site;
6. if uncertainty cannot be recovered, retain the source for ground-method truth and method research rather than approving private-pack import.

## Candidate P3 — Texas A&M University–Corpus Christi geophysical test site

Sources:

- construction article DOI `10.1190/tle40030208.1`
- official university project description dated November 2020

Verified source facts:

- controlled 50 m by 50 m university field site;
- construction included a pre-installation survey, excavation, and placement of known targets;
- benign targets include steel drums, plastic drums, plastic buckets, steel pipes, and well covers;
- targets are distributed along seven lines and grouped by material;
- the published site description reports target depths from approximately 0.5 m to 3.0 m;
- the article reportedly documents target types, locations, orientations, and depths.

Current classification:

```text
physical_depth_provenance = installed_known_depth
real_field_data = yes
benign_targets = yes
site_scale = 50_m_by_50_m
multiple_depth_levels = yes
raw_public_dataset_confirmed = no
machine_readable_target_table = not_yet
sentinel_1_included = no
direct_app_training_approval = pending_table_access_and_scale_match
priority = 1
```

Required extraction work:

1. obtain the article table or figure containing target-level depths and orientations;
2. confirm whether each depth means depth-to-top, center, base, or excavation depth;
3. request any available radar, resistivity, magnetic, or other survey files and acquisition dates;
4. treat the full field as one physical-site group;
5. evaluate whether the 50 m by 50 m area supports any defensible satellite-scale window without mixing multiple targets.

## Candidate P4 — Ahmadu Bello University geophysics test site

Sources:

- open depth-comparison article DOI `10.1016/j.envc.2024.100910`
- controlled-site development review DOI `10.1007/s11600-023-01096-3`
- related controlled-site studies referenced by the open article

Verified source facts:

- controlled 55 m by 55 m field site on lateritic-clay soil;
- targets were physically installed with known materials, properties, geometries, orientations, and depths;
- published sources describe a site depth range of approximately 0.6 m to 3.0 m;
- benign targets include floor tile, concrete blocks, metallic pipes, plastic buckets, steel drums, and an engine block;
- the 2024 open study evaluates eight buried targets against their actual depths;
- the same site has been surveyed using multiple geophysical methods, including electrical resistivity, VLF-EM, magnetic, and seismic methods;
- datasets from the depth study are available from the authors on request rather than as a public archive.

Current classification:

```text
physical_depth_provenance = installed_known_depth
real_field_data = yes
benign_targets = yes
site_scale = 55_m_by_55_m
multiple_depth_levels = yes
multi_method_measurements = yes
public_target_level_depth_table = not_yet_extracted
raw_data_access = author_request
sentinel_1_included = no
direct_app_training_approval = pending_table_data_and_scale_match
priority = 1
```

Required extraction work:

1. extract the actual-depth column for the eight evaluated targets from the open paper;
2. map each actual depth to target type, dimensions, profile, and orientation;
3. contact the authors for the underlying datasets and target construction sheet;
4. confirm the depth reference definition and installation uncertainty;
5. treat the whole 55 m by 55 m field as one physical-site group;
6. evaluate satellite-scale separability before importing an app calibration record.

## Candidate P5 — Guangzhou University GPR dataset

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

## Candidate P6 — Hacimusalar multi-method survey

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

## Candidate P7 — Morocco utilities and voids dataset

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

## Candidate P8 — MERL-GPR

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

1. complete the remaining TU1208 target mapping and seek source-backed uncertainty;
2. seek IAG/USP reference uncertainty, the original target spreadsheet, and any raw public or author-provided data;
3. obtain the Texas A&M–Corpus Christi target-level construction table;
4. extract the Ahmadu Bello actual-depth table and request the underlying datasets;
5. inspect the complete Guangzhou archive metadata or contact the authors;
6. seek independent excavation confirmation for Hacimusalar;
7. apply the completed satellite-scale rule before importing any target as an app calibration row;
8. continue searching for additional independent physical sites and confirmed no-target/background cases.

## Checklist

- [x] Establish a structured candidate register.
- [x] Identify TU1208 as independently surveyed physical-depth evidence.
- [x] Identify IAG/USP as installed known-depth evidence.
- [x] Identify Texas A&M–Corpus Christi as installed known-depth evidence.
- [x] Identify Ahmadu Bello University as installed known-depth evidence.
- [x] Reach at least three independent controlled physical-site candidates for screening.
- [x] Keep Hacimusalar as interpreted-depth evidence only.
- [x] Keep simulated data separate from real calibration.
- [x] Resolve the TU1208 surveyed target-top depth reference.
- [x] Extract the TU1208 Gneiss 14/20 pipe-layer subset at 0.9 m, 1.5 m, and 2.1 m.
- [ ] Complete TU1208 remaining target mapping and recover reference uncertainty.
- [x] Confirm the IAG/USP Line 4 actual-depth table and target-top definition.
- [x] Confirm that IAG/USP installation used open-pit topographic surveying.
- [ ] Recover IAG/USP reference uncertainty, original target spreadsheet, and raw-data availability.
- [ ] Obtain Texas A&M–Corpus Christi target-level depths and data-access information.
- [ ] Extract Ahmadu Bello target-level actual depths and request data.
- [ ] Complete Guangzhou metadata inspection or author inquiry.
- [ ] Find independently documented confirmed no-target/background cases.
- [x] Run the first scale and approved-feature compatibility screening.
- [ ] Import only verified, supportable records into the private pack.
