# Numerical Depth Estimation — Session Handoff V2 — 2026-07-25

**Branch:** `main`  
**Goal:** unlock honest numerical depth estimation using real independent calibration evidence  
**Current status:** important evidence progress, but numerical depth remains blocked  
**Calibration records created:** `0`  
**Training ready:** no  
**App numerical depth enabled:** no

---

## 1. Plain-English current status

The project still cannot honestly output numerical depth.

The strongest positive-depth site is now **J.R. Whiting Ponds 1 and 2**:

- 107 actual mapped cover-thickness measurements;
- measured range about `0.619 m` to `0.762 m`;
- licensed construction-record survey;
- 100-foot survey grid;
- subgrade and final topsoil elevations are both recorded.

It is still not a calibration row because:

- the survey's numerical vertical accuracy is missing;
- no independently confirmed empty comparison area has been mapped;
- no clean unchanged Sentinel-1 period has been verified.

The strongest empty-area geometry lead is **Plant Kraft AP-1**:

- physical CCR removal is confirmed;
- a post-excavation topographic map exists;
- an excavation-limit drawing exists;
- the drawing uses Georgia East Zone, NAD83;
- the engineering/survey firm is identified.

It is still not a calibration row because:

- the coordinate-bearing map pages could not be rendered reliably;
- the exact AP-1 polygon was not extracted;
- boundary-position uncertainty is missing;
- the possible quiet period before port redevelopment is unverified.

Current readiness:

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
calibration_records_created = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

---

## 2. The exact point reached

The original six-site landfill search was exhausted and documented:

- Elk Plain;
- Sudbury;
- Go East;
- Recomp;
- RAMCO;
- Triune.

The search then moved to public coal-combustion-residual closure packages because some utilities and regulators publish final construction reports, closure-by-removal reports, and as-built drawings.

The biggest positive breakthrough was J.R. Whiting.

The negative/comparison search checked many completed-removal sites. Most failed for one of three repeating reasons:

1. the final boundary was explicitly labelled approximate;
2. the detailed final survey was not publicly retrievable;
3. the cleared area was rebuilt, converted to wetlands or stormwater use, or redeveloped.

The last active search path was:

```text
find a large completed clean closure
+ final survey plat or post-excavation survey directly readable
+ exact mapped boundary tied to physical removal confirmation
+ dry and unused final surface
+ clean unchanged Sentinel-1 period
```

The most recent candidate checks after the documented commits were:

- **Riverbend, North Carolina:** complete removal and grassed surface are promising, but the state document folder did not expose a readable final survey.
- **Pearl Ash Pond, Illinois:** identified as inactive and closed, but no usable public facility archive or closure survey was found.
- **Grand Tower, Illinois:** rejected because demolition, remediation, and industrial redevelopment prevent a clean unchanged radar period.
- The search was narrowing toward regulator-filed clean-closure survey plats with exact dimensions tied to permanent benchmarks.

Do not restart from general landfill candidates. Continue from the clean-closure survey-plat path.

---

## 3. How this session worked

Continue the same evidence-first method.

1. **Use simple status language.** Every update should contain:
   - current status;
   - next step.

2. **Do not run broad generic searches.** Start from a named facility and an exact missing record.

3. **Prefer official records:**
   - regulator files;
   - certified engineering reports;
   - construction-quality reports;
   - final construction documentation reports;
   - closure certifications;
   - as-built drawings;
   - post-excavation topographic surveys;
   - recorded survey plats;
   - state inspection and approval letters.

4. **Separate these evidence types:**
   - design requirement;
   - constructed minimum;
   - actual measured per-point depth;
   - construction tolerance;
   - survey measurement accuracy;
   - exact mapped removal boundary;
   - approximate work-plan boundary;
   - confirmed clean or removed area;
   - analyst-selected background.

5. **Never treat decimal display precision as survey accuracy.**

6. **Never convert a construction tolerance into total depth uncertainty without source support.**

7. **Never digitize a map labelled approximate as survey-grade geometry.**

8. **Never replace a pond/excavation boundary with a larger parcel or covenant tract unless an official record explicitly states they are identical.**

9. **Check the surface after cleanup.** Reject or hold areas converted into:
   - wetlands;
   - stormwater ponds;
   - operating ponds;
   - industrial storage;
   - building sites;
   - port redevelopment;
   - engineered liner-and-drain systems.

10. **Do not create a calibration row until all required fields exist.**

11. **Document each meaningful result in `main` immediately.**

12. **Do not ask the user to email agencies or perform manual record searches.** Continue the public-document work yourself.

---

## 4. Strongest positive-depth lead

### J.R. Whiting Ponds 1 and 2

Document:

`docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`

Commit:

`94c18ec docs: add J.R. Whiting measured cover evidence`

Established:

- completed final soil cover required 24 inches (`0.6096 m`);
- final construction report contains surveyed subgrade and topsoil elevations;
- control points `1000` through `1106` provide 107 mapped measured depths;
- recovered thickness range is `2.03 ft` to `2.50 ft`;
- metric range is approximately `0.618744 m` to `0.762 m`;
- survey grid is 100 feet;
- elevations are tied to NGVD29;
- survey work was completed by ROWE;
- topsoil survey completed November 21, 2019;
- final record drawings were issued.

Still missing:

- numerical vertical accuracy for the ROWE survey;
- independently confirmed CCR-free comparison footprint;
- verified unchanged post-closure Sentinel-1 period;
- visual verification of the official record-drawing table before private geometry extraction;
- independent validation and holdout site groups.

Decision:

```text
positive evidence = strongest found
actual mapped depth values = yes
numerical uncertainty = no
confirmed negative = no
clean timing = no
eligible calibration row = no
```

---

## 5. Strongest confirmed-empty leads

### 5.1 Plant Kraft AP-1 — strongest geometry-pending lead

Document:

`docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`

Commit:

`b28f47f docs: bound Plant Kraft surveyed removal route`

Established:

- physical CCR removal confirmed;
- removal complete by March 2018 or earlier;
- state remediation review and soil approval exist;
- post-excavation topographic map exists;
- excavation-limit drawing exists;
- top-of-structural-fill map exists;
- map uses Georgia East Zone, NAD83;
- survey/engineering firm identified as KEM & Co.

Still missing:

- readable rendering of the AP-1 excavation-limit map;
- exact private polygon extraction;
- boundary-position uncertainty;
- confirmation that the same polygon represents the final verified removal condition;
- clean unchanged Sentinel-1 timing before the 2021 port-property transfer.

Important rule:

Do not substitute the county parcel, environmental-covenant tract, hazardous-site point, or an aerial estimate for the AP-1 excavation limit.

### 5.2 J.C. Weadock — strongest physical removal verification

Document:

`docs/DEPTH_JC_WEADOCK_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`

Commit:

`05f6d1b docs: add J.C. Weadock confirmed removal evidence`

Established:

- 50-foot verification grid;
- 272 verification nodes;
- photographs, visual/color checks, microscopy, regulator approval;
- clean-fill backfill and vegetation.

Failure:

- public final boundary remains approximate;
- detailed August 2020 grid drawing was not publicly retrievable.

Decision:

Evidence-only. Do not digitize the approximate outline.

### 5.3 J.H. Campbell — strong regulator-confirmed removal

Documents:

- `docs/DEPTH_JH_CAMPBELL_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
- `docs/DEPTH_JH_CAMPBELL_EXACT_BOUNDARY_FOLLOWUP_2026-07-25.md`

Commits:

- `9f6fc09 docs: add J.H. Campbell confirmed removal evidence`
- `6092f76 docs: close JH Campbell exact boundary route`

Established:

- excavation to the established base of CCR;
- grid-node verification;
- colorimetric and microscopy checks;
- EGLE observation and concurrence;
- clean-fill backfill and vegetation.

Failure:

- accessible official maps label both the excavation and pond boundaries approximate;
- the detailed August 2019 removal documentation report was not publicly available;
- the later 2023 remedy report still used approximate boundaries.

Decision:

Closed as an exact-boundary public route.

---

## 6. Other CCR/removal sites checked

### Possum Point

Document:

`docs/DEPTH_POSSUM_POINT_REMOVAL_BOUNDARY_TIMING_FOLLOWUP_2026-07-25.md`

Commit:

`32d8109 docs: close Possum Point removal route`

Result:

- four ponds fully excavated;
- at least six inches of over-excavation;
- Pond E became an active stormwater pond;
- other areas remained managed industrial/post-closure structures;
- exact boundary not recovered.

Decision: closed.

### Mt. Storm

Document:

`docs/DEPTH_MT_STORM_REMOVAL_AND_SURFACE_REUSE_FOLLOWUP_2026-07-25.md`

Commit:

`723bb7e docs: close Mt Storm removal route`

Result:

- Ponds A-D removed and professionally certified;
- Ponds A-C rebuilt as operating ponds;
- Pond D backfilled;
- former pond land planned for storage, equipment, and construction.

Decision: closed because of immediate reuse.

### Grainger

Document:

`docs/DEPTH_GRAINGER_WETLAND_REMOVAL_FOLLOWUP_2026-07-25.md`

Commit:

`a5a68a8 docs: close Grainger wetland removal route`

Result:

- two ponds emptied;
- at least one additional foot of soil removed;
- remaining soil tested and regulator-approved;
- areas converted into wetlands, planted, monitored, and planned for redevelopment.

Decision: closed because the surface is not a stable dry control.

### Dale

Document:

`docs/DEPTH_DALE_CLEAN_CLOSURE_SURVEY_FOLLOWUP_2026-07-25.md`

Commit:

`b0c33c docs: close Dale public survey route`

Result:

- Kentucky inspectors verified removal down to native soil;
- exact final survey and pond-specific stable timing were not publicly retrievable.

Decision: evidence-only.

### Emery Pond

Document:

`docs/DEPTH_EMERY_POND_ENGINEERED_REUSE_FOLLOWUP_2026-07-25.md`

Commit:

`f8d8814 docs: close Emery Pond engineered reuse route`

Result:

- closure by removal confirmed;
- former pond rebuilt with a composite liner and perimeter drain for continuing groundwater cleanup.

Decision: closed because it is an engineered active cleanup surface, not a natural empty control.

### Bremo Bluff

Result:

- full removal and regulator acceptance confirmed;
- cleared areas were tied to named project-grid cells and field survey;
- record-drawing/survey-coordinate sheets were not publicly readable;
- no exact real-world polygon extracted.

Decision: evidence-only; not separately documented in Git during this pass.

### Riverbend

Result:

- complete removal, regrading, grassing, and continuing stability inspections appear promising;
- North Carolina's public document folder did not expose a readable final survey or exact polygon.

Decision: retain as an uncompleted lead; do not create a row.

### Pearl Ash Pond

Result:

- inactive and closed unit identified;
- no usable public facility archive or closure survey found.

Decision: weak hold.

### Grand Tower

Result:

- active demolition, remediation, and industrial redevelopment.

Decision: reject for clean timing.

---

## 7. Earlier landfill-site work completed in the same session

Read these for the original six-site screen and its final bounded results:

- `docs/DEPTH_THREE_SITE_BOUNDED_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_ELK_PLAIN_SURVEY_ACCURACY_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_SUDBURY_REPORT_64264_FINAL_PUBLIC_RECOVERY_2026-07-25.md`
- `docs/DEPTH_RECOMP_AS_BUILT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_RAMCO_AS_BUILT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_TRIUNE_COMPLETION_REPORT_FOLLOWUP_2026-07-25.md`
- `docs/DEPTH_GO_EAST_NEGATIVE_EVIDENCE_UPDATE_2026-07-25.md`

Key final decisions:

- **Elk Plain:** real mapped depth values, but no numerical survey accuracy and no confirmed negative.
- **Sudbury:** verified minimum and numerical construction controls, but no extracted final mapped surface.
- **Go East:** two physically checked empty-area leads and a `0.762 m` minimum constructed cover, but boundaries are unextracted and the site has major construction confounding.
- **Recomp:** original cover later buried under new engineered construction.
- **RAMCO:** no numerical installed thickness or accuracy.
- **Triune:** completion report unavailable and no numerical cover evidence.

---

## 8. Documents the next session must read — in order

### First: current handoff and status

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25_V2.md` — this document; read first.
2. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25.md` — earlier handoff; background only.
3. `docs/DEPTH_NUMERICAL_ESTIMATION_HANDOFF_2026-07-25.md` — earlier compact handoff; background only.

### Current strongest evidence

4. `docs/DEPTH_JR_WHITING_MEASURED_COVER_EVIDENCE_UPDATE_2026-07-25.md`
5. `docs/DEPTH_PLANT_KRAFT_SURVEYED_REMOVAL_AND_REUSE_FOLLOWUP_2026-07-25.md`
6. `docs/DEPTH_JC_WEADOCK_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
7. `docs/DEPTH_JH_CAMPBELL_CONFIRMED_REMOVAL_EVIDENCE_UPDATE_2026-07-25.md`
8. `docs/DEPTH_JH_CAMPBELL_EXACT_BOUNDARY_FOLLOWUP_2026-07-25.md`

### Closed CCR/removal routes

9. `docs/DEPTH_POSSUM_POINT_REMOVAL_BOUNDARY_TIMING_FOLLOWUP_2026-07-25.md`
10. `docs/DEPTH_MT_STORM_REMOVAL_AND_SURFACE_REUSE_FOLLOWUP_2026-07-25.md`
11. `docs/DEPTH_GRAINGER_WETLAND_REMOVAL_FOLLOWUP_2026-07-25.md`
12. `docs/DEPTH_DALE_CLEAN_CLOSURE_SURVEY_FOLLOWUP_2026-07-25.md`
13. `docs/DEPTH_EMERY_POND_ENGINEERED_REUSE_FOLLOWUP_2026-07-25.md`

### Original named-site screen

14. `docs/DEPTH_THREE_SITE_BOUNDED_FOLLOWUP_2026-07-25.md`
15. `docs/DEPTH_ELK_PLAIN_SURVEY_ACCURACY_FOLLOWUP_2026-07-25.md`
16. `docs/DEPTH_SUDBURY_REPORT_64264_FINAL_PUBLIC_RECOVERY_2026-07-25.md`
17. `docs/DEPTH_RECOMP_AS_BUILT_FOLLOWUP_2026-07-25.md`
18. `docs/DEPTH_RAMCO_AS_BUILT_FOLLOWUP_2026-07-25.md`
19. `docs/DEPTH_TRIUNE_COMPLETION_REPORT_FOLLOWUP_2026-07-25.md`
20. `docs/DEPTH_GO_EAST_NEGATIVE_EVIDENCE_UPDATE_2026-07-25.md`
21. `docs/DEPTH_GO_EAST_CONFIRMED_NEGATIVE_EVIDENCE_2026-07-25.md`
22. `docs/DEPTH_SUDBURY_NUMERICAL_CONTROL_EVIDENCE_UPDATE_2026-07-25.md`
23. `docs/DEPTH_PUBLIC_ENGINEERING_PACKAGE_SCREEN_2026-07-24.md`

### Governing plan, blockers, architecture, and validator

24. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md`
25. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
26. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
27. `scripts/validate_depth_calibration_pack.py`
28. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md`

### Completed method test

29. `docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md`
30. `docs/DEPTH_BUTO_METHOD_TEST_EXECUTION_PLAN_2026-07-24.md`
31. `scripts/run_buto_s1_method_screen.py`
32. `tests/unit/test_buto_s1_method_screen.py`

### Original notebook context

33. Read the supplied notebook phase inventory, especially:
    - Sentinel-1 pipeline and grid QA;
    - PCA anomaly and object extraction;
    - classifier and training scaffolding;
    - depth-related cells;
    - target labels that remain unvalidated.
34. Review the original notebook only as implementation context. Do not treat its depth, material, or target labels as calibration truth.
35. Review `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb` only if the next task needs the current candidate-scout implementation.

---

## 9. Immediate next steps

### Step 1 — Continue the clean-closure survey-plat search

Find a named, completed, large surface-impoundment clean closure where the public regulator package directly includes:

- final post-excavation or clean-closure survey;
- exact dimensions tied to permanent benchmarks or coordinates;
- physical confirmation that the material was removed;
- dry and unused final surface;
- completion date;
- post-closure records proving the same surface stayed unchanged.

Prefer:

- regulator-hosted files over utility summary pages;
- final closure report over closure plan;
- survey plat over approximate sketch;
- as-built or post-excavation topography over parcel boundaries.

Stop immediately when:

- the only map is approximate;
- the detailed survey is unavailable;
- the site was converted to wetlands, stormwater, industrial storage, buildings, or redevelopment;
- the surface timing cannot be separated from later work.

### Step 2 — Keep two focused recovery paths open

#### Positive path: J.R. Whiting

Search only for:

- ROWE survey-control notes;
- numerical vertical accuracy;
- equipment/instrument specification tied to the record survey;
- post-closure inspection evidence for an unchanged period;
- an independently confirmed CCR-free comparison area.

#### Negative path: Plant Kraft

Search only for:

- a readable copy of the Certification of CCR Removal map pages;
- the AP-1 post-excavation topographic map;
- the excavation-limit drawing;
- survey notes or boundary-position accuracy;
- records proving a clean period between final grading/removal and later port redevelopment.

Do not repeat parcel or covenant searches unless an official source says the tract equals the AP-1 excavation limit.

### Step 3 — Only after one complete row

When one positive or negative candidate becomes complete:

1. extract geometry privately;
2. create a candidate row privately;
3. run `scripts/validate_depth_calibration_pack.py`;
4. record every validator failure;
5. do not weaken the validator;
6. do not start training until independent site groups exist.

---

## 10. Short roadmaps

### Roadmap A — First positive record

```text
J.R. Whiting survey accuracy
→ confirm unchanged Sentinel-1 dates
→ visually verify record table
→ extract private depth-point geometry
→ create candidate positive rows
→ run validator
```

### Roadmap B — First confirmed negative record

```text
readable final removal survey
→ exact private polygon
→ boundary uncertainty
→ prove dry unused surface
→ verify unchanged Sentinel-1 dates
→ create candidate negative row
→ run validator
```

### Roadmap C — Dataset readiness

```text
complete site group 1
→ complete independent site group 2
→ complete independent site group 3
→ assign train / validation / holdout
→ no site-group reuse
→ validator passes
```

### Roadmap D — Numerical-depth research

```text
validator passes
→ extract matched Sentinel-1 features
→ test depth correlation
→ validate on separate site
→ test untouched holdout
→ quantify error and failure range
```

### Roadmap E — App unlock

```text
repeatable holdout performance
→ architecture gate review
→ honest uncertainty display
→ enable numerical depth only inside validated conditions
```

---

## 11. Hard rules for the next session

Do not:

- start model training;
- enable depth in the app;
- create placeholder calibration rows;
- use analyst-drawn background as confirmed empty;
- use approximate boundaries as exact geometry;
- use design thickness as an exact measured label;
- use displayed decimals as accuracy;
- use a construction tolerance as total uncertainty without support;
- reuse one physical site group across train, validation, and holdout;
- restart broad searching before exhausting the named clean-closure survey-plat path.

---

## 12. Final handoff statement

**Current status:** The search made a real breakthrough on the positive side with J.R. Whiting's 107 mapped measured cover depths. The negative side also improved: Plant Kraft proves that coordinate-bearing post-excavation mapping exists, while Weadock and Campbell prove very strong physical removal. None is complete enough for a calibration row.

**Next step:** Continue the regulator-filed clean-closure survey-plat search for one directly readable exact removal boundary on a dry, unused, unchanged surface. In parallel, continue only the narrow J.R. Whiting accuracy search and Plant Kraft map-recovery search.
