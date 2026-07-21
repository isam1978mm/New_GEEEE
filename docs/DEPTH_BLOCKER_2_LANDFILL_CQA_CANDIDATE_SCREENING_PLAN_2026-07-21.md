# Blocker 2 — Landfill Final-Cover CQA Candidate-Screening Plan — 2026-07-21

Status: approved documentation plan for a new public-source screening path. Blocker 2 remains unresolved. This document does not reopen Blocker 2, authorize calibration-pack intake, or permit depth training.

Creating this plan is the authorized repository documentation change. Execution of Stage 1 remains read-only and must produce its assessment in chat without creating or editing additional repository or private-pack files.

Read with:

- `docs/DEPTH_REMAINING_BLOCKERS_AND_UNBLOCKING_PLAN_2026-07-20.md`
- `docs/DEPTH_BLOCKERS_EXECUTION_PLAN_2026-07-20.md`
- `docs/DEPTH_BLOCKER_2_PUBLIC_ONLY_FAILURE_2026-07-21.md`
- `docs/DEPTH_PUBLIC_SOURCE_ELIGIBILITY_MATRIX_2026-07-21.md`
- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
- `docs/DEPTH_CONFOUNDER_CONTROL_SPEC.md`
- `docs/DEPTH_VALIDATION_GATES_SPEC.md`

## Current decision

```text
blocker_id = 2
candidate_source_class = landfill_final_cover_cqa_certification_reports
candidate_status = candidate_under_review
blocker_2_status = unresolved
formal_reopen_status = not_requested
calibration_pack_intake = not_authorized
depth_training = blocked
app_depth_enabled = false
```

The previous public-only search screened landfill inventories but did not screen facility-specific final-cover Construction Quality Assurance certification and validation reports as a separate source class.

These reports may contain as-built elevations, verified layer thicknesses, construction dates, survey precision or tolerance, settlement information, and cell boundaries. Those fields make the class worth screening.

They do not establish that Sentinel-1 measures cover depth. Sentinel-1 may respond only to surface construction, moisture, vegetation, roughness, drainage, terrain, or settlement. This plan tests that distinction rather than assuming a depth signal.

## Governance constraints

The following existing rules remain binding:

- natural-interface analogs such as permafrost thaw depth and groundwater depth are method-only and prohibited from calibration-pack import;
- ordnance and other out-of-family sources remain excluded;
- the approved Sentinel-1 experiment unit is:

```text
whole_physical_site_or_large_isolated_section_pre_post_experiment
```

- individual survey points, small targets, or pixels must not be promoted into independent satellite calibration rows;
- new sources must use the existing B2/B6 register and decision vocabulary;
- no uncertainty, settlement correction, depth reference, negative status, or sensor support may be invented;
- no one is contacted and no fieldwork is requested from the user under this plan;
- private coordinates, source paths, and calibration records remain outside Git.

## Candidate decision vocabulary

Every candidate must remain in or end in one existing B6 state:

```text
candidate_under_review
evidence_verified_pending_support
direct_calibration_candidate
method_research_only
rejected_missing_independent_depth
rejected_missing_uncertainty
rejected_scale_or_sensor_mismatch
rejected_privacy_or_misuse_risk
rejected_out_of_finding_family
```

Do not create a parallel terminal-state vocabulary. Missing dates, settlement evidence, confirmed negatives, or other detailed failures must be recorded as field-level blockers and quality notes under the closest valid B6 state.

## Open risks

### R1 — Sentinel-1 depth measurability is unproven

A verified cover depth is only a label candidate. It has calibration value only if later multi-site testing shows that adjusted Sentinel-1 measurements track verified depth rather than only surface condition or construction timing.

Stage-1 value:

```text
R1_status = not_tested_pending_stage_3
```

### R2 — Settlement may make construction-time depth stale

The depth at cap construction may differ from the depth during later Sentinel-1 observations.

A candidate requires either:

- an as-built depth survey close enough to the selected Sentinel-1 analysis window to make settlement immaterial under a documented rule; or
- a later source-backed topographic or settlement survey that supports observation-date depth.

Assumed settlement rates are prohibited.

### R3 — Boreholes are not automatic confirmed negatives

A single natural-soil borehole or trial-pit log does not prove that an entire Sentinel-1-sized area is target-free and undisturbed.

A negative candidate requires:

- investigation coverage sufficient for the full analysis footprint;
- traceable evidence supporting no buried feature in the approved finding family;
- documented land-use and construction stability during the Sentinel-1 observation window;
- independent contract-level review.

Until then:

```text
reference_status = uncertain_reference
candidate_state = candidate_under_review
```

### R4 — Reopening is not solving

```text
formal_reopen
= user authorizes the failed public-only path to resume because a source class has passed document, support, and radar-linkage gates

blocker_2_solved
= a private pack passes the dataset contract with eligible positives and confirmed negatives in train, validation, and untouched holdout splits
```

No candidate count by itself solves Blocker 2.

### R5 — Radar linkage must be demonstrated

Before any landfill cell becomes `direct_calibration_candidate`, the project must show across independent facilities that adjusted radar measurements relate to verified observation-date cover depth after controlling for major confounders.

Stage-1 value:

```text
R5_status = not_tested_pending_stage_3
```

## Stage 1 — Public document and coverage screening

Status: read-only. Chat deliverable only.

### Goal

Determine whether named public documents contain enough traceable information to justify source-specific eligibility review.

### Search scope

Screen public regulatory and environmental document portals for Sentinel-1-era final-cover CQA certification or validation reports. The initial target is:

```text
10 to 15 candidate cells
across at least 6 independent facilities
closure or cover construction during or after 2015
```

The target is a search objective, not a readiness threshold.

### Required extraction per positive candidate

Record only source-supported fields:

- public agency or regulator;
- facility and cell reference using a non-coordinate public identifier;
- named document title, date, version, and stable public reference;
- final-grade elevation source;
- top-of-waste elevation source or verified layer-thickness source;
- depth-to-top calculation rule;
- survey method, precision, tolerance, or bounded uncertainty;
- as-built survey date;
- later settlement or topographic survey date when available;
- construction start and completion window;
- cell footprint and isolation from active or mixed cells;
- cover material and surface context;
- terrain, drainage, vegetation, and moisture context when documented;
- preliminary Sentinel-1 pre/post acquisition availability;
- unresolved fields and rejection reasons.

### Depth rule

A candidate depth may be derived only when the source supports one of these forms:

```text
known_depth_top_m
= final_surface_elevation_m - top_of_waste_elevation_m
```

or:

```text
known_depth_top_m
= sum_of_source_verified_cover_layer_thicknesses_m
```

The source must establish a consistent vertical datum and comparable survey locations. No interpolation or conversion is allowed unless the source documents the method and uncertainty.

### Negative-candidate screening

Public borehole, trial-pit, geotechnical, engineering, or construction archives may be screened only as negative-candidate sources.

Each negative candidate must report:

- number and spatial distribution of investigation points;
- relationship of the investigation points to the proposed Sentinel-1 analysis footprint;
- depth and method of investigation;
- whether the record supports absence of the approved buried-feature family;
- evidence of no relevant construction or land-use disturbance during the observation window;
- limitations preventing `confirmed_no_target` status.

A single log cannot pass by itself.

### Sentinel-1 availability screen

For each candidate, confirm only preliminary feasibility:

- pre-construction and post-construction acquisitions exist;
- orbit direction and relative orbit can be matched;
- the cell has valid coverage and adequate clean analysis area;
- the footprint is large enough for a whole-cell or isolated-section experiment;
- adjacent active cells, roads, drainage works, structures, or changing land cover do not make the experiment obviously unusable.

This screen establishes availability, not depth linkage.

### Stage-1 risk values

Every Stage-1 row must report:

```text
R1_depth_measurability = not_tested_pending_stage_3
R2_observation_date_depth = pass | fail | unresolved
R3_negative_eligibility = pass | fail | unresolved | not_applicable
R4_reopen_vs_solve_boundary = acknowledged
R5_radar_linkage = not_tested_pending_stage_3
```

### Stage-1 deliverable

Provide in chat:

- a row-ready candidate table;
- named public documents for every row;
- pass, fail, or unresolved status for every required contract field;
- B6 candidate state;
- R1–R5 status;
- explicit rejection reasons;
- recommendation limited to one of:

```text
proceed_to_stage_2_source_specific_review
continue_stage_1_search
reject_source_class_for_missing_document_evidence
```

Stage 1 cannot declare Blocker 2 reopened or solved.

## Gate 1 — User decision on Stage 2

The user reviews the Stage-1 table and decides whether source-specific eligibility review is authorized.

A recommendation to proceed requires named public documents from multiple independent facilities with plausible depth-to-top, uncertainty, observation-date depth, cell extent, and Sentinel-1 availability.

## Stage 2 — Source-specific contract and support review

Status: separate authorization required.

### Goal

Determine which document-qualified candidates have complete enough evidence and support definitions to enter a radar-linkage experiment.

### Required checks

For each candidate:

- independently documented depth to top;
- numerical uncertainty or source-backed bounded interval;
- observation-date depth validity after settlement review;
- exact physical-site and leakage grouping;
- approved whole-cell or large-isolated-section experiment unit;
- clean analysis window and mixing assessment;
- matched Sentinel-1 acquisition plan;
- source licensing and provenance;
- sensitivity, privacy, and misuse review;
- preliminary positive or negative eligibility.

### Stage-2 decision

Candidates with verified evidence but untested radar linkage must remain:

```text
evidence_verified_pending_support
```

They must not be marked `direct_calibration_candidate` before Stage 3.

### Stage-2 deliverable

Provide a frozen candidate set, proposed site groups, approved analysis footprints held privately, acquisition plans, and explicit exclusions.

No calibration-pack intake occurs at this stage.

## Gate 2 — User decision on Stage 3

The user decides whether the frozen candidate set is strong enough to justify the radar-linkage experiment.

A minimum candidate count may support proceeding, but does not by itself establish readiness or reopen Blocker 2.

## Stage 3 — Multi-site Sentinel-1 radar-linkage demonstration

Status: separate authorization required.

### Goal

Test whether Sentinel-1 measurements contain reproducible information associated with verified observation-date cover depth, rather than only surface or construction differences.

### Experiment rules

- reuse the approved matched Sentinel-1 angle and seasonal workflow;
- apply `docs/DEPTH_CONFOUNDER_CONTROL_SPEC.md`;
- use whole physical sites or large isolated sections;
- keep each physical facility or leakage group together;
- freeze features and preprocessing before final comparison;
- compare depth-bearing models against confounder-only and simple baselines;
- control or stratify incidence angle, season, moisture, vegetation, terrain, construction timing, drainage, and settlement;
- include leave-one-site-out or equivalent site-held-out checks during support research;
- reject candidates whose apparent signal is explained only by recent construction or surface condition;
- do not use the current unknown research site for fitting or threshold selection.

### Required evidence

The analysis must show:

- verified cover-depth variation across independent facilities;
- radar variation associated with that depth after confounder control;
- consistency of effect direction or predictive utility across sites;
- performance beyond frozen confounder-only and simple baselines;
- identified support boundaries and abstention conditions;
- honest failure reporting when the relationship does not generalize.

### Stage-3 decisions

```text
linkage_supported_pending_reopen_review
linkage_not_supported_reject_source_class_for_depth
linkage_inconclusive_more_evidence_required
```

These are experiment outcomes, not replacements for the B6 register states.

If linkage is not supported, affected candidates become `rejected_scale_or_sensor_mismatch` or `method_research_only`, with reasons.

If linkage is supported, candidates may be recommended for `direct_calibration_candidate` review, but no pack intake begins until the formal reopen decision.

## Gate 3 — Formal Blocker 2 reopen decision

Only after Stage 3, the user decides whether Blocker 2 is formally reopened.

A reopen recommendation requires all of the following:

- named public documents from multiple independent facilities;
- traceable depth-to-top and uncertainty;
- observation-date depth supported after settlement review;
- defensible whole-cell or isolated-section Sentinel-1 experiment units;
- at least one viable independently supported negative lane;
- multi-site radar-linkage evidence that survives confounder controls;
- no unresolved privacy, misuse, licensing, or finding-family prohibition;
- a credible path to train, validation, and untouched holdout site groups.

Formal reopening authorizes later register updates and private-pack intake work. It does not solve Blocker 2 and does not authorize training.

## Stage 4 — Register update, private-pack assembly, and validation

Status: separate explicit authorization required after formal reopening.

### Existing tool sequence

```text
scripts/init_depth_calibration_pack.py
→ scripts/add_depth_calibration_record.py --create-template
→ scripts/add_depth_calibration_record.py
→ scripts/add_depth_calibration_record.py --write
→ scripts/validate_depth_calibration_pack.py
→ scripts/finalize_depth_calibration_manifest.py
→ scripts/finalize_depth_calibration_manifest.py --write
→ scripts/validate_depth_calibration_pack.py
```

### Rules

- update the existing candidate register and eligibility matrix rather than creating parallel registers;
- store real records, coordinates, source paths, and site splits outside Git;
- import only contract-eligible positives and independently confirmed negatives;
- keep each facility or leakage group in one split;
- include eligible records in train, validation, and untouched holdout splits;
- keep the holdout untouched and research-eligible;
- do not create rows merely to make a split non-empty;
- keep the current unknown research site excluded from fitting and threshold selection.

### Blocker 2 pass condition

Blocker 2 is solved only when the private calibration pack passes the dataset contract and aggregate validator with eligible positives and negatives in every required split.

```text
blocker_2_solved
= validated_contract_complete_private_pack
```

Only then may relative-depth training begin under the later scientific-validation gates.

## Prohibited shortcuts

Do not:

- infer Sentinel-1 depth sensitivity from document quality or footprint size;
- treat preliminary Sentinel-1 coverage as radar-depth linkage;
- mark R1 or R5 passed during Stage 1 or Stage 2;
- use construction-time depth without observation-date settlement support;
- assume a settlement rate;
- treat one borehole as a confirmed negative area;
- invent uncertainty or depth reference;
- create per-pixel or per-survey-point satellite calibration rows;
- split one facility across train, validation, and holdout;
- promote simulations, notebook outputs, classifier results, PCA values, or anomaly scores into physical truth;
- train a model before the pack passes;
- enable app depth or report a confirmation percentage.

## Verification checklist

### Stage 1

- [ ] named public documents retrieved;
- [ ] candidate rows span multiple independent facilities;
- [ ] depth-to-top source recorded;
- [ ] uncertainty source recorded;
- [ ] survey and construction dates recorded;
- [ ] settlement evidence recorded or marked unresolved;
- [ ] whole-cell scale and mixing screened;
- [ ] preliminary Sentinel-1 coverage checked;
- [ ] negative candidates assessed under the strict footprint rule;
- [ ] R1 and R5 marked `not_tested_pending_stage_3`;
- [ ] chat-only candidate table delivered.

### Stage 2

- [ ] source-specific contract review passes for frozen candidates;
- [ ] observation-date depth is defensible;
- [ ] site and leakage groups are frozen;
- [ ] private analysis footprints and acquisition plans are prepared;
- [ ] candidates remain `evidence_verified_pending_support` pending Stage 3.

### Stage 3

- [ ] multi-site depth variation exists;
- [ ] matched Sentinel-1 workflow is executed consistently;
- [ ] confounders and baselines are tested;
- [ ] site-held-out support is assessed;
- [ ] radar linkage is supported, rejected, or honestly inconclusive.

### Gate 3

- [ ] user explicitly decides whether Blocker 2 is reopened.

### Stage 4

- [ ] existing register and matrix are updated only after authorization;
- [ ] private pack contains eligible positives and negatives;
- [ ] train, validation, and untouched holdout site groups are valid;
- [ ] validator and finalized manifest pass;
- [ ] Blocker 2 is solved only after the validated pack passes.

## Current status after documenting this plan

```text
candidate_source_class_status = candidate_under_review
stage_1_status = not_started
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
formal_reopen_status = not_requested
blocker_2_status = unresolved
calibration_dataset_status = not_populated
depth_training = blocked
app_depth_enabled = false
```
