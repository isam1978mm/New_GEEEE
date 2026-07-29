# Numerical depth estimation — session handoff — 2026-07-29 V2

## Start here

This is the authoritative handoff for the next session.

Read this entire document and the required-reading list before searching, running Earth Engine, changing the app, reopening a closed candidate, merging a recovery branch, or changing the selected strategy.

## Plain-English current status

**Numerical depth is still NOT GOOD TO GO.**

The combined plan remains active:

- **Option 5 — Change Target:** useful radar anomaly output is implemented and merged.
- **Option 1 — Global Depth:** strict evidence-first calibration search continues.
- **Option 3 — Complete Candidates:** Tyrone Dam 3X is the current foreground route.
- **Option 4 — Local AOI Calibration:** available, but inactive until one AOI has a complete shallow/deep/control package.
- **Option 2 — Ordering Test:** RMA was executed and closed as inconsistent.

Current gates:

```text
usable positive depth site groups = 0
usable confirmed negative site groups = 0
usable calibration rows = 0
Option 1 Earth Engine query executed = false
historical Option 2 RMA Earth Engine query executed = true
training started = false
numerical depth ready = false
app depth enabled = false
```

## Exact stopping point

The work stopped on **PR #47 — Tyrone 3X and No. 1 as-built recovery**.

```text
PR = #47
branch = agent/tyrone-3x-no1-asbuilt-recovery-20260729
state = open draft
merged = no
merge instruction = DO NOT MERGE
head = 7b20816b3ade6d6b81f503f15e0f0c6f8dfd5239
```

PR #47 is a temporary recovery branch only. It contains workflows for downloading official records, extracting text, recovering the USGS mine-waste polygon, downloading a USGS 3DEP DEM, and attempting basemap georeferencing.

### Workflow results at handoff

```text
Tyrone 3X and No.1 as-built recovery = success
run = 30465301800
artifact = 8729313353
after-download size = about 145 MB
artifact name = tyrone-3x-no1-asbuilt-records
expires = 2026-08-05

Tyrone 3X DEM recovery = success
run = 30465302007
artifact = 8729286115
artifact name = tyrone-3x-dem-records
expires = 2026-08-05

Tyrone 3X georeference recovery = failure
run = 30465313522

full repository CI = success
run = 30465302117
```

## Immediate next action

1. Download artifact `8729313353` before it expires.
2. Inventory every recovered PDF and extracted text file.
3. Identify the exact documents named:
   - Comprehensive Cover Performance Evaluation;
   - 3X Tailing Annual Summary;
   - 3X Tailing As-Built;
   - No. 1 Stockpile Annual Summary;
   - No. 1 Stockpile As-Built;
   - 2020 closure-plan text, figures, plates and tables;
   - 2020 Appendix A reclamation drawings;
   - later repair and stability records.
4. Inspect only the decisive Tyrone questions listed below.
5. Download artifact `8729286115` only as supporting topographic context. Do not treat DEM-derived geometry as official Test Plot 5/6 boundaries.
6. Diagnose the failed georeference workflow only if the official PDFs do not already provide usable coordinate-tied geometry.
7. Close PR #47 without merge after recording a final decision.

## Decisive Tyrone questions

A Tyrone route passes only if the recovered official records establish all required items.

### Depth evidence

- final measured as-built depth for Test Plot 5;
- final measured as-built depth for Test Plot 6;
- numerical uncertainty, confidence interval, tolerance, or survey accuracy;
- proof that the values apply to the full polygons rather than isolated test points.

Known published values must be verified against the recovered originals. Earlier evidence described approximately:

```text
Test Plot 5 mean = 26.8 inches
Test Plot 6 mean = 37.4 inches
```

Do not rely on previously transcribed intervals until the recovered official report is checked directly.

### Geometry

- exact Test Plot 5 polygon;
- exact Test Plot 6 polygon;
- coordinate system, datum, surveyed corners, CAD/GIS geometry, or a defensible georeferenced official drawing;
- at least 30–40 m clean interior after excluding boundaries, roads, drains, instruments, swales, channels, repairs, and infrastructure.

### Surface comparability

- same or genuinely comparable radar-facing surface material;
- same cover-layer sequence except for the depth difference being tested;
- same or comparable vegetation treatment;
- comparable slope, aspect, grading, drainage, roughness, and maintenance history.

### Stability

- exact construction-completion date;
- no major repair, regrading, erosion reconstruction, traffic disturbance, or additional reclamation during the chosen Sentinel-1 period;
- plot-specific stability after 2014.

### Control requirement

For **Option 1**, Tyrone may contribute a positive shallow/deep site group without supplying the entire global dataset.

For **Option 4**, Tyrone additionally needs a defensible confirmed control or zero/unchanged reference under comparable surface conditions.

Do not call an adjacent slope a control merely because it looks untreated.

## Decision rules after artifact review

### GOOD TO GO — documentary radar screen

Use this only if all seven gates pass:

```text
full-scale clean zones = yes
final measured numerical depths = yes
numerical uncertainty = yes
coordinate-tied geometry = yes
matched radar-facing surfaces = yes
exact second depth or confirmed control = yes
stable Sentinel-1 period = yes
```

If Tyrone passes:

1. create a permanent main-branch evidence document and structured JSON;
2. close PR #47 without merge;
3. preregister a bounded radar comparison before looking at radar values;
4. run Earth Engine only for the approved polygons and stable period;
5. complete spatial, temporal, orbit, incidence-angle, valid-pixel, and seasonal QA;
6. create a calibration row only if the radar result and all evidence gates remain defensible.

### NOT GOOD TO GO

If any fatal item is missing:

- document the exact blocker;
- distinguish a true rejection from an external-record blocker;
- close PR #47 without merge;
- do not create a calibration row;
- do not run Earth Engine to compensate for missing ground truth.

## How we worked

The next session should continue the same evidence-first method.

### 1. Cheap documentary screen before radar

Reject immediately when a fatal condition is clear:

- construction incomplete;
- no stable post-construction Sentinel-1 period;
- only one cover/depth condition;
- covered-versus-uncovered comparison instead of two numerical conditions;
- clean interior below about 30–40 m after exclusions;
- obviously different surfaces, slope, material, vegetation, grading, drainage, or maintenance;
- active reconstruction or disturbance.

### 2. Deep official-record review only for survivors

Review for:

- final measured as-built depth, not design depth or minimum requirement;
- numerical uncertainty, interval, tolerance, or survey accuracy;
- coordinate-tied polygons;
- an exact second depth condition or confirmed control;
- matching radar-facing near-surface construction;
- stable observation dates;
- sufficient clean interior after exclusions.

### 3. Fail closed

Never substitute:

- design depth for measured as-built depth;
- broad site boundary for treatment polygon;
- nearby land for a confirmed control;
- satellite-estimated corners for official geometry;
- qualitative construction language for numerical uncertainty;
- one landfill area for a negative control because its cover differs;
- DEM patterns for official treatment boundaries.

### 4. Temporary recovery branches

Recovery PR rules:

- label as recovery-only or do-not-merge;
- do not merge workflows into `main`;
- preserve official files and hashes in artifacts;
- close the PR after the evidence decision;
- write permanent decisions in main-branch documentation, not only in temporary workflow code.

### 5. Radar comes last

For Option 1 or Option 4, do not run Earth Engine because a candidate merely looks promising.

Radar begins only after the documentary gate passes and the comparison is preregistered.

## Work completed in this project phase

### Option 5 — merged and usable

PR #35 was merged.

The app now exposes the existing PCA anomaly summaries in the established classifier-results area with the label:

`Radar anomaly review — NOT DEPTH`

The output includes object count, total object area, median anomaly, strongest anomaly, and ranked objects.

The score is explicitly described as:

- unitless;
- within-run only;
- not probability;
- not physical confirmation;
- not measured change;
- not a depth estimate.

`Depth estimate: not available` remains preserved.

Validation at merge:

```text
frontend production build = passed
full test suite = 1150 passed, 31 skipped
committed SPA assets = synchronized
```

### Option 1 batches 1–4 — merged

Twenty new candidates were screened in four bounded batches. None passed.

Merged PRs:

- #36 — Batch 1;
- #37 — Batch 2;
- #38 — Batch 3;
- #39 — Batch 4.

Batch finalists and fatal blockers:

- Olympic View: one repeated profile or a different cover assembly; no measured pair.
- Lowry Landfill: broad/minimum-only statements; no mapped measured pair or uncertainty.
- Fort Dix: engineered cap versus existing landfill cover; no confirmed control or measured pair.
- Mather AFB: no coordinate-tied measured pair; Site 4 is confounded by consolidation and infrastructure.

### Deep-recovery routes closed without merge

- PR #40 — Detour Lake: large trial, but depth confounded with slope, aspect, grading, peat, and revegetation; no measured coordinate-tied pair with uncertainty.
- PR #42 — Silver Bow Creek: very large remedy, but no published measured depth polygons or uncertainty.
- PR #43 — John Sevier: strong record drawings, but one continuous cap system and no second measured depth condition.
- PR #44 — Tyrone USNR: measured point thicknesses for one nominal three-foot cover; treatment differences are seed/mulch, not depth.
- PR #45 — Continental test plots: no final measured depths, no geometry, materials deliberately confounded, stable period not proven.
- PR #46 — Mount Taylor: drawings show nominal 36-inch and 42-inch assemblies, but agency review states measured thickness tables and other QA evidence were missing; later earthmoving complicates stability.

All temporary recovery workflows remained unmerged.

## Active and pending routes

### PR #47 — Tyrone 3X and No.1

Current foreground route. Finish first.

### PR #41 — Aurora Soil Capping Study

```text
state = open draft
merge instruction = DO NOT MERGE
```

Aurora remains one of the strongest experimental designs:

- 36 replicated one-hectare cells;
- published treatment layout;
- potential matched pair of approximately 100 cm and 150 cm using the same nominal surface and subsoil materials;
- long monitoring period.

Still missing:

- public final measured as-built depths;
- numerical construction uncertainty;
- exact coordinate-tied cell polygons.

Finish or close PR #41 only after PR #47 unless Tyrone becomes blocked.

### New Mexico EMNRD public-record request

```text
reference = N000019-070026
submitted = 2026-07-28
status = pending unless a newer agency response is available
```

When the response arrives, preserve all files unchanged and compare them against the records recovered in PR #47.

### Aitik WRD6

Strong nominal 1.6 m versus 2.1 m matched design and long monitoring, but blocked by missing official surveyed corners, measured as-built values, and uncertainty.

Do not approximate geometry from imagery.

### Faro Mine pilot

Large panels and multiple nominal depths, but missing the exact matched-panel matrix, official polygons, measured final thicknesses, and uncertainty.

## Historical route that must not be repeated

### Option 2 RMA ordering test

Final validated result:

```text
acquisitions = 82
usable months = 33
3-foot zone above 2-foot zone = 20/33 = 60.6%
Wilson 95% interval = 0.4368 to 0.7532
median monthly difference = +0.3678
positive seasons = 2/4
final decision = ordering_inconsistent
```

Do not:

- cherry-pick summer/fall;
- reverse expected direction after seeing the result;
- change the metric post hoc;
- create a calibration row from RMA.

## Required reading for the next session

Read in this order.

### Authoritative handoffs and strategy

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29_V2.md`
2. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29.md`
3. `docs/DEPTH_NUMERICAL_ESTIMATION_OPTION_REFERENCE.md`
4. `docs/OPTION1_OPTION5_COMBINED_PLAN_START_2026-07-28.md`
5. `docs/DEPTH_OPTION4_LOCAL_AOI_FEASIBILITY_RESULT_2026-07-28.md`

### Current Tyrone route

6. PR #47 body, workflow runs, artifacts, and discussion
7. `docs/DEPTH_OPTION3_TYRONE_DAM3X_DECISIVE_RECORD_RECOVERY_RESULT_2026-07-28.md`
8. the Tyrone public-record request documentation and structured request JSON
9. every recovered official Tyrone PDF and extracted text file in artifact `8729313353`
10. the USGS polygon and DEM metadata in artifact `8729286115`

### Option 1 merged screening history

11. `docs/DEPTH_OPTION1_GLOBAL_BATCH1_CHEAP_SCREEN_2026-07-28.md`
12. `docs/DEPTH_OPTION1_GLOBAL_BATCH1_FINAL_RESULT_2026-07-28.md`
13. `docs/DEPTH_OPTION1_GLOBAL_BATCH2_CHEAP_SCREEN_2026-07-28.md`
14. `docs/DEPTH_OPTION1_LOWRY_LANDFILL_DECISIVE_RESULT_2026-07-28.md`
15. `docs/DEPTH_OPTION1_GLOBAL_BATCH3_CHEAP_SCREEN_2026-07-28.md`
16. `docs/DEPTH_OPTION1_FORT_DIX_DECISIVE_RESULT_2026-07-28.md`
17. `docs/DEPTH_OPTION1_GLOBAL_BATCH4_CHEAP_SCREEN_2026-07-28.md`
18. `docs/DEPTH_OPTION1_MATHER_AFB_DECISIVE_RESULT_2026-07-28.md`
19. the matching JSON files under `data/`

### Closed experiments and near-misses

20. `docs/DEPTH_OPTION2_RMA_ORDERING_TEST_RESULT_2026-07-28.md`
21. PR #40 — Detour Lake, closed without merge
22. PR #42 — Silver Bow Creek, closed without merge
23. PR #43 — John Sevier, closed without merge
24. PR #44 — Tyrone USNR, closed without merge
25. PR #45 — Continental test plots, closed without merge
26. PR #46 — Mount Taylor, closed without merge
27. PR #41 — Aurora recovery, still open and do-not-merge

### App architecture and evidence rules

28. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
29. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
30. validator, calibration-record, split-isolation, evidence-reference, and uncertainty specifications under `docs/` and `data/`

## Notebook warning

The uploaded notebook is not the current app architecture and must not drive the documentary calibration decision.

It contains many duplicate experimental cells, manual Earth Engine authentication, numerous derived “treasure/geophysics” indices, PCA anomaly extraction, rule-based classifiers, model scaffolding, and claims that are not calibrated depth evidence. The notebook also includes a manual `ee.Authenticate()` fallback and many later target-classification cells. Treat it as historical experimentation only. Its phase inventory is summarized in the uploaded notebook-phases document.

Do not use notebook outputs, PCA anomaly values, CNN labels, or synthetic geophysics layers as ground-truth depth.

## Short roadmap

### Roadmap A — finish Tyrone first

1. download artifacts;
2. inventory official files;
3. recover exact Test Plot 5/6 measurements and geometry;
4. verify uncertainty, surface match, clean width, and stability;
5. issue GOOD TO GO or NOT GOOD TO GO;
6. close PR #47 without merge;
7. write permanent result on `main`.

### Roadmap B — only if Tyrone passes

1. preregister one bounded radar comparison;
2. run Earth Engine for the approved polygons and period;
3. complete QA;
4. decide whether one Option 1 site group or an Option 4 local route is defensible;
5. keep global depth disabled until multiple independent sites and holdouts exist.

### Roadmap C — if Tyrone fails or remains externally blocked

1. finish Aurora PR #41;
2. then revisit Aitik or Faro only for exact missing records;
3. avoid another unlimited random candidate search;
4. prefer official CQA/as-built packages over attractive design papers.

## Required reporting style

Always tell the user in plain English:

```text
GOOD TO GO or NOT GOOD TO GO
current status
what was proven
what is missing
whether we are blocked
exact next step
whether the user must do anything
```

Do not hide long-running recovery attempts behind vague progress messages.

## Handoff command for the next session

Resume with:

> Read `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29_V2.md` and every item in its required-reading section. Continue from PR #47. Download and inspect artifacts `8729313353` and `8729286115`. Decide whether Tyrone Test Plots 5 and 6 provide exact measured as-built depths, numerical uncertainty, official polygons, matched surfaces, sufficient clean interiors, and a stable Sentinel-1 period. Do not merge PR #47. Do not run Earth Engine until every documentary gate passes. Report GOOD TO GO or NOT GOOD TO GO, the current status, and the exact next step in plain English.
