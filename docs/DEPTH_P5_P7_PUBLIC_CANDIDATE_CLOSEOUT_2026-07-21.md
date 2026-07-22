# Depth P5–P7 Public Candidate Closeout — 2026-07-21

Status: `public_queue_closeout_method_only_or_blocked`.

No email, form, author contact, operator contact, or records request was sent.

## P5 — Guangzhou University GPR dataset

Public archive reviewed: Zenodo DOI `10.5281/zenodo.14637589`.

Verified:

- 3.8 GB public archive containing real tunnel-lining, pipeline, and reinforced-concrete GPR data;
- pipeline folder contains raw/proprietary radar project files and many scan files;
- Zenodo archive preview exposes `.dt`, `.RAD`, `.RD3`, `.MIS`, `.ZON`, `.ini`, `.Bkg`, `.Stc`, marker text, and project-data folders;
- the public preview contains no visible PDF, spreadsheet, CSV, CAD drawing, depth map, or independent construction/survey table;
- archive and record descriptions state that pipeline layouts and depths vary but do not map scans to independently measured numerical depth-to-top truth or uncertainty.

Decision:

```text
candidate_id = P5
real_gpr_data = yes
independent_depth_table_public = no
reference_definition = unresolved
reference_uncertainty = unresolved
method_research_usable = yes
known_depth_positive = no
private_pack_import = not_approved
public_only_path = exhausted_without_full_3_8_GB_download_or_source_materials
```

## P6 — Hacımusalar multi-method survey

Public sources reviewed:

- Mendeley Data DOI `10.17632/27wsdn3mc2.1`;
- conference record DOI `10.3997/2214-4609.202420109`.

Verified:

- real-field GPR, ERT, and magnetometry data are publicly described;
- anomalies are interpreted as a shallow buried rectangular/wall body;
- approximately 1.2 m is an interpreted GPR depth;
- no excavation, open-trench survey, engineering as-built, or independently measured depth-to-top confirmation was found in the public record reviewed.

Decision:

```text
candidate_id = P6
reported_depth = approximately_1.2_m
physical_depth_provenance = geophysical_interpretation_only
independent_confirmation = not_found
method_research_usable = yes_cross_method
known_depth_positive = no
private_pack_import = prohibited_pending_independent_confirmation
```

## P7 — Morocco utilities and voids dataset

Public sources reviewed:

- Mendeley Data DOI `10.17632/ww7fd9t325.1`;
- Data in Brief DOI `10.1016/j.dib.2025.111338`.

Verified:

- 2,239 JPEG radargram images collected during infrastructure projects in Morocco from 2019–2024;
- labels cover utilities, voids, and intact zones;
- the dataset is designed for detection/classification training;
- public descriptions do not provide independently measured per-image numerical depth-to-top labels, survey uncertainty, construction records, coordinates, or physical-site leakage groups.

Decision:

```text
candidate_id = P7
classification_benchmark = suitable
confirmed_negative = not_approved_intact_label_is_not_independent_absence_proof
known_depth_positive = no
numerical_depth_calibration = not_approved
private_pack_import = prohibited
```

## Queue decision

P5–P7 do not unblock the contract-ready private calibration pack.

The remaining highest-value executable path is TAMUCC P3, but its next step requires owner-controlled private inputs and authenticated Earth Engine execution:

```text
private_site_geojson
+ private_independently_reviewed_background_geojson
+ authenticated_Earth_Engine_session
+ exact_A_ASCENDING_relative_orbit_107_shared_image_match
+ private_manifest_output_outside_Git
```

Without those inputs, the exact shared-image match cannot be executed safely or reproducibly from the public repository alone.

## Current blocker state

```text
public_P1_P2_uncertainty_path = blocked_requires_source_materials
P3_exact_S1_match = blocked_requires_owner_private_inputs_and_EE
P4_S1_route = rejected_phased_installation
P5 = method_only_missing_independent_depth_table
P6 = method_only_interpreted_depth
P7 = classification_only_missing_numeric_depth_truth
confirmed_negative_count = 0
contract_ready_positive_count = 0
private_pack_status = blocked_missing_contract_ready_pack
model_fitting = prohibited
app_depth_enabled = false
```

## Public references

- Guangzhou University GPR dataset: `https://zenodo.org/records/14637589`
- Hacımusalar dataset: `https://data.mendeley.com/datasets/27wsdn3mc2/1`
- Hacımusalar conference record: `https://research.itu.edu.tr/en/publications/new-findings-at-hacimusalar-mound-through-the-ground-penetrating-/`
- Morocco utilities and voids dataset: `https://data.mendeley.com/datasets/ww7fd9t325/1`
- Morocco dataset article: `https://pmc.ncbi.nlm.nih.gov/articles/PMC11847285/`
