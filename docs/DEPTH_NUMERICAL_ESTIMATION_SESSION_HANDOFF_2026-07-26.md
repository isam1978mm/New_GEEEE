# Numerical Depth Estimation — Session Handoff — 2026-07-26

**Branch:** `main`  
**Repository:** `max2026-lab/New_GEE`  
**Starting repository head before this handoff:** `832fe6446f7ce873aeb83675e27af9b2005cccfc`  
**Goal:** unlock honest numerical depth estimation only if independent evidence and repeatable radar linkage support it

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
training_started = false
broad_candidate_search = paused
approved_next_phase = radar_linkage_feasibility_screen
```

---

## 1. Plain-English current status

The app still cannot honestly output numerical depth.

No candidate has passed the full calibration contract. The repeated public-document search has now screened more than 400 leads. Most candidates failed because at least one of these remained missing:

- an actual measured depth;
- numerical measurement or survey uncertainty;
- exact mapped geometry;
- a clean observation period;
- an unchanged surface;
- an independently confirmed comparison area;
- enough independent sites for training, validation and holdout.

The work order has therefore changed.

Do **not** continue broad generic landfill searching as the immediate next task.

The next phase is a bounded scientific feasibility screen asking:

> Does Sentinel-1 contain any repeatable surface response that follows known or credibly ordered cover depth after moisture, vegetation, construction and acquisition differences are controlled?

This feasibility phase is exploratory only. It cannot enable numerical depth in the app and cannot create production calibration truth.

---

## 2. Exact point reached

The latest decision is recorded in:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`

Commit:

`832fe644 docs: pivot depth work to radar linkage feasibility screen`

The broad calibration-document search is paused because it was spending most effort on difficult evidence retrieval before answering the more basic scientific question: whether a usable radar relationship exists at all.

The immediate next deliverable has **not** yet been built.

The next session must create the execution plan for the feasibility screen using the strongest imperfect candidates, predeclared radar features, matched acquisition rules, confounder masks and clear pass/fail criteria.

No production model should be fitted during the first screen.

---

## 3. Why the feasibility pivot is necessary

Sentinel-1 C-band does not directly measure a buried interface one or several metres below the surface.

Any relationship with cover depth would be indirect through surface effects such as:

- settlement;
- moisture and drainage;
- vegetation response;
- roughness;
- compaction;
- long-term deformation.

Those surface effects are also affected by grading, soil type, vegetation, drainage design, repairs, roads and weather.

A documented depth value is therefore not enough. The project first needs evidence that depth ordering corresponds to a repeatable radar ordering after those surface confounders are controlled.

A feasibility pass would justify returning to strict document extraction.

A feasibility failure across properly designed sites would justify stopping the unbounded Sentinel-1 backscatter depth-calibration route.

---

## 4. How this work was performed

Continue the same evidence-first method.

### 4.1 Communication style

Every progress update should be brief and contain:

- current status;
- next step;
- usable calibration-row count;
- whether numerical depth is ready.

Do not bury the decision in technical detail.

### 4.2 Search method

1. Start from a named site and an exact missing record.
2. Prefer official regulator, utility, engineering and survey records.
3. Search exact report titles, permit numbers, document IDs, archive page markers and engineering phrases.
4. Check whether the measurement was made before or after the final remedy.
5. Check whether the surface stayed unchanged during the satellite period.
6. Check whether the measured locations and the radar observation area can be matched.
7. Document every meaningful promotion, hold or rejection immediately in `main`.
8. Move on after a route is decisively closed.

### 4.3 Evidence distinctions that must remain separate

Never merge these concepts:

- design requirement;
- minimum specified thickness;
- constructed minimum;
- actual measured point depth;
- average depth;
- one-sided lower bound;
- finite bounded interval;
- construction tolerance;
- measurement precision;
- survey accuracy;
- exact surveyed geometry;
- approximate outline;
- parcel boundary;
- target or work-area boundary;
- confirmed no-target area;
- analyst-selected background.

### 4.4 PDF and map handling

- Use the PDF screenshot/render route whenever a figure, table, drawing or map must be visually read.
- If rendering fails, use only the parsed text.
- Never claim that an unseen drawing was inspected.
- Never use OCR-derived fragments as exact geometry without visible confirmation.
- Never treat displayed decimal places as measurement accuracy.
- Never invent a coordinate reference system, tolerance or uncertainty.

### 4.5 Repository method

- Use the GitHub connector.
- Work directly on `main` for these documentary decisions.
- Create one concise Markdown dossier for each meaningful candidate or blocker.
- No pull request is needed for the documentation-only research path.

### 4.6 Safety and privacy limits

- Documentary and remote-sensing research only.
- Do not provide field-entry, excavation or hazardous-site access instructions.
- Avoid military and ammunition sites.
- Do not publish exact target coordinates in GitHub documents.
- Any recovered detailed geometry belongs in private calibration storage, not the public repository.

---

## 5. Calibration contract remains unchanged

Read:

`docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`

A strict positive record still requires:

- actual finite `known_depth_top_m`;
- `depth_reference_uncertainty_m`, unless the source explicitly provides a finite bounded interval;
- independently produced evidence;
- traceable source and review method;
- valid site and feature grouping;
- observation dates;
- exact enough geometry to match the feature to the sensor data;
- no cross-split leakage.

A confirmed negative still requires an independent source establishing that the area is a valid no-target/background case.

Design minimums, averages, one-sided lower bounds, notebook outputs, PCA scores and app predictions are not calibration truth.

The feasibility-screen proxy records must be marked research-ineligible and stored separately from strict calibration rows.

---

## 6. Strongest candidate bank for the feasibility screen

### 6.1 River Road Landfill — strongest measured-point candidate

Core dossier:

`docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`

Confirmed:

- 129 physical certification pits;
- about two pits per acre;
- surveyed pit locations shown on Sheet 1 of 3;
- Appendix A contains final cover thickness for every pit;
- deficient areas were corrected and re-certified;
- professional engineering and surveying controls were used;
- protected, undeveloped landfill surface;
- no current cap-failure finding was identified.

Still missing:

- readable individual accepted pit depths;
- identification of initial failures versus final accepted measurements;
- readable Sheet 1 pit geometry;
- coordinate system and datum for the pit plan;
- numerical measurement and survey uncertainty;
- disturbance exclusions for roads, drainage, vents, monitoring and repairs;
- point-by-point Sentinel-1 timing validation.

Important correction:

- Table 1 at `AR304822` is a **soil textural-classification table**, not a depth table.
- Do not use the old assumed `AR304840–AR304889` extraction window as verified.
- The actual pit forms remain image-only and inaccessible through the reviewed public routes.

Public-access routes already exhausted:

- NEPIS text search and targeted OCR snippets;
- direct NEPIS PDF patterns;
- EPA catalog and SEMS searches;
- Pennsylvania public-document searches;
- archive and mirror searches;
- unusual pit identifiers such as `68B` and `77A`;
- generic and exact report-title searches.

Do not repeat these routes unless a genuinely new rendering or archive capability is available.

### 6.2 Auburn McMaster Street — strong vacant-cover candidate

Read:

`docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`

Confirmed:

- licensed construction surveys;
- actual local cover thickness recorded on as-built drawings;
- general cover minimum of 12 inches;
- ecological-buffer cover of 2 feet;
- approved reuse material allowed only below 2 feet from final grade;
- public parcel/easement survey geometry;
- later vacant compacted-gravel condition;
- cover reported intact through May 2025.

Still missing:

- readable local as-built thickness values;
- exact target subarea polygons;
- construction or survey accuracy;
- finite uncertainty.

Do not treat the `>2 ft` condition as a finite depth label.

### 6.3 John Sevier Bottom Ash Pond — large stable-cover candidate

Read:

`docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`

Confirmed:

- 24 inches of soil cover over geomembrane;
- final closure completed in July 2017;
- approximately 20-acre capped footprint;
- annual inspections from 2022 through 2026 reported no yearly geometry change or structural deficiency;
- settlement instruments showed less than 0.1 ft movement in the latest annual period;
- final closure plans are indexed as record drawings.

Still missing:

- exact surveyed cap polygon;
- readable record drawings;
- cover-thickness tolerance;
- numerical uncertainty;
- proof that the published 24-inch statement represents an actual accepted local thickness rather than only a uniform construction statement.

### 6.4 Sconondoa Street former MGP — strongest surveyed-excavation lead

Read:

`docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`

Confirmed:

- mapped excavation-depth variation;
- licensed as-built survey package exists;
- later vacant condition;
- potentially useful within-site depth contrast.

Still missing:

- readable survey appendix;
- exact local depth values and geometry;
- numerical survey uncertainty;
- clean matched Sentinel-1 timing and surface controls.

### 6.5 J.R. Whiting — strongest actual mapped values in the older evidence archive

Read the previous handoff and:

`docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`

Confirmed:

- 107 mapped measured cover-thickness values;
- thickness range approximately `0.619 m` to `0.762 m`;
- 100-foot survey grid;
- surveyed subgrade and final topsoil elevations;
- licensed construction-record survey.

Still missing:

- numerical vertical survey accuracy;
- independently confirmed empty comparison area;
- clean unchanged observation period.

J.R. Whiting remains important strict-depth evidence, but the first feasibility-screen decision selected River Road, Auburn, John Sevier and Sconondoa because they may offer a simpler within-site or surface-response experiment.

### 6.6 Berks Landfill — secondary measured-point hold

Read:

- `docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`
- `docs/DEPTH_BERKS_LANDFILL_AR206_ACCESS_ADDENDUM_2026-07-25.md`

Confirmed:

- cap thickness was physically measured by excavation or augering;
- multiple measurement campaigns existed;
- western forested areas were deliberately preserved in part;
- later inspection history is documented.

Still missing:

- point field table;
- point map and CRS;
- numerical uncertainty;
- exact disturbance overlay;
- full 2025 review.

Keep as a hold. Do not use site averages as point labels.

---

## 7. River Road documents to read together

Read all of these before doing more River Road work:

1. `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
2. `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
3. `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
4. `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
5. `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`

The fifth document supersedes the earlier assumed page-window interpretation where they conflict.

Current River Road result:

```text
actual_measurement_program_confirmed = yes
pit_by_pit_values_known_to_exist = yes
pit_values_readable = no
surveyed_locations_known_to_exist = yes
location_sheet_readable = no
numerical_uncertainty = no
strict_calibration_row = no
feasibility_proxy_candidate = yes
```

---

## 8. Candidate routes closed in this work period

Do not restart these routes without new decisive evidence.

### Closed because values were pre-remedy, historical or later replaced

- `docs/DEPTH_HIMCO_DUMP_PRE_REMEDY_TEST_PITS_FOLLOWUP_2026-07-25.md`
  - 24 direct measurements existed before later grading and final remedy construction.
- `docs/DEPTH_FORT_WAYNE_REDUCTION_PRE_REMEDY_GRID_FOLLOWUP_2026-07-25.md`
  - 36 grid measurements predated excavation, regrading and final capping.
- `docs/DEPTH_BOONE_COUNTY_TEST_CELL_HISTORICAL_ONLY_CLOSURE_2026-07-26.md`
  - exact 0.6 m test-cell cover existed, but the cell was dismantled in September 1980.
- `docs/DEPTH_HELEVA_LANDFILL_HISTORICAL_CLAY_CAP_FOLLOWUP_2026-07-25.md`
  - historical two-foot clay layer did not provide surveyed final post-remedy point depths.

### Closed because the surface was actively operated, repaired or disturbed

- `docs/DEPTH_WEST_KL_AVENUE_ACTIVE_CAP_SYSTEM_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_KEYSTONE_SANITATION_DYNAMIC_COVER_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_LOPEZ_CANYON_ACTIVE_POSTCLOSURE_USE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_MODERN_SANITATION_ACTIVE_LANDFILL_DISTURBANCE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`
- `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_DORNEY_ROAD_DESIGN_ONLY_AND_REMEDY_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

Recurring failures included gas systems, wells, drainage, access roads, settlement repairs, mowing, replanting, truck traffic, forest growth, wetlands and continuing O&M.

### Closed because only a design minimum or construction statement was recovered

- `docs/DEPTH_OLD_CITY_OF_YORK_MINIMUM_COVER_AND_MONITORING_CLOSURE_2026-07-26.md`
  - two-foot minimum only; no local accepted measurements or uncertainty.
- `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_DORNEY_ROAD_DESIGN_ONLY_AND_REMEDY_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`

### Closed because of ecological conversion or redevelopment

- `docs/DEPTH_EAST_MOUNT_ZION_ECOLOGICAL_REVITALIZATION_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GARRETT_DALTON_FOUNDRY_REQUIRED_BUT_REDEVELOPED_CLOSURE_2026-07-26.md`
- `docs/DEPTH_CLOTHIER_ACTIVE_REUSE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_PHOTECH_REDEVELOPMENT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_COLESVILLE_DYNAMIC_CAP_FOLLOWUP_2026-07-25.md`

### Closed because the target was removed, treated or non-unique

- `docs/DEPTH_MW_MANUFACTURING_TREATED_WASTE_AND_ACTIVE_SYSTEM_CLOSURE_2026-07-26.md`
  - original target removed; later caps contain treated/stabilized material and active groundwater systems.
- `docs/DEPTH_ARKEMA_PIFFARD_CLEAN_CLOSURE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_CROSS_GYPSUM_POND_ACTIVE_SITE_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_WINYAH_REMOVAL_REUSE_FOLLOWUP_2026-07-25.md`

These closures added no usable calibration rows.

---

## 9. Immediate next task

Create a bounded feasibility-screen execution plan.

The plan should answer, before any analysis is run:

1. Which two or three sites will be used first?
2. What depth-order labels are source-supported at each site?
3. Which labels are exact, bounded, minimum-only or approximate?
4. Which areas must be excluded for roads, drainage, vents, monitoring, repairs, vegetation and redevelopment?
5. What observation period is construction-free and surface-stable?
6. Which Sentinel-1 orbit direction and relative orbit will be used?
7. Which dates pass rainfall, moisture, vegetation and seasonal matching?
8. Which small predeclared feature set will be calculated?
9. What within-site comparison will be tested?
10. What exact result passes or fails the feasibility screen?

Do not start with a large classifier or hundreds of derived features.

Do not use the app's anomaly masks, PCA outputs or notebook depth proxies as labels.

---

## 10. Short roadmap

### Phase A — Candidate and zone definition

- Select River Road, Auburn and John Sevier as the first candidate set unless geometry access makes one impossible.
- Keep Sconondoa as the next substitution candidate.
- Define shallow, intermediate and deep proxy zones only from source-supported evidence.
- Mark every feasibility record as ineligible for production calibration.
- Build explicit exclusion masks.

Deliverable:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_EXECUTION_PLAN_2026-07-26.md`

### Phase B — Acquisition manifest

- Use native-resolution Sentinel-1 data.
- Match orbit direction and relative orbit where possible.
- Record acquisition IDs.
- Use repeated dates.
- Screen rainfall, moisture, snow, vegetation and construction periods.
- Do not treat a 2 m resampled grid as independent 2 m radar information.

Deliverable:

- site/date manifest;
- exclusion ledger;
- declared feature list;
- no analysis results yet.

### Phase C — Small scientific screen

Calculate only predeclared interpretable features:

- VV;
- VH;
- VV–VH or equivalent polarization relation;
- temporal median;
- temporal variability;
- moisture-persistence contrast;
- stable within-site spatial contrast;
- deformation/coherence only where suitable SLC/GSLC data exist.

Produce transparent tables and plots.

No production model.

### Phase D — Decision

Pass only if:

- a predeclared within-site relationship appears;
- it repeats across multiple matched dates;
- it survives moisture, vegetation and construction exclusions;
- it has consistent direction at a second independent site;
- it is larger than isolated pixel noise;
- it is not created by resampling, smoothing or post-hoc feature selection.

Fail if:

- no stable relationship appears;
- direction reverses across dates;
- moisture or vegetation explains the result;
- the effect exists only during construction;
- the effect is isolated-pixel noise;
- it does not repeat independently;
- surface-condition variables explain the data as well as or better than depth ordering.

Decision outcomes:

- **Pass:** return to strict document extraction for the successful site conditions.
- **Fail:** keep numerical depth blocked and stop the Sentinel-1 backscatter calibration search.
- **Mixed:** narrow the product to settlement, moisture response or broad depth class under limited validated conditions.

---

## 11. What must not change

- Do not weaken the calibration contract.
- Do not enable app numerical depth from feasibility proxies.
- Do not call a minimum thickness an actual local depth.
- Do not call a one-sided lower bound a bounded interval.
- Do not assign site averages to individual pixels or points.
- Do not infer survey accuracy from decimal formatting.
- Do not digitize approximate maps as survey geometry.
- Do not substitute parcel boundaries for target boundaries.
- Do not fit and evaluate using the same physical site group across splits.
- Do not claim direct underground imaging from Sentinel-1.
- Do not show false precision such as `2.37 m` without evidence supporting that precision.

---

## 12. Documents to read in order

### Mandatory first read

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26.md`
2. `docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`
3. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
4. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25_V2.md`
5. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
6. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`

### Active feasibility-candidate read

7. `docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`
8. `docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`
9. `docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`
10. `docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`
11. `docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`
12. `docs/DEPTH_BERKS_LANDFILL_AR206_ACCESS_ADDENDUM_2026-07-25.md`

### River Road read

13. `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
14. `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
15. `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
16. `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
17. `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`

### All other new dossiers since the previous V2 handoff

18. `docs/DEPTH_ARKEMA_PIFFARD_CLEAN_CLOSURE_FOLLOWUP_2026-07-25.md`
19. `docs/DEPTH_BOONE_COUNTY_TEST_CELL_HISTORICAL_ONLY_CLOSURE_2026-07-26.md`
20. `docs/DEPTH_CLOTHIER_ACTIVE_REUSE_FOLLOWUP_2026-07-25.md`
21. `docs/DEPTH_COLESVILLE_DYNAMIC_CAP_FOLLOWUP_2026-07-25.md`
22. `docs/DEPTH_CROSS_GYPSUM_POND_ACTIVE_SITE_FOLLOWUP_2026-07-25.md`
23. `docs/DEPTH_DORNEY_ROAD_DESIGN_ONLY_AND_REMEDY_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
24. `docs/DEPTH_EAST_MOUNT_ZION_ECOLOGICAL_REVITALIZATION_FOLLOWUP_2026-07-25.md`
25. `docs/DEPTH_FORT_WAYNE_REDUCTION_PRE_REMEDY_GRID_FOLLOWUP_2026-07-25.md`
26. `docs/DEPTH_GARRETT_DALTON_FOUNDRY_REQUIRED_BUT_REDEVELOPED_CLOSURE_2026-07-26.md`
27. `docs/DEPTH_HELEVA_LANDFILL_HISTORICAL_CLAY_CAP_FOLLOWUP_2026-07-25.md`
28. `docs/DEPTH_HIMCO_DUMP_PRE_REMEDY_TEST_PITS_FOLLOWUP_2026-07-25.md`
29. `docs/DEPTH_KEYSTONE_SANITATION_DYNAMIC_COVER_FOLLOWUP_2026-07-25.md`
30. `docs/DEPTH_LOPEZ_CANYON_ACTIVE_POSTCLOSURE_USE_CLOSURE_2026-07-26.md`
31. `docs/DEPTH_MODERN_SANITATION_ACTIVE_LANDFILL_DISTURBANCE_CLOSURE_2026-07-26.md`
32. `docs/DEPTH_MW_MANUFACTURING_TREATED_WASTE_AND_ACTIVE_SYSTEM_CLOSURE_2026-07-26.md`
33. `docs/DEPTH_OLD_CITY_OF_YORK_MINIMUM_COVER_AND_MONITORING_CLOSURE_2026-07-26.md`
34. `docs/DEPTH_PHOTECH_REDEVELOPMENT_FOLLOWUP_2026-07-25.md`
35. `docs/DEPTH_STRASBURG_LANDFILL_DESIGN_ONLY_AND_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
36. `docs/DEPTH_WALSH_LANDFILL_ET_FOREST_DESIGN_ONLY_CLOSURE_2026-07-26.md`
37. `docs/DEPTH_WEST_KL_AVENUE_ACTIVE_CAP_SYSTEM_FOLLOWUP_2026-07-25.md`
38. `docs/DEPTH_WINYAH_REMOVAL_REUSE_FOLLOWUP_2026-07-25.md`

The previous V2 handoff contains the older J.R. Whiting, Plant Kraft, J.C. Weadock, J.H. Campbell, Possum Point, Mt. Storm, Grainger, Dale, Emery Pond and earlier candidate history. Read it rather than restarting those searches.

---

## 13. External session attachments reviewed

The following attachments were reviewed during the project but do not provide independent depth calibration truth:

- `notebook phases.md`
- `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb`

The candidate-scout notebook creates lawful paid-imagery request zones and quote comparisons. It does not contain measured depth evidence.

The notebook-phase summary describes historical heuristic and proxy outputs. Depth-named notebook values are not calibration labels unless independent provenance is recovered.

---

## 14. Repository progress since the previous V2 handoff

From commit `b480527` to the radar-feasibility decision at `832fe644`:

- 37 commits were added;
- 32 new depth-research dossiers were added;
- River Road became the strongest measured-point candidate;
- Auburn, John Sevier and Sconondoa remained useful feasibility candidates;
- numerous design-only, pre-remedy, redeveloped, active-system and dynamic-surface routes were closed;
- usable calibration rows remained zero;
- the approved next phase changed from broad document search to radar-linkage feasibility screening.

Important recent commits:

```text
3bcd25c docs: record River Road surveyed pit candidate
d8b3fcb docs: add River Road NEPIS OCR access addendum
5d89099 docs: record River Road Appendix A extraction window
d575eaf docs: add River Road OCR survey-control evidence
b8f75c5 docs: correct River Road OCR page mapping
2a302db docs: record exhausted River Road public access routes
5a92a77 docs: close redeveloped Garrett Dalton route
be1c037 docs: close historical Boone test cell route
6a61b0a docs: close active Lopez Canyon route
3fa3987 docs: close dynamic Walsh ET cover route
69d8cc2 docs: close active Modern Sanitation route
8604342 docs: close Strasburg design-only cap route
03df2f1 docs: close Dorney Road design-only cap route
653ccd7 docs: close Old City of York minimum-cover route
1d9939f docs: close MW Manufacturing treated-waste route
832fe64 docs: pivot depth work to radar linkage feasibility screen
```

---

## 15. Final handoff status

```text
strict_calibration_rows = 0
strict_positive_site_groups = 0
strict_confirmed_negative_site_groups = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
broad_candidate_search = paused
next_work_product = feasibility_screen_execution_plan
first_candidate_bank = River_Road_Auburn_John_Sevier
substitution_candidate = Sconondoa
```

### Next step in plain English

Build the small, controlled radar experiment first.

Use the strongest imperfect sites only to test whether deeper and shallower zones keep the same radar ordering across matched dates. If that relationship does not repeat after moisture, vegetation and construction controls, stop the Sentinel-1 numerical-depth route. If it does repeat at independent sites, return to strict measurement, geometry and uncertainty extraction before enabling any depth output.
