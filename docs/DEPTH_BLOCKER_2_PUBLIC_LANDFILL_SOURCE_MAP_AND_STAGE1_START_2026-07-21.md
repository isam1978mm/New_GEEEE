# Blocker 2 — Public Landfill Engineering Source Map and Stage-1 Start — 2026-07-21

Status: authorized documentation update and initial Stage-1 screening record. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, app-depth enablement, contact, or fieldwork is authorized by this document.

Read with:

- `docs/DEPTH_BLOCKER_2_LANDFILL_CQA_CANDIDATE_SCREENING_PLAN_2026-07-21.md`
- `docs/DEPTH_BLOCKER_2_PUBLIC_ONLY_FAILURE_2026-07-21.md`
- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
- `docs/DEPTH_CONFOUNDER_CONTROL_SPEC.md`

## Current decision

```text
candidate_source_class = landfill_final_cover_cqa_and_closure_records
stage_1_status = started
blocker_2_status = unresolved
formal_reopen_status = not_requested
calibration_pack_intake = not_authorized
depth_training = blocked
app_depth_enabled = false
```

## Verified public source hierarchy

### Tier 1 — EPA CCR public compliance websites

Primary national index:

- EPA `List of Publicly Accessible Internet Sites Hosting CCR Management Compliance Data and Information`.
- The EPA list was last updated June 25, 2026.
- The list links to facility-maintained public websites required by the CCR rule.

Why this tier is useful:

- many independent facilities;
- standardized closure and post-closure document categories;
- public written closure plans, professional-engineer certifications, notices, annual reports, and related records;
- hectare-scale or larger engineered disposal units;
- clear facility and unit names.

Limits:

- the EPA list is an index, not calibration truth;
- each facility document set remains `candidate_under_review`;
- public posting does not guarantee surveyed top-of-waste elevations, final-grade elevations, numerical survey tolerance, observation-date settlement support, or Sentinel-1 depth linkage;
- coal-combustion residual units are regulated engineered waste-containment structures, not automatically an approved benign finding family. Finding-family and sensitivity review remain required.

### Tier 2 — State engineering and cleanup portals

High-value portals include:

- Washington Ecology Cleanup and Tank Search;
- Florida DEP OCULUS;
- New York DEC DECDocs;
- Arkansas DEQ solid-waste records and ePortal;
- Texas TCEQ facility records;
- other state closure, CQA, solid-waste, and cleanup-document systems.

Why this tier is useful:

- facility-specific CQA certification reports;
- engineering design reports;
- final-cover topographic surveys;
- record or as-built drawings;
- construction summaries;
- survey and geotechnical records;
- later monitoring and periodic-review reports.

Limits:

- document naming and completeness are inconsistent;
- some portals expose only metadata or require a public-records request;
- exact depth-to-top and uncertainty still require document-level extraction.

### Tier 3 — EPA SEMS, Superfund, and post-closure archives

Primary use:

- five-year reviews;
- operation and maintenance reports;
- settlement-monument tables;
- later topographic surveys;
- final-cover repair history;
- observation-date condition checks.

Limits:

- a report saying that settlement was observed is insufficient;
- usable settlement evidence needs monument or survey identifier, date, elevation, vertical datum or reference, precision, and a relationship to the proposed analysis footprint.

### Tier 4 — Public geotechnical archives for negative candidates

Examples:

- BGS GeoIndex and scanned borehole, shaft, trial-pit, and well records;
- US state DOT and geotechnical archives.

Use rule:

```text
single_borehole_log = not_a_confirmed_negative
```

A negative candidate requires multi-point coverage of the full Sentinel-1 analysis footprint, evidence supporting absence of the approved buried-feature family, and documented land-use or construction stability during the observation period.

## Source-specific corrections and guardrails

1. Do not describe coal ash as benign. Treat it as regulated engineered waste requiring finding-family and sensitivity review.
2. Treat the EPA CCR master list as a high-yield candidate index only.
3. Do not use any reported Cocopah cover or settlement number until the exact primary document, page, table, date, and identifier are recovered.
4. Do not assume SEMS or five-year-review records contain survey-grade settlement data.
5. Use current BGS wording: more than one million borehole, shaft, and well records are indexed; individual logs remain negative candidates only.
6. A closure plan is a design document. It does not replace an as-built survey or CQA certification report.
7. Final-cover thickness is not automatically depth-to-top unless the source establishes the top-of-waste or CCR subgrade reference and comparable survey location.
8. Sentinel-1 availability is not Sentinel-1 depth linkage.

## Stage-1 initial candidate screen

### N1-01 — Go East Corp Landfill, Washington

Named public documents:

- `Go East Corp Landfill - Construction Quality Assurance Report (without appendices)`, revised July 1, 2022;
- `Go East Corp Landfill - As-Built/Record Drawings (Appendix O of Construction Quality Assurance Report, July 1, 2022)`;
- `Go East Corp Landfill - Construction Summary Report (Appendix E of Construction Quality Assurance Report, July 1, 2022)`;
- approved closure plans and specifications.

Verified facts:

- closure construction ran from March 2021 through July 2022;
- the landfill footprint was reduced from about 10 acres to about 6 acres;
- final geomembrane cover and initial overlying soils were installed from January through March 2022;
- licensed surveyors produced as-built survey documents;
- the CQA report states that the final surface improvements included an additional final one foot of cover under later work;
- the site includes major grading, drainage, vegetation, residential development, and other strong surface confounders.

Current field status:

```text
candidate_state = candidate_under_review
named_public_documents = pass
closure_window = pass
professional_cqa = pass
large_analysis_footprint = pass
as_built_drawings = pass
depth_to_top = unresolved
numerical_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = high_risk_surface_and_development_confounding
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- retain for document extraction;
- do not treat the stated one-foot cover as `known_depth_top_m` without matching top-of-waste or verified layer reference;
- likely difficult as a clean Sentinel-1 experiment because landfill closure and subdivision construction overlap.

### N1-02 — Sudbury Road Landfill, Washington

Named public documents:

- `Construction Quality Assurance Certification Report`, April 14, 2017;
- `Engineering Design Report for Sudbury Landfill Remedial Action`, January 6, 2016;
- `Construction Plans and Specs - Vol I - Final`;
- `Construction Plans and Specs - Vol II - Final`;
- `Construction Plans and Specs - Vol III CQA - Final`;
- `Sudbury Landfill Periodic Review 2022`.

Current field status:

```text
candidate_state = candidate_under_review
named_public_documents = pass
closure_in_sentinel_1_era = pass_or_likely
depth_to_top = not_yet_extracted
numerical_uncertainty = not_yet_extracted
settlement_or_later_topography = candidate_2022_periodic_review
s1_scale = not_yet_screened
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- high-priority state-portal candidate because it has CQA, engineering design, construction plans, and a later periodic review;
- next task is document-level extraction of elevations, cover details, survey tolerance, dates, and later surface condition.

### N1-03 — Paradise Fossil Plant Slag Ponds 2A and 2B, Kentucky

Named public documents:

- `257-102(d)_Written Closure Plan_PAF_Slag Stilling Pond 2C_Rev3`, November 19, 2020, covering Slag Ponds 2A and 2B and Stilling Pond 2C;
- `257-102(d)(3)(iii)_Certification of Final Closure System_PAF_Slag Stilling Pond 2C`;
- `257-102(h)_Certification of Closure_PAF_Slag Stilling Pond 2C`;
- written post-closure plan and annual inspection records.

Verified facts:

- Slag Ponds 2A and 2B were identified as 16.5 acres and 11.5 acres and proposed for closure in place;
- the combined area requiring final cover was estimated at approximately 29.2 acres;
- the closure plan scheduled site grading in 2021, final-cover installation in 2022, and closure completion in 2023;
- the plan specifies final-cover performance and minimum soil-layer requirements, but a plan is not an as-built depth record;
- Stilling Pond 2C involved removal and repurposing and must not be mixed with closure-in-place positives.

Current field status:

```text
candidate_state = candidate_under_review
named_public_documents = pass
closure_window = pass
large_analysis_footprint = pass
closure_in_place_positive_area = pass_for_2A_2B_only
as_built_depth_to_top = unresolved
numerical_uncertainty = unresolved
observation_date_settlement = unresolved
mixed_unit_risk = high_if_2C_is_included
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- retain Slag Ponds 2A and 2B as a candidate unit;
- exclude Stilling Pond 2C from the same positive experiment because its CCR was removed and the area was repurposed;
- recover final CQA/as-built records before any depth label is considered.

### N1-04 — Shawnee Consolidated Waste Dry Stack, Kentucky

Named public documents:

- `257-102(h)_Certification of Closure_SHF_Consolidated Waste Dry Stack`;
- `257-102(b)_Written Closure Plan_SHF_Consolidated Waste Dry Stack_Rev2`;
- written post-closure plan and annual monitoring records.

Verified facts:

- the written closure plan reports approximately 309 acres as the largest area requiring final cover;
- the planned alternative final cover uses structured geomembrane, engineered turf, and sand infill;
- the plan states that settlement monitoring will be completed;
- a closure certification is publicly listed.

Current field status:

```text
candidate_state = candidate_under_review
named_public_documents = pass
closure_certification = pass
satellite_scale = pass
exact_as_built_cover_depth = unresolved
numerical_uncertainty = unresolved
settlement_monitoring_records = referenced_not_recovered
surface_material_comparability = high_risk_synthetic_cover
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- retain as a high-priority large-area candidate;
- synthetic turf and geomembrane create a major surface-signature confounder and may make the unit method-research-only even if engineering documentation is complete.

### N1-05 — Gallatin North Rail Loop Landfill, Tennessee

Named public document:

- `257-102(b)_Written Closure Plan_GAF_North Rail Loop Landfill Cell 1 - Rev 1`, September 16, 2021.

Verified facts:

- the largest future area requiring final cover is approximately 52.4 acres;
- the alternative cover includes 12 inches of vegetative soil, 12 inches of protective soil, a drainage layer, and a geomembrane;
- Cell 1 operation completion was scheduled for 2021, but installation of the final cover system and completion of closure were scheduled for 2033.

Current field status:

```text
candidate_state = candidate_under_review
named_public_document = pass
satellite_scale = pass
s1_era_final_closure_event = fail_or_not_yet_occurred
as_built_depth_to_top = unavailable
numerical_uncertainty = unavailable
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- not suitable for the current S1-era final-closure screen unless later public records show a separately completed and isolated cell-cover event;
- retain only as a future or phased-cell lead.

### N1-06 — Independence Plant, Arkansas

Named public document groups:

- `Written Closure Plan and Amendments — Existing CCR Landfill Cells 12-15`;
- closure-plan summary and professional-engineer certification letter;
- closure and completion notifications for the East and West Recycle Ponds;
- written post-closure plans.

Current field status:

```text
candidate_state = candidate_under_review
public_compliance_site = pass
named_document_groups = pass
landfill_cells_final_closure_event = unresolved
recycle_ponds_closure_completion = pass_at_metadata_level
closure_in_place_vs_removal = unresolved
depth_to_top = not_yet_extracted
numerical_uncertainty = not_yet_extracted
s1_scale = not_yet_screened
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- retain for document-level screening;
- do not assume recycle-pond closure created a depth-positive unit until closure method and remaining-material reference are verified.

## Initial Stage-1 result

```text
named_facilities_screened = 6
facilities_with_public_cqa_or_closure_certification = 5+
facilities_with_clear_sentinel_1_era_closure_window = at_least_3
facilities_with_verified_contract_complete_depth_to_top = 0
facilities_with_verified_numerical_uncertainty = 0
facilities_with_verified_observation_date_depth = 0
facilities_with_demonstrated_sentinel_1_depth_linkage = 0
```

This is a successful start of Stage 1, not a reopen result.

## Next Stage-1 tasks

1. Extract the Sudbury CQA, engineering, plans, and 2022 periodic-review fields.
2. Recover Paradise final CQA or as-built records for Ponds 2A and 2B and separate them from 2C.
3. Recover Shawnee settlement-monitoring and as-built cover records.
4. Inspect Independence closure documents for closure method, unit footprint, dates, and survey support.
5. Add geographically independent facilities from the EPA CCR master list and state portals.
6. Screen only preliminary Sentinel-1 acquisition availability after document fields support a plausible experiment.
7. Keep all rows in `candidate_under_review` or `evidence_verified_pending_support`; no row may become `direct_calibration_candidate` before Stage 3.

## Current consequence

```text
blocker_2_status = unresolved
stage_1_status = active
formal_reopen_status = not_requested
calibration_pack_intake = not_authorized
depth_training = blocked
app_depth_enabled = false
```
