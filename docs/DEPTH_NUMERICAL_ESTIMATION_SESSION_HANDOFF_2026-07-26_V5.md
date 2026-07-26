# Numerical Depth Estimation — Canonical Session Handoff V5 — 2026-07-26

**Read this file first.**  
**Repository:** `max2026-lab/New_GEE`  
**Branch:** `main`  
**Goal:** unlock honest numerical depth estimation only if independent calibration evidence and a repeatable radar linkage both support it

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
training_started = false
broad_candidate_search = paused
approved_next_phase = radar_linkage_feasibility_screen
```

This V5 is the canonical handoff. It resolves a conflict created by overlapping sessions and supersedes the stopping-point instructions in all older handoffs.

In particular, the instruction in V4 to resume at Dorney Road is stale. Dorney Road, Old City of York and M.W. Manufacturing were already screened and closed before the project pivoted to the radar-linkage feasibility phase.

Older handoffs remain useful as evidence indexes and detailed history, but they must not override this file.

---

## 1. Plain-English current status

The app still cannot honestly output numerical depth in metres.

No site has passed the complete calibration contract. The project has screened more than 400 leads. The repeating blockers were:

- actual measured depth missing;
- numerical measurement or survey uncertainty missing;
- exact mapped geometry missing;
- the measured surface changed before or during the Sentinel-1 period;
- no independently confirmed comparison area;
- no clean train, validation and holdout site groups.

The work order has changed.

Do **not** continue broad generic landfill searching as the immediate next task.

The approved next phase is a bounded scientific screen asking:

> After moisture, vegetation, construction and acquisition differences are controlled, does Sentinel-1 show any repeatable surface response that follows known or credibly ordered cover depth?

This screen is exploratory only. It cannot enable numerical depth, cannot create production calibration truth and cannot weaken the calibration contract.

---

## 2. Repository conflict resolved

The repository contains several handoffs created by overlapping sessions.

### Stale instruction

`docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V4.md` says to resume at Dorney Road.

That is no longer correct.

The following routes were completed afterward or already existed on the same final branch history:

- Dorney Road Landfill — closed;
- Old City of York Landfill — closed;
- M.W. Manufacturing — closed;
- broad generic candidate search — paused;
- radar-linkage feasibility screen — approved as the next phase.

### Canonical decision

Read:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`

Commit:

`832fe644 docs: pivot depth work to radar linkage feasibility screen`

The detailed feasibility-phase handoff is:

`docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26.md`

Commit:

`a7706d1 docs: hand off depth radar feasibility phase`

This V5 preserves that scientific pivot and adds the repository-conflict correction.

---

## 3. Exact point reached

The document-search phase is paused.

The last strict candidate screens completed before the pivot were:

### Dorney Road Landfill

Document:

`docs/DEPTH_DORNEY_ROAD_DESIGN_ONLY_AND_REMEDY_INFRASTRUCTURE_CLOSURE_2026-07-26.md`

Commit:

`03df2f1 docs: close Dorney Road design-only cap route`

Reason: no point-specific accepted cover depths, no mapped measurement points and no numerical uncertainty; gas vents, drainage, monitoring and wetlands confound the surface.

### Old City of York Landfill

Document:

`docs/DEPTH_OLD_CITY_OF_YORK_MINIMUM_COVER_AND_MONITORING_CLOSURE_2026-07-26.md`

Commit:

`653ccd7 docs: close Old City of York minimum-cover route`

Reason: the public two-foot value is only a minimum specification, with no mapped accepted measurements or numerical uncertainty; monitoring and residential use confound the site.

### M.W. Manufacturing

Document:

`docs/DEPTH_MW_MANUFACTURING_TREATED_WASTE_AND_ACTIVE_SYSTEM_CLOSURE_2026-07-26.md`

Commit:

`1d9939f docs: close MW Manufacturing treated-waste route`

Reason: the original target was removed, later caps contain treated industrial material, and the active groundwater system and wetlands prevent a simple soil-over-target interpretation.

### Work not yet completed

The bounded radar-linkage feasibility **execution plan has not yet been created**.

No feasibility analysis branch has been implemented.

No production model has been fitted.

No calibration records have been created.

The next session starts by writing the execution plan, not by searching candidate number 401 and not by training.

---

## 4. The way we worked

The user normally says `go`, `continue` or `proceed`. Continue autonomously.

Every progress update should be brief and state:

- current status;
- next step;
- usable calibration-row count;
- whether numerical depth is ready.

### Evidence-first rules

1. Start from one named site and one exact missing record.
2. Prefer official regulator, utility, engineering, survey, as-built, closure, CQA and inspection records.
3. Search exact report titles, permit numbers, document IDs, archive page markers and distinctive engineering phrases.
4. Confirm whether a value is design, minimum, average, lower bound, bounded interval or actual measured point depth.
5. Keep construction tolerance, measurement precision, survey accuracy and total uncertainty separate.
6. Confirm whether measurements were made before or after the final remedy.
7. Confirm whether the same surface remained unchanged during the radar observation period.
8. Reject approximate outlines, parcel substitutes and analyst-selected backgrounds as calibration geometry.
9. Reject averages, design minimums and one-sided lower bounds as point labels.
10. Never infer missing coordinates, depths, re-certification status, datum or uncertainty.
11. Do not create a calibration row until the complete contract passes.
12. Document every decisive promote, hold or rejection on `main`.
13. When a route closes, record one clear reason, commit it and move on.
14. Do not ask the user to email agencies or manually retrieve files.
15. Do not weaken the contract or validator.

### PDF and map rules

- Use PDF rendering or screenshots whenever a map, drawing, table, figure or scanned form must be read.
- If rendering fails, use only parsed text.
- Never claim an unseen drawing was inspected.
- Never treat OCR fragments as survey geometry.
- Never treat displayed decimal places as measurement accuracy.

### Repository rules

- Use the GitHub connector.
- Documentation-only research can be committed directly to `main`.
- One concise Markdown dossier per meaningful candidate or blocker.
- No pull request is needed for this documentary research path.
- Keep exact target coordinates out of public Git history.

### Safety boundary

- Documentary and remote-sensing research only.
- No field-entry, excavation or hazardous-site access instructions.
- Avoid military and ammunition sites.
- Detailed recovered geometry belongs in private calibration storage, not GitHub.

---

## 5. Calibration contract remains unchanged

Read:

`docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`

A strict positive record requires:

- finite `known_depth_top_m`, or a source-provided finite bounded interval;
- `depth_reference_uncertainty_m`;
- independently produced evidence;
- traceable source and review method;
- exact enough geometry to match the measurement to sensor observations;
- valid reference and observation dates;
- stable surface history;
- correct site/feature grouping;
- no train, validation or holdout leakage.

A strict negative requires independent evidence that the area is a valid no-target or background case.

Never use as calibration truth:

- notebook depth outputs;
- PCA anomaly values;
- classifier labels;
- target masks;
- simulated layers;
- analyst guesses;
- design minimums;
- site-wide averages;
- one-sided lower bounds.

All feasibility proxy records must be clearly marked research-ineligible and kept separate from strict calibration records.

---

## 6. Approved next phase

The approved phase is documented in:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`

The screen asks one narrow question:

> Do deeper and shallower documented zones maintain a consistent radar ordering across repeated matched dates after surface and acquisition confounders are controlled?

### First candidate bank

1. River Road Landfill.
2. Auburn McMaster Street.
3. John Sevier Bottom Ash Pond.
4. Sconondoa Street former MGP as a backup or fourth site.

J.R. Whiting remains the strongest older source of already recovered mapped numerical cover values and should be retained as an additional evidence source.

Berks Landfill remains a secondary hold.

### Required radar controls

- native Sentinel-1 resolution;
- same orbit direction;
- same relative orbit where possible;
- similar incidence angle;
- repeated dates;
- matched seasonal windows;
- rainfall and soil-moisture screening;
- construction-active dates excluded;
- roads, drainage, repairs, vents, monitoring and changed vegetation excluded;
- areas large enough to contain multiple native radar-resolution elements.

### Predeclared first feature set

- VV backscatter;
- VH backscatter;
- VV minus VH or equivalent polarization relation;
- temporal median;
- temporal variability;
- persistent moisture-sensitive contrast;
- within-site spatial contrast against matched control zones;
- deformation or coherence only where suitable SLC/GSLC products exist.

Do not begin with hundreds of notebook-derived features.

Do not treat a 2 m resampled grid as independent 2 m radar observations.

### Pass criteria

The screen passes only if:

1. a predeclared relationship appears within a site;
2. it repeats across multiple matched dates;
3. it survives rainfall, vegetation and construction controls;
4. the same direction appears at a second independent site;
5. the effect covers more than isolated pixels;
6. it is not created by resampling, smoothing or post-hoc feature selection.

A one-site-only result remains exploratory.

### Failure criteria

Keep the Sentinel-1 numerical-depth route blocked if:

- no consistent relationship appears;
- the direction reverses across dates;
- the signal disappears after moisture or vegetation control;
- the effect exists only during construction;
- the effect is isolated-pixel noise;
- it does not repeat independently;
- surface-condition variables explain the result as well as or better than depth ordering.

---

## 7. Immediate next deliverable

Create:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_EXECUTION_PLAN_2026-07-26.md`

The plan should contain:

1. objective and non-production status;
2. proxy-record schema marked research-ineligible;
3. selected sites and why each is usable for the screen;
4. shallow/intermediate/deep zone definitions supported by sources;
5. geometry confidence and exclusions;
6. observation windows;
7. orbit and incidence-angle matching rules;
8. rainfall, moisture and vegetation controls;
9. predeclared radar features;
10. native-resolution aggregation rules;
11. site-level and cross-site tests;
12. pass, mixed and fail decisions;
13. output tables and plots;
14. audit trail for acquisition IDs and exclusion decisions;
15. explicit statement that the result cannot enable app depth.

Do not write production-model code before this plan is complete.

---

## 8. Short roadmap

### Phase 1 — Plan

- write the bounded execution plan;
- choose two or three usable within-site contrasts;
- mark every proxy record research-ineligible;
- predeclare features, exclusions and decision thresholds.

### Phase 2 — Build the exploratory dataset

- create only the minimum proxy tables and polygons needed for the screen;
- record source, date, confidence and known limitations;
- keep proxy data outside the strict calibration pack.

### Phase 3 — Run a small transparent analysis

- use native-resolution Sentinel-1 inputs;
- match dates and orbits;
- apply weather and disturbance exclusions;
- produce simple tables and one chart per test;
- avoid PCA-driven discovery and rule-based notebook labels.

### Phase 4 — Decide

- **Pass:** resume strict document extraction only for conditions showing repeatable linkage.
- **Mixed:** narrow the product claim to settlement, moisture response or depth class under limited conditions.
- **Fail:** keep numerical depth blocked and stop the unbounded Sentinel-1 backscatter depth-calibration route.

### Phase 5 — Only after a pass

- recover exact measured depths and numerical uncertainty;
- create strict calibration rows;
- build independent train, validation and holdout site groups;
- implement uncertainty and out-of-distribution rejection;
- validate on untouched sites before enabling any app output.

---

## 9. Strongest open evidence packages

### River Road Landfill

Role: strongest post-construction certification-pit package.

Confirmed:

- 129 physical certification pits;
- surveyed pit locations exist on Sheet 1 of 3;
- Appendix A contains each pit's final cover thickness;
- deficient areas were corrected and re-certified;
- professional engineering and survey controls;
- protected undeveloped surface.

Missing:

- readable accepted pit values;
- initial-failure versus final-recertification status;
- readable Sheet 1 geometry;
- CRS and datum;
- numerical measurement and survey uncertainty;
- point disturbance overlay;
- matched unchanged Sentinel-1 interval.

Important corrections:

- Table 1 at `AR304822` is soil textural classification, not depth.
- Do not use the assumed `AR304840–AR304889` window as verified.
- Public access routes have been exhausted unless a genuinely new rendering or archive capability appears.

Read all River Road files:

1. `docs/DEPTH_RIVER_ROAD_LANDFILL_SURVEYED_CERTIFICATION_PITS_CANDIDATE_2026-07-25.md`
2. `docs/DEPTH_RIVER_ROAD_NEPIS_OCR_ACCESS_ADDENDUM_2026-07-25.md`
3. `docs/DEPTH_RIVER_ROAD_APPENDIX_A_EXTRACTION_WINDOW_2026-07-25.md`
4. `docs/DEPTH_RIVER_ROAD_OCR_SURVEY_CONTROL_ADDENDUM_2026-07-26.md`
5. `docs/DEPTH_RIVER_ROAD_OCR_PAGE_MAPPING_CORRECTION_2026-07-26.md`

The fifth file supersedes conflicting page-window assumptions.

### Auburn McMaster Street

Read:

`docs/DEPTH_AUBURN_MCMASTER_SURVEYED_COVER_CANDIDATE_2026-07-25.md`

Strengths:

- licensed construction surveys;
- actual local cover thickness recorded in as-built drawings;
- vacant compacted-gravel surface;
- cover reported intact through May 2025.

Missing readable local values, exact target subareas and numerical uncertainty.

The `> 0.6096 m` reuse-material condition is only a lower bound.

### John Sevier Bottom Ash Pond

Read:

`docs/DEPTH_JOHN_SEVIER_BOTTOM_ASH_POND_MEASURED_COVER_CANDIDATE_2026-07-25.md`

Strengths:

- documented placement of 24 inches of cover soil over geomembrane;
- closure completed July 2017;
- approximately 20-acre footprint;
- inspections through 2026 report no yearly geometry change or structural deficiency.

Missing exact polygon, local accepted thickness values, tolerance and uncertainty.

### Sconondoa Street former MGP

Read:

`docs/DEPTH_SCONONDOA_SURVEYED_EXCAVATION_CANDIDATE_2026-07-25.md`

Strengths:

- mapped excavation-depth variation;
- licensed as-built survey package exists;
- later vacant setting.

Missing readable survey appendix, exact local values, numerical uncertainty and matched stable subareas.

### J.R. Whiting

Read:

`docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`

Strengths:

- 107 mapped measured cover values;
- approximately `0.619–0.762 m`;
- 100-foot grid;
- NGVD29;
- licensed construction-record survey.

Missing numerical vertical accuracy, confirmed negative area and clean observation interval.

### Berks Landfill

Read:

- `docs/DEPTH_BERKS_LANDFILL_MEASURED_CAP_POINTS_CANDIDATE_2026-07-25.md`
- `docs/DEPTH_BERKS_LANDFILL_AR206_ACCESS_ADDENDUM_2026-07-25.md`

Keep as a hold. Do not use site averages as point labels.

---

## 10. Recent routes closed — read before revisiting

Do not restart these without new decisive evidence:

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
- `docs/DEPTH_DORNEY_ROAD_DESIGN_ONLY_AND_REMEDY_INFRASTRUCTURE_CLOSURE_2026-07-26.md`
- `docs/DEPTH_OLD_CITY_OF_YORK_MINIMUM_COVER_AND_MONITORING_CLOSURE_2026-07-26.md`
- `docs/DEPTH_MW_MANUFACTURING_TREATED_WASTE_AND_ACTIVE_SYSTEM_CLOSURE_2026-07-26.md`

Common failure reasons:

- values were pre-remedy;
- only design minimums were public;
- no numerical uncertainty;
- active gas, leachate or groundwater systems;
- wetlands or open water;
- roads, truck traffic or repairs;
- forest growth, mowing or replanting;
- redevelopment;
- original target removed;
- mixed or treated material made the depth interpretation non-unique.

---

## 11. Required reading order for the next session

### Read first

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V5.md`
2. `docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`
3. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26.md`
4. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
5. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
6. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
7. `scripts/validate_depth_calibration_pack.py`
8. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md`
9. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md`

### Read as historical context, not as the current stopping point

10. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V4.md`
11. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-26_V3.md`
12. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25_V2.md`

Where these conflict with V5 or the feasibility decision, V5 controls.

### Read all current lead packages

13. all five River Road files listed in section 9;
14. Auburn McMaster Street dossier;
15. John Sevier dossier;
16. Sconondoa dossier;
17. J.R. Whiting dossier;
18. both Berks dossiers.

### Read all recent closure files

19. every file listed in section 10 before revisiting any of those candidates.

### Read the uploaded project references

20. `/mnt/data/notebook phases.md`
21. `/mnt/data/lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb`

The notebook-phase summary explains the historical notebook structure and shows that many claimed depth, treasure, metal and object outputs are heuristic, simulated, resampled or classifier-derived. They are not calibration truth.

The lawful candidate-scout notebook creates paid-imagery request zones, false-positive warnings and quote-comparison outputs. It does not provide measured depth evidence and is unrelated to the calibration contract. Read it only to avoid confusing its candidate scores or request zones with depth calibration data.

---

## 12. Tool limitations already encountered

- EPA NEPIS, SEMS, NYSDEC and TVA PDFs often expose parsed text but fail visual rendering.
- The screenshot service repeatedly failed on several scanned figures and drawings.
- Local runtime DNS failed for several government hosts.
- Adobe PDF conversion required login or disappeared during the session.
- OCR skipped image-only engineering forms.

Therefore:

- do not repeat the same River Road public-access routes without a new capability;
- do not claim unseen forms were read;
- preserve the known document key `91025HWW` for River Road;
- use a new renderer, archive identifier or separately indexed document if one appears.

---

## 13. Recent decisive commits

```text
3bcd25c River Road candidate recorded
b1e529a Berks evidence addendum
2a302db River Road public access routes exhausted
5a92a77 Garrett/Dalton closed
be1c037 Boone test cell closed
6a61b0a Lopez Canyon closed
3fa3987 Walsh closed
69d8cc2 Modern Sanitation closed
8604342 Strasburg closed
03df2f1 Dorney Road closed
653ccd7 Old City of York closed
1d9939f M.W. Manufacturing closed
832fe644 feasibility pivot approved
a7706d1 feasibility-phase handoff created
420a6f3 numerical-depth handoff V3 created
bc543d4 corrected handoff V4 created
```

V5 resolves the overlap between these handoffs and decisions.

---

## 14. Final handoff instruction

Start by creating the bounded radar-linkage feasibility execution plan.

Do not resume Dorney Road.

Do not continue generic landfill candidate searching.

Do not train a production model.

Do not enable app depth.

Keep the strict status visible:

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
next_deliverable = DEPTH_RADAR_LINKAGE_FEASIBILITY_EXECUTION_PLAN_2026-07-26.md
```
