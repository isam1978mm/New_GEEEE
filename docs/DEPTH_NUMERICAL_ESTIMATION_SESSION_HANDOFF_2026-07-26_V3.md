# Numerical Depth Estimation — Session Handoff V3 — 2026-07-26

**Repository:** `max2026-lab/New_GEE`  
**Branch:** `main`  
**Goal:** unlock honest numerical depth estimation using independent, measured, mapped calibration evidence  
**Current usable calibration rows:** `0`  
**Numerical depth training ready:** no  
**App numerical depth enabled:** no

---

## 1. Read this first

The project still cannot honestly output numerical depth in metres.

The research has found several strong engineering-evidence leads, but none yet satisfies every required field:

1. actual measured physical depth or a source-provided finite interval;
2. exact mapped target geometry;
3. numerical measurement or survey uncertainty;
4. construction/reference date;
5. an unchanged Sentinel-1 observation interval;
6. independently confirmed negative/background evidence;
7. independent train, validation, and holdout site groups.

Current readiness remains:

```text
usable_positive_records = 0
usable_confirmed_negative_records = 0
calibration_records_created = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

Do not claim that depth works. Do not start model training. Do not enable depth in the app.

---

## 2. Exact point reached

The last completed candidate was **Strasburg Landfill**.

Strasburg was closed because its public records provide an engineered cap and continuing protection, but only design-layer values—not mapped accepted measurements or numerical tolerance. The cap also contains gas/leachate infrastructure and continuing operations and maintenance.

Document:

`docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

Commit:

`8604342 docs: close Strasburg design-only cap route`

### Exact resume point

Resume with **Dorney Road Landfill**.

The next session should screen the EPA cap-focused record collection for:

- a completed post-construction or final remedial-action report;
- actual measured final-cover thicknesses, not design requirements;
- mapped measurement points or survey-controlled polygons;
- survey datum and numerical accuracy/tolerance;
- later repairs, wetlands work, gas systems, roads, drainage, monitoring, or other surface disturbance;
- a stable Sentinel-1 interval for any surviving simple subarea.

Do not create a Dorney document until the candidate has a decisive promote/hold/reject result.

---

## 3. How we worked

Continue the same evidence-first method.

### User-facing working style

- The user normally says `go`, `continue`, or `proceed`; continue autonomously.
- Keep updates brief and plain.
- Every progress update should state:
  - current status;
  - next step.
- Do not ask permission between search steps.
- Do not ask the user to email agencies or manually retrieve records.
- When a route closes, explain why in one short sentence, document it, commit it, and move on.

### Research workflow

1. Start with one named facility and one exact missing record.
2. Prefer official regulator, utility, certified engineering, survey, construction-quality, final-closure, as-built, or inspection records.
3. Search for the completed evidence package, not merely the permit or design plan.
4. Separate these evidence types:
   - planned/design thickness;
   - regulatory minimum;
   - constructed minimum;
   - actual measured point depth;
   - source-provided bounded interval;
   - construction tolerance;
   - survey accuracy;
   - exact target geometry;
   - approximate outline;
   - parcel/covenant boundary;
   - independently confirmed negative area.
5. Check what happened to the surface after the measurement.
6. Reject or exclude surfaces affected by redevelopment, roads, buildings, wetlands, stormwater use, landfill expansion, active gas systems, drainage work, repeated settlement repair, major vegetation conversion, or other construction.
7. For PDF figures, tables, drawings, maps, and scanned forms, visually render or screenshot the relevant page.
8. Never claim an unseen drawing was inspected.
9. Never infer coordinates, thickness values, failed/re-certified pit status, datum, or accuracy from OCR gaps.
10. Record exact private geometry only outside Git; repository documents must not contain raw target coordinates.
11. Document meaningful promote/hold/reject decisions immediately on `main`.
12. Do not weaken the calibration contract or validator to make a candidate pass.

### Stop rules for a candidate

Stop and reject/hold when:

- only design thickness is available;
- only an average is available;
- only a one-sided lower bound is available;
- the point table or map is known to exist but cannot be extracted;
- numerical uncertainty is missing;
- the surface was rebuilt or disturbed after measurement;
- exact geometry is replaced by a parcel, covenant, or approximate boundary;
- the measurement endpoint is ambiguous;
- an unchanged Sentinel-1 interval cannot be proved.

---

## 4. Governing evidence gate

Read and obey:

`docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`

The contract requires, for a positive record:

- finite `known_depth_top_m`;
- required `depth_reference_uncertainty_m`, unless the source explicitly gives a finite bounded interval;
- independent evidence, not app/notebook signals;
- traceable source and review method;
- stable site/feature/group identifiers;
- observation dates and sensor linkage;
- no leakage across train, validation, and holdout.

Important prohibitions:

- no app or notebook prediction as truth;
- no PCA anomaly, classifier probability, target mask, simulated layer, or generated depth label as truth;
- no design minimum substituted for actual depth;
- no landfill-wide average assigned to a point or Sentinel-1 pixel;
- no decimal display precision treated as measurement accuracy;
- no site/group reuse between dataset splits.

---

## 5. Current strongest candidates

### 5.1 River Road Landfill — strongest post-construction certification-pit package

Primary document:

`docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`

Confirmed:

- 129 physical final-cover certification pits;
- approximately two pits per acre;
- pit locations were surveyed;
- Appendix A records final cover thickness for each pit;
- deficient areas were corrected and re-certified;
- professional engineering and surveying certification;
- long-term inactive and protected surface.

Still missing:

- individual final accepted pit values;
- original failure versus final re-certification status;
- Sheet 1 point locations;
- CRS and datum;
- numerical measurement and survey uncertainty;
- exact disturbance/maintenance overlay;
- point-specific unchanged Sentinel-1 interval.

Critical EPA source key:

```text
EPA NEPIS document = 91025HWW
embedded package = 1987 Closure Certification and Post-Closure Plan
```

Do not use the certified three-foot minimum as a point label.

Do not treat Table 1 or Table 2 as depth tables; they contain soil textural/nutrient composite results.

Do not repeat the exhausted broad access searches unless a new archive or document identifier appears.

Required River Road reading:

- `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
- `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
- `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`

Latest River Road commits:

- `3bcd25c docs: record River Road surveyed pit candidate`
- `d8b3fcb docs: record River Road appendix access blocker`
- `5d89099 docs: record River Road Appendix A extraction window`
- `d575eaf docs: add River Road OCR survey-control evidence`
- `b8f75c5 docs: correct River Road OCR page mapping`
- `2a302db docs: record exhausted River Road public access routes`

Correct future extraction anchors:

```text
APPENDIX A — FIELD REPORTS
Todd Giddings and Associates field-report form
FINAL COVER CERTIFICATION — Sheet 1 of 3
EPA document key 91025HWW
```

### 5.2 J.R. Whiting Ponds 1 and 2 — strongest already extracted mapped depth values

Document:

`docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`

Confirmed:

- 107 mapped construction-record depth values;
- control points 1000–1106;
- approximately 0.619–0.762 m measured cover range;
- subgrade and final topsoil elevations;
- 100-foot survey grid;
- NGVD29 vertical datum;
- licensed construction-record survey.

Still missing:

- numerical vertical accuracy;
- independently confirmed negative area;
- verified unchanged Sentinel-1 interval;
- final visual verification of the official record table;
- independent validation and holdout sites.

This remains the strongest lead where the numerical point values themselves have already been recovered.

### 5.3 John Sevier Bottom Ash Pond — strongest measured placed-cover narrative

Document:

`docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`

Confirmed:

- final 24 inches of cover soil was placed above the eastern geomembrane cap;
- closure completed in 2017;
- annual inspection history through 2026;
- repeated no-geometry-change findings;
- very small recent settlement readings.

Still missing:

- exact surveyed cap polygon;
- local measured thickness range or finite interval;
- construction tolerance;
- survey accuracy;
- stable subarea excluding instruments, roads, drainage, wells, burrows, and maintenance.

### 5.4 Auburn McMaster Street — strongest vacant gravel-cover lead

Document:

`docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`

Confirmed:

- licensed construction surveys;
- Appendix A states actual soil-cover thickness is shown;
- reuse material placed more than two feet below final grade;
- geotextile demarcation layer;
- compacted-gravel vacant surface;
- cover intact through May 2025;
- legal parcel metes-and-bounds survey.

Still missing:

- readable as-built local depth labels;
- exact reuse-material subarea polygons;
- datum and survey accuracy;
- finite depth interval;
- simple stable gravel subareas excluding wells, utilities, streambank/ecological work, and recovery systems.

Important: `> 0.6096 m` is a one-sided lower bound and is not an eligible depth label.

### 5.5 Berks Landfill — strongest pre-remedy measured-point subset

Document:

`docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`

Confirmed:

- direct excavation/auger cap-thickness measurements;
- multiple eastern and western point campaigns;
- field endpoint was refuse or auger refusal;
- potentially preserved forested western subset;
- construction verification and long-term review history;
- correct EPA remedial collection is Region 3 collection 206.

Still missing:

- point field table;
- point map, CRS, and datum;
- field-method uncertainty;
- exact overlay of forest, trails, roads, drainage, monitoring, construction, and repairs;
- retrievable July 2, 2025 five-year review;
- unchanged point-specific Sentinel-1 interval.

Do not use the reported western/eastern averages as point labels.

### 5.6 Sconondoa Street former MGP — strongest surveyed-excavation lead

Document:

`docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`

Confirmed:

- licensed surveyor;
- 15- or 20-foot survey grids;
- excavation depths approximately 5–20 feet;
- post-construction topographic surveys;
- largely vacant post-remediation setting.

Still missing:

- survey appendix extraction;
- exact cell polygons and elevations;
- numerical survey uncertainty;
- simple stable subcells excluding asphalt, riprap, utilities, structures, wells, and gas-regulator infrastructure.

### 5.7 Plant Kraft AP-1 — strongest clean-removal geometry-pending lead

Document:

`docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`

Confirmed:

- physical CCR removal;
- post-excavation topographic mapping;
- excavation-limit drawing;
- Georgia East Zone, NAD83;
- survey/engineering firm identified.

Still missing:

- readable coordinate-bearing map pages;
- exact AP-1 polygon;
- boundary uncertainty;
- clean unchanged interval before port redevelopment.

Do not substitute the parcel or covenant boundary for the AP-1 excavation limit.

---

## 6. New routes closed during this session

Read these before revisiting any site.

### EPA landfill-cap routes

- `docs/DEPTH_HELEVA_LANDFILL_HISTORICAL_CLAY_CAP_FOLLOWUP_2026-07-25.md`  
  Historical two-foot clay statement predates the later engineered cap; no final point measurements or uncertainty.

- `docs/DEPTH_EAST_MOUNT_ZION_ECOLOGICAL_REVITALIZATION_FOLLOWUP_2026-07-25.md`  
  Meadow conversion, mowing, replanting, shrubs, gas vents, and animal burrows make the surface dynamic.

- `docs/DEPTH_KEYSTONE_SANITATION_DYNAMIC_COVER_FOLLOWUP_2026-07-25.md`  
  Repeated subsidence, ponding, repairs, monitoring, and pending cover changes.

- `docs/DEPTH_WEST_KL_AVENUE_ACTIVE_CAP_SYSTEM_FOLLOWUP_2026-07-25.md`  
  Active multilayer cap with extraction trenches, wells, flare system, and continuing maintenance; no readable point table.

- `docs/DEPTH_HIMCO_DUMP_PRE_REMEDY_TEST_PITS_FOLLOWUP_2026-07-25.md`  
  Twenty-four direct measurements predated later regrading, revegetation, and gas-system construction.

- `docs/DEPTH_FORT_WAYNE_REDUCTION_PRE_REMEDY_GRID_FOLLOWUP_2026-07-25.md`  
  Thirty-six grid measurements predated excavation, regrading, cap construction, slurry wall, and collection systems.

- `docs/DEPTH_MODERN_SANITATION_ACTIVE_LANDFILL_DISTURBANCE_CLOSURE_2026-07-26.md`  
  Active landfill context; trucks crossed the cap, disturbed areas were reseeded, settlement was filled, and later cells overlie part of the cap.

- `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`  
  Design values only; gas/leachate infrastructure and continuing O&M.

### Other completed/engineered-cover routes

- `docs/DEPTH_GARRETT_DALTON_FOUNDRY_REQUIRED_BUT_REDEVELOPED_CLOSURE_2026-07-26.md`  
  Order required future measurements, but no completed package was found and the property was renovated for school use.

- `docs/DEPTH_BOONE_COUNTY_TEST_CELL_HISTORICAL_ONLY_CLOSURE_2026-07-26.md`  
  Physically confirmed 0.6 m cover, but the test cell was dismantled in September 1980.

- `docs/DEPTH_LOPEZ_CANYON_ACTIVE_POSTCLOSURE_USE_CLOSURE_2026-07-26.md`  
  Large engineered cover, but heliport, microturbines, flare, municipal fleet/mulching operations, and no point-specific as-built measurements.

- `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`  
  Design minimums only; changing forest, mowing, replanting, vents, wells, monitoring devices, and access paths.

### Commits for these closures

```text
e43e909  close Heleva historical clay-cap route
2015bb6  close East Mount Zion revitalization route
2034ec7  close Keystone dynamic cover route
5cd0001  close West KL active cap route
1940024  close Himco pre-remedy pit route
994ab72  close Fort Wayne pre-remedy grid route
5a92a77  close redeveloped Garrett Dalton route
be1c037  close historical Boone test cell route
6a61b0a  close active Lopez Canyon route
3fa3987  close dynamic Walsh ET cover route
69d8cc2  close active Modern Sanitation route
8604342  close Strasburg design-only cap route
```

Do not revisit these routes unless a new final as-built point table, exact mapped geometry, numerical uncertainty source, or decisive stable-surface evidence appears.

---

## 7. Earlier routes that remain closed or evidence-only

### Strong physical removal but missing exact geometry

- `docs/DEPTH_JC_WEADOCK_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_JH_CAMPBELL_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_JH_CAMPBELL_EXACT_BOUNDARY_FOLLOWUP_2026-07-25.md`

### CCR/removal routes closed by reuse or changed surface

- `docs/DEPTH_POSSUM_POINT_REMOVAL_BOUNDARY_TIMING_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_MT_STORM_REMOVAL_AND_SURFACE_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GRAINGER_WETLAND_REMOVAL_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_DALE_CLEAN_CLOSURE_SURVEY_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_EMERY_POND_ENGINEERED_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_WINYAH_REMOVAL_AND_SURFACE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_CROSS_GYPSUM_CONFIRMED_REMOVAL_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_ARKEMA_PIFFARD_EXCAVATION_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_PHOTECH_EXCAVATION_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_COLESVILLE_EXCAVATION_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_CLOTHIER_EXCAVATION_FOLLOWUP_2026-07-25.md`

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

Key decisions:

- Elk Plain: mapped values, but no numerical survey accuracy or confirmed negative.
- Sudbury: numerical construction controls, but no extracted final mapped surface.
- Go East: physically checked empty-area leads and constructed cover, but unextracted boundaries and major construction confounding.
- Recomp: old cover buried under new engineered construction.
- RAMCO: no numerical installed thickness/accuracy.
- Triune: completion report unavailable and no numerical evidence.

---

## 8. Documents the next session must read — in order

### Read first: current status and contract

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V3.md`
2. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
3. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25_V2.md`
4. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md`
5. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
6. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
7. `scripts/validate_depth_calibration_pack.py`
8. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md`

### Read next: strongest current leads

9. `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
10. `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
11. `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
12. `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
13. `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`
14. `docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`
15. `docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`
16. `docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`
17. `docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`
18. `docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`
19. `docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`

### Read before revisiting recent rejections

20. `docs/DEPTH_HELEVA_LANDFILL_HISTORICAL_CLAY_CAP_FOLLOWUP_2026-07-25.md`
21. `docs/DEPTH_EAST_MOUNT_ZION_ECOLOGICAL_REVITALIZATION_FOLLOWUP_2026-07-25.md`
22. `docs/DEPTH_KEYSTONE_SANITATION_DYNAMIC_COVER_FOLLOWUP_2026-07-25.md`
23. `docs/DEPTH_WEST_KL_AVENUE_ACTIVE_CAP_SYSTEM_FOLLOWUP_2026-07-25.md`
24. `docs/DEPTH_HIMCO_DUMP_PRE_REMEDY_TEST_PITS_FOLLOWUP_2026-07-25.md`
25. `docs/DEPTH_FORT_WAYNE_REDUCTION_PRE_REMEDY_GRID_FOLLOWUP_2026-07-25.md`
26. `docs/DEPTH_GARRETT_DALTON_FOUNDRY_REQUIRED_BUT_REDEVELOPED_CLOSURE_2026-07-26.md`
27. `docs/DEPTH_BOONE_COUNTY_TEST_CELL_HISTORICAL_ONLY_CLOSURE_2026-07-26.md`
28. `docs/DEPTH_LOPEZ_CANYON_ACTIVE_POSTCLOSURE_USE_CLOSURE_2026-07-26.md`
29. `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`
30. `docs/DEPTH_MODERN_SANITATION_ACTIVE_LANDFILL_DISTURBANCE_CLOSURE_2026-07-26.md`
31. `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

### Read for the earlier evidence history

32. `docs/DEPTH_JC_WEADOCK_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
33. `docs/DEPTH_JH_CAMPBELL_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
34. `docs/DEPTH_JH_CAMPBELL_EXACT_BOUNDARY_FOLLOWUP_2026-07-25.md`
35. `docs/DEPTH_POSSUM_POINT_REMOVAL_BOUNDARY_TIMING_FOLLOWUP_2026-07-25.md`
36. `docs/DEPTH_MT_STORM_REMOVAL_AND_SURFACE_REUSE_FOLLOWUP_2026-07-25.md`
37. `docs/DEPTH_GRAINGER_WETLAND_REMOVAL_FOLLOWUP_2026-07-25.md`
38. `docs/DEPTH_DALE_CLEAN_CLOSURE_SURVEY_FOLLOWUP_2026-07-25.md`
39. `docs/DEPTH_EMERY_POND_ENGINEERED_REUSE_FOLLOWUP_2026-07-25.md`
40. `docs/DEPTH_THREE_SITE_BOUNDED_FOLLOWUP_2026-07-25.md`
41. `docs/DEPTH_ELK_PLAIN_SURVEY_ACCURACY_FOLLOWUP_2026-07-25.md`
42. `docs/DEPTH_SUDBURY_REPORT_64264_FINAL_PUBLIC_RECOVERY_2026-07-25.md`
43. `docs/DEPTH_RECOMP_AS_BUILT_FOLLOWUP_2026-07-25.md`
44. `docs/DEPTH_RAMCO_AS_BUILT_FOLLOWUP_2026-07-25.md`
45. `docs/DEPTH_TRIUNE_COMPLETION_REPORT_FOLLOWUP_2026-07-25.md`
46. `docs/DEPTH_GO_EAST_NEGATIVE_EVIDENCE_UPDATE_2026-07-25.md`
47. `docs/DEPTH_GO_EAST_CONFIRMED_NEGATIVE_EVIDENCE_2026-07-25.md`
48. `docs/DEPTH_SUDBURY_NUMERICAL_CONTROL_EVIDENCE_UPDATE_2026-07-25.md`
49. `docs/DEPTH_PUBLIC_ENGINEERING_PACKAGE_SCREEN_2026-07-24.md`

### Method-test and implementation context

50. `docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md`
51. `docs/DEPTH_BUTO_METHOD_TEST_EXECUTION_PLAN_2026-07-24.md`
52. `scripts/run_buto_s1_method_screen.py`
53. `tests/unit/test_buto_s1_method_screen.py`
54. `docs/DEPTH_FEATURE_INVENTORY.md`

### Supplied non-repository files

55. `notebook phases.md`
56. `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb`

Important conclusions from the supplied files:

- The original notebook is useful as implementation history and phase inventory.
- Its depth, treasure, material, danger, or target labels are heuristic/proxy outputs and are not independent calibration truth.
- The candidate-scout notebook creates lawful paid-imagery request zones and quote comparisons.
- The candidate-scout notebook does not provide depth calibration evidence and should not be used to populate the depth dataset.

---

## 9. Immediate next steps

### Step 1 — Screen Dorney Road Landfill

Search the cap-focused EPA collection for:

```text
final remedial action report
construction completion report
as-built cap drawings
construction quality assurance report
cover-thickness verification
survey tables
northing/easting points
post-construction inspection history
```

Decision order:

1. Does a completed report exist?
2. Does it give actual measured thickness, not design minimums?
3. Are measurements mapped to points or polygons?
4. Is numerical uncertainty stated or source-bounded?
5. Did wetlands, gas systems, roads, drainage, monitoring, erosion, settlement, or repairs disturb the surface?
6. Is any simple subarea unchanged during Sentinel-1 years?

If no, document and close immediately.

### Step 2 — Keep River Road open only for a genuinely new access route

Do not repeat the already exhausted broad searches.

Resume River Road only if one of these appears:

- a direct page-image rendition of `91025HWW`;
- a separately scanned 1987 closure package;
- a new EPA/Pennsylvania document ID;
- a downloadable `APPENDIX A — FIELD REPORTS`;
- `FINAL COVER CERTIFICATION — Sheet 1 of 3`.

### Step 3 — Focused recovery paths for existing strong leads

#### J.R. Whiting

Search only for:

- ROWE survey-control notes;
- numerical vertical accuracy;
- instrument/equipment specification tied to the record survey;
- stable post-closure interval;
- confirmed CCR-free comparison area.

#### Auburn McMaster

Search only for:

- Appendix A as-built soil-cover thickness sheets;
- CQA plan survey tolerances;
- exact simple gravel target subareas;
- final surface/demarcation elevations;
- stable post-2018 interval.

#### John Sevier

Search only for:

- final construction as-built cap drawing;
- measured thickness range or accepted interval;
- project-specific tolerance;
- exact eastern cap polygon;
- Final Cover System Integrity Studies.

#### Berks

Search only for:

- Region 3 collection 206 field table and point map;
- March 1995 RI volumes;
- 1997 topographic plan;
- 1999 final design drawings;
- July 2001 completion report;
- July 2025 five-year review;
- forested-western disturbance overlay.

#### Sconondoa

Search only for:

- final engineering report survey appendix;
- exact excavation cells and elevations;
- survey accuracy/tolerance;
- stable simple subcell.

### Step 4 — Create the first record only when complete

For one complete candidate:

```text
extract private geometry
→ create private candidate row
→ populate depth, uncertainty, evidence, dates, and stability
→ run scripts/validate_depth_calibration_pack.py
→ record every failure
→ do not weaken the validator
```

### Step 5 — Build independent groups

One passing row does not unlock training.

Need at minimum independent site groups for:

```text
training
validation
holdout
```

No physical site or local group may cross splits.

---

## 10. Short roadmaps

### Roadmap A — Resume next session

```text
read V3 handoff
→ read contract
→ screen Dorney Road completion/CQA records
→ promote, hold, or reject
→ document and commit
→ continue to next named cap collection
```

### Roadmap B — First usable positive record

```text
actual mapped depth values
→ exact geometry
→ numerical uncertainty
→ unchanged Sentinel-1 interval
→ private record
→ validator pass
```

### Roadmap C — First confirmed negative record

```text
physical removal or independently verified no-target condition
→ exact final survey boundary
→ boundary uncertainty
→ dry/simple unchanged surface
→ private negative record
→ validator pass
```

### Roadmap D — Dataset readiness

```text
complete site group 1
→ complete independent site group 2
→ complete independent site group 3
→ train / validation / holdout assignment
→ no group leakage
→ validator passes
```

### Roadmap E — Numerical-depth research

```text
validated dataset
→ matched Sentinel-1 features
→ correlation/model test
→ separate-site validation
→ untouched holdout test
→ measured error and failure range
```

### Roadmap F — App unlock

```text
repeatable holdout performance
→ architecture gate review
→ honest uncertainty and supported-range display
→ enable numerical depth only inside validated conditions
```

---

## 11. Hard rules

Do not:

- claim numerical depth is working;
- train a depth model now;
- enable depth in the app;
- invent or estimate calibration values;
- create placeholder rows;
- use design thickness as measured truth;
- use a minimum or lower bound as a point value;
- use a site average as a local depth;
- use approximate map geometry;
- substitute parcel/covenant boundaries for target geometry;
- infer unseen figures, handwritten values, CRS, or uncertainty;
- use app/notebook signals as independent labels;
- ignore later surface disturbance;
- reuse one site/group across splits;
- expose exact private target coordinates in repository documents;
- repeat exhausted River Road access searches without new evidence.

---

## 12. Final handoff statement

The search has made real progress, but it has not unlocked numerical depth.

The strongest already extracted mapped-depth lead is **J.R. Whiting**. The strongest post-construction certification-pit package is **River Road**, but its 129 individual values and survey sheet remain image-only and numerical uncertainty is missing. **John Sevier**, **Auburn McMaster**, **Berks**, **Sconondoa**, and **Plant Kraft** remain focused secondary leads with clearly defined missing records.

The exact next action is to screen **Dorney Road Landfill** for a completed, readable construction-verification package containing actual measured final-cover thicknesses, mapped points, numerical uncertainty, and a stable surviving surface.

```text
usable_calibration_rows = 0
numerical_depth_ready = no
next_candidate = Dorney_Road_Landfill
next_required_record = post_construction_measured_cover_table_and_map
```
