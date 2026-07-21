# Depth P4 Ahmadu Bello Source Qualification — 2026-07-20

Status: partial source qualification for the private local depth-research workflow. This document records verified public facts and unresolved evidence gaps for Candidate P4. It does not approve private-pack import, model fitting, or app depth output.

## Candidate

```text
candidate_id = P4
authoritative_name = Ahmadu Bello University Geophysics Test Site
primary_depth_article_doi = 10.1016/j.envc.2024.100910
construction_article_doi = 10.1007/s12517-024-12039-7
```

## Verified physical-depth records

The open depth-comparison article explicitly labels its actual-depth column as `Depth to top (m)` and reports eight physical references:

```text
six_empty_plastic_buckets = 0.80 m
one_horizontal_empty_steel_drum = 0.80 m
two_horizontal_empty_steel_drums = 1.00 m
one_vertical_empty_steel_drum = 0.60 m
six_water_filled_plastic_buckets = 0.80 m
four_cylinder_engine_block = 1.20 m
concrete_block = 0.80 m
two_horizontal_pipes = 0.50 m
```

These values match the eight candidate rows already stored in `docs/depth_public_evidence/controlled_site_depths_v1.json`.

## Other verified facts

- the controlled site is approximately 55 m by 55 m;
- the host material is described as lateritic-clay soil;
- targets were installed with known materials, dimensions, positions, depths, and orientations;
- a pre-burial geophysical investigation was conducted;
- the pre-burial investigation reported no major target-related anomaly that would significantly influence the post-burial comparison;
- post-burial electrical-resistivity and VLF-EM investigations were performed;
- the article compares geophysical estimates against actual physical depths rather than treating those estimates as ground truth;
- the underlying datasets are available from the authors on request;
- the full site must remain one physical-site group for leakage control.

## Evidence not recovered in this pass

The following were not found in the reviewed public sources:

- numerical installation-depth tolerance;
- numerical survey or surface-reference uncertainty;
- a final bounded uncertainty for each depth-to-top record;
- the exact calendar date or construction interval when targets were installed;
- a public machine-readable raw-data package with acquisition dates;
- a public construction log or target-placement sheet.

No uncertainty value is invented. The existing candidate rows must retain `reference_uncertainty_m = null` until source-backed evidence is recovered.

## Confirmed-background status

The source documents a pre-burial survey state and reports no major anomaly that would significantly affect the target-response study.

This is useful independent ground-method background evidence, but it is not automatically an approved Sentinel-1 `confirmed_no_target` record. A satellite-background record still requires:

```text
exact installation date or bounded event window
matching pre-installation Sentinel-1 acquisitions
controlled orbit and observation geometry
comparable season and moisture
separation of excavation and restoration disturbance
private site and background windows
```

## Scale decision

The completed Sentinel-1 scale screen remains binding:

```text
sentinel_1_target_level_separation = not_supported
whole_site_pre_post_screen = priority_candidate_pending_dates
approved_experiment_unit = physical_site_or_large_isolated_section
```

The eight depth-to-top values must not be converted into eight independent Sentinel-1 samples.

## Current classification

```text
physical_depth_provenance = installed_known_depth
reference_definition = explicit_depth_to_top
verified_depth_record_count = 8
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
pre_burial_ground_survey = yes
post_burial_ground_survey = yes
exact_installation_date = not_recovered
raw_data_access = author_request
source_evidence_usable = yes_for_ground_method_truth
method_research_usable = yes
direct_app_calibration_usable = no_target_level_scale_not_supported
private_pack_import_approved = no_missing_reference_uncertainty_and_source_materials
candidate_state = evidence_verified_pending_uncertainty_dates_and_support
```

## Qualification decision

P4 is strong installed depth-to-top evidence for ground-method research. The eight depth values and their target descriptions are independently documented and may remain in the repository-safe candidate file.

P4 is not ready for private calibration-pack import because the required reference uncertainty is absent. Its whole-site Sentinel-1 pre/post path also remains blocked until an installation date or defensible event interval is recovered and matching acquisition support is verified.

## Next actions

1. Request installation or survey tolerance for the eight depth records.
2. Request the construction log, target-placement sheet, and exact installation date or bounded construction period.
3. Request the underlying pre-burial and post-burial datasets and acquisition dates.
4. Preserve all records under one physical-site group.
5. Create private site and background windows only after date recovery.
6. Run the aggregate Sentinel-1 coverage and orbit screen.
7. Import no record until uncertainty, source versions, review fields, and support decisions satisfy the complete depth dataset contract.

## Current decision

```text
P4_depth_to_top_records = verified_8
P4_reference_uncertainty = blocked_requires_source_request
P4_exact_installation_date = blocked_requires_source_request
P4_raw_data = available_on_request_not_acquired
P4_confirmed_background = candidate_not_approved
P4_private_pack_import = not_approved
P4_whole_site_pre_post_research = pending_dates_and_coverage
app_depth_enabled = false
```
