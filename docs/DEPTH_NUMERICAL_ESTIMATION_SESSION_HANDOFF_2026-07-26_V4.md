# Numerical Depth Estimation — Corrected Session Handoff V4 — 2026-07-26

**Read this document first.**  
**Repository:** `max2026-lab/New_GEE`  
**Branch:** `main`  
**Goal:** unlock honest numerical depth estimation using independent measured and mapped calibration evidence  
**Usable calibration rows:** `0`  
**Numerical depth ready:** no  
**App depth enabled:** no

This V4 is the canonical handoff. It supersedes the required-reading/path list in V3. V3 remains useful for the detailed narrative:

`docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V3.md`

---

## 1. Current truth

The app cannot honestly produce numerical depth in metres yet.

No candidate currently has every required item:

- actual physical depth or source-provided finite interval;
- exact target geometry;
- numerical measurement/survey uncertainty;
- reference and construction dates;
- unchanged Sentinel-1 observation interval;
- independently confirmed negative/background evidence;
- independent train, validation, and holdout site groups.

```text
usable_positive_records = 0
usable_confirmed_negative_records = 0
calibration_records_created = 0
training_ready = no
numerical_depth_ready = no
app_depth_enabled = no
```

Do not claim depth works. Do not train. Do not enable depth.

---

## 2. Exact stopping point

The last completed screen was **Strasburg Landfill**.

Result: closed because the public record contains design-layer values rather than mapped accepted measurements or numerical tolerance, and the cap has gas/leachate infrastructure with continuing operations and maintenance.

Document:

`docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

Commit:

`8604342 docs: close Strasburg design-only cap route`

### Resume here

Screen **Dorney Road Landfill** next.

Look only for:

- completed remedial-action/construction report;
- actual post-construction cover-thickness measurements;
- mapped measurement points or survey-controlled polygons;
- CRS, datum, and numerical accuracy/tolerance;
- final accepted values rather than design minimums;
- later wetlands, gas, road, drainage, monitoring, erosion, settlement, or repair disturbance;
- a surviving simple unchanged Sentinel-1 subarea.

If these are not present, document one concise rejection, commit it, and move on.

---

## 3. Way of working

The user normally says `go`, `continue`, or `proceed`. Continue autonomously.

Every short update should state:

- current status;
- next step.

Research rules:

1. Start from one named facility and one exact missing record.
2. Prefer official regulator, utility, engineering, survey, as-built, closure, CQA, and inspection documents.
3. Search for completed evidence, not merely permits or plans.
4. Separate design minimums from actual measured point depths.
5. Separate construction tolerance from survey accuracy and total uncertainty.
6. Reject averages, one-sided lower bounds, and approximate boundaries as calibration labels.
7. Check whether the measured surface was later rebuilt, repaired, redeveloped, planted, trenched, driven over, or otherwise changed.
8. Visually render PDF maps, figures, forms, and tables before using them.
9. Never claim an unseen figure was inspected.
10. Never infer coordinates, depths, re-certification status, datum, or uncertainty from OCR gaps.
11. Keep exact target coordinates private and out of Git.
12. Document each decisive promote/hold/reject result on `main`.
13. Do not ask the user to email agencies or manually retrieve files.
14. Do not weaken the contract or validator.

When a route closes:

```text
one-sentence reason
→ create/update concise doc
→ commit to main
→ move to next named candidate
```

---

## 4. Governing contract

Read:

`docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`

A positive record requires finite `known_depth_top_m` and `depth_reference_uncertainty_m`, unless the source explicitly provides a finite bounded interval.

The evidence must be independent of the app/notebook signal pipeline.

Never use as truth:

- notebook depth labels;
- PCA anomaly values;
- classifier outputs;
- target masks;
- simulated or generated layers;
- analyst guesses;
- design minimums;
- site-wide averages.

No physical site/group may cross training, validation, and holdout.

---

## 5. Strongest open leads

### River Road Landfill

Role: strongest post-construction certification-pit package.

Confirmed:

- 129 final-cover certification pits;
- surveyed pit locations;
- individual final thicknesses recorded in Appendix A;
- deficient areas corrected and re-certified;
- inactive protected surface.

Missing:

- actual accepted pit values;
- failure versus re-certification status;
- Sheet 1 locations;
- CRS/datum;
- numerical uncertainty;
- point disturbance overlay;
- unchanged Sentinel-1 interval.

Do not use the three-foot minimum as a point value. Do not use soil Tables 1–2 as depth.

Critical source:

```text
EPA NEPIS key = 91025HWW
```

Only resume River Road when a genuinely new page-image or document identifier appears. Broad access routes are exhausted.

Required River Road docs:

- `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
- `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`

### J.R. Whiting

Role: strongest lead with already recovered mapped numerical values.

- 107 mapped measured cover values;
- approximately `0.619–0.762 m`;
- 100-foot survey grid;
- NGVD29;
- licensed construction-record survey.

Missing vertical survey accuracy, confirmed negative, unchanged interval, and independent validation/holdout groups.

Document:

`docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`

### John Sevier Bottom Ash Pond

Role: strongest placed-cover narrative with stable inspection history.

- actual 24-inch layer placement confirmed;
- closure in 2017;
- inspections through 2026;
- repeated no-geometry-change findings.

Missing exact cap polygon, local thickness interval, tolerance, survey accuracy, and clean subarea exclusions.

Document:

`docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`

### Auburn McMaster Street

Role: strongest vacant compacted-gravel cover lead.

- licensed construction surveying;
- actual local cover thickness confirmed to exist in Appendix A;
- reuse material more than two feet below grade;
- vacant stable gravel surface through May 2025.

Missing readable as-built values, target subarea geometry, datum, survey uncertainty, and finite depth interval.

`> 0.6096 m` is only a lower bound and cannot become a row.

Document:

`docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`

### Berks Landfill

Role: strongest pre-remedy measured-point subset.

- direct hand-excavation/auger measurements;
- potentially preserved forested western subset;
- correct EPA remedial collection is Region 3 collection 206.

Missing field table, point map, CRS, uncertainty, disturbance overlay, 2025 review, and unchanged point interval.

Do not use eastern/western averages as point labels.

Document:

`docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`

### Sconondoa Street former MGP

Role: strongest surveyed-excavation lead.

- licensed surveyor;
- 15/20-foot grids;
- excavation depths about 5–20 feet;
- final topographic surveys;
- largely vacant setting.

Missing survey appendix, exact cells/elevations, uncertainty, and stable simple subcell.

Document:

`docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`

### Plant Kraft AP-1

Role: strongest clean-removal geometry-pending lead.

- physical removal confirmed;
- post-excavation map and excavation-limit drawing exist;
- Georgia East Zone, NAD83.

Missing readable exact polygon, boundary uncertainty, and clean interval before redevelopment.

Do not substitute parcel/covenant geometry.

Document:

`docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`

---

## 6. Recent routes closed

Read before revisiting:

- `docs/DEPTH_HELEVA_LANDFILL_HISTORICAL_CLAY_CAP_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_EAST_MOUNT_ZION_ECOLOGICAL_REVITALIZATION_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_KEYSTONE_SANITATION_DYNAMIC_COVER_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_WEST_KL_AVENUE_ACTIVE_CAP_SYSTEM_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_HIMCO_DUMP_PRE_REMEDY_TEST_PITS_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_FORT_WAYNE_REDUCTION_PRE_REMEDY_GRID_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GARRETT_DALTON_FOUNDRY_REQUIRED_BUT_REDEVELOPED_CLOSURE_2026-07-26.md`
- `docs/DEPTH_BOONE_COUNTY_TEST_CELL_HISTORICAL_ONLY_CLOSURE_2026-07-26.md`
- `docs/DEPTH_LOPEZ_CANYON_ACTIVE_POSTCLOSURE_USE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`
- `docs/DEPTH_MODERN_SANITATION_ACTIVE_LANDFILL_DISTURBANCE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

Recent closure commits:

```text
e43e909 Heleva
2015bb6 East Mount Zion
2034ec7 Keystone
5cd0001 West KL Avenue
1940024 Himco
994ab72 Fort Wayne Reduction
5a92a77 Garrett/Dalton
be1c037 Boone County test cell
6a61b0a Lopez Canyon
3fa3987 Walsh
69d8cc2 Modern Sanitation
8604342 Strasburg
```

---

## 7. Earlier closed/evidence-only routes

### Strong physical removal; exact geometry missing

- `docs/DEPTH_JC_WEADOCK_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_JH_CAMPBELL_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_JH_CAMPBELL_EXACT_BOUNDARY_FOLLOWUP_2026-07-25.md`

### Closed CCR/removal and changed-surface routes

- `docs/DEPTH_POSSUM_POINT_REMOVAL_BOUNDARY_TIMING_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_MT_STORM_REMOVAL_AND_SURFACE_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GRAINGER_WETLAND_REMOVAL_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_DALE_CLEAN_CLOSURE_SURVEY_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_EMERY_POND_ENGINEERED_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_WINYAH_REMOVAL_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_CROSS_GYPSUM_POND_ACTIVE_SITE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_ARKEMA_PIFFARD_CLEAN_CLOSURE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_PHOTECH_REDEVELOPMENT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_COLESVILLE_DYNAMIC_CAP_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_CLOTHIER_ACTIVE_REUSE_FOLLOWUP_2026-07-25.md`

### Original landfill-package screen

- `docs/DEPTH_THREE_SITE_BOUNDED_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_ELK_PLAIN_SURVEY_ACCURACY_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_SUDBURY_REPORT_64264_FINAL_PUBLIC_RECOVERY_2026-07-25.md`
- `docs/DEPTH_RECOMP_AS_BUILT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_RAMCO_AS_BUILT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_TRIUNE_COMPLETION_REPORT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GO_EAST_NEGATIVE_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_GO_EAST_CONFIRMED_NEGATIVE_EVIDENCE_2026-07-25.md`
- `docs/DEPTH_SUDBURY_NUMERICAL_CONTROL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_PUBLIC_ENGINEERING_PACKAGE_SCREEN_2026-07-24.md`

---

## 8. Required reading order

### First

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V4.md`
2. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
3. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V3.md`
4. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25_V2.md`
5. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md`
6. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
7. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
8. `scripts/validate_depth_calibration_pack.py`
9. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md`

### Current lead packages

10. all five River Road documents listed in section 5;
11. `docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`;
12. `docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`;
13. `docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`;
14. `docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`;
15. `docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`;
16. `docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`.

### Before repeating old searches

17. all recent rejection documents in section 6;
18. all earlier closed/evidence-only documents in section 7.

### Method and implementation context

19. `docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md`
20. `docs/DEPTH_BUTO_METHOD_TEST_EXECUTION_PLAN_2026-07-24.md`
21. `scripts/run_buto_s1_method_screen.py`
22. `tests/unit/test_buto_s1_method_screen.py`
23. `docs/DEPTH_FEATURE_INVENTORY.md`

### Supplied files

24. `notebook phases.md`
25. `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb`

The original notebook is implementation history only. Its depth, treasure, danger, material, target, classifier, PCA, or simulated outputs are not calibration truth.

The candidate-scout notebook creates lawful imagery request zones and quote comparisons. It does not provide depth evidence.

---

## 9. Immediate roadmap

### Resume

```text
read V4
→ read contract
→ screen Dorney Road completed CQA/as-built records
→ decide promote / hold / reject
→ document and commit
```

### Existing positive lead

```text
mapped measured depth
→ exact geometry
→ numerical uncertainty
→ unchanged Sentinel-1 interval
→ private row
→ validator
```

### Confirmed negative lead

```text
physical removal or verified no-target
→ exact final survey
→ boundary uncertainty
→ dry simple unchanged surface
→ private negative row
→ validator
```

### Dataset readiness

```text
independent site group 1
→ independent group 2
→ independent group 3
→ train / validation / holdout
→ no leakage
→ validator pass
```

### Numerical research and app unlock

```text
validated dataset
→ matched Sentinel-1 features
→ separate-site validation
→ untouched holdout
→ measured error range
→ architecture review
→ uncertainty display
→ limited depth enablement
```

---

## 10. Hard rules

Do not:

- claim numerical depth works;
- train now;
- enable app depth;
- invent rows or uncertainty;
- use design values, averages, or lower bounds as point depth;
- use approximate or parcel geometry;
- infer unseen PDF content;
- use app/notebook outputs as independent truth;
- ignore later disturbance;
- expose private target coordinates;
- reuse groups across splits;
- repeat exhausted River Road searches without a new identifier.

---

## 11. Final handoff statement

The research has made meaningful progress but has not unlocked numerical depth.

- Strongest recovered mapped values: **J.R. Whiting**.
- Strongest post-construction pit package: **River Road**.
- Strongest stable placed-cover narrative: **John Sevier**.
- Strongest vacant gravel lead: **Auburn McMaster**.
- Strongest preserved pre-remedy point subset: **Berks western forest**.
- Strongest surveyed excavation: **Sconondoa**.
- Strongest removal geometry-pending lead: **Plant Kraft**.

The exact next action is **Dorney Road Landfill**: recover a readable completed construction-verification package with actual mapped final-cover measurements and numerical uncertainty, or close the route quickly.

```text
usable_calibration_rows = 0
numerical_depth_ready = no
next_candidate = Dorney_Road_Landfill
```
