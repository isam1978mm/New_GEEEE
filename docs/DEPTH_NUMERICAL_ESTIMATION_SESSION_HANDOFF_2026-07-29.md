# Numerical depth estimation — session handoff — 2026-07-29

## Start here

This document is the authoritative handoff for the next session.

The next session must read the required-reading section before searching, running Earth Engine, changing the app, reopening a closed candidate, or changing the selected strategy.

## Plain-English status

**Numerical depth is still NOT GOOD TO GO.**

The combined plan remains active:

- **Option 5 — Change Target:** useful radar anomaly output is implemented and merged.
- **Option 1 — Global Depth:** strict documentary calibration search continues.
- **Option 4 — Local AOI Calibration:** available, but inactive until one AOI provides a complete shallow/deep/control package.
- **Option 3 — Complete Candidates:** Tyrone Dam 3X remains pending while waiting for the New Mexico EMNRD records response.

No numerical depth result is enabled.

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

The foreground task stopped at the decisive review of the **Syncrude 1990 tailings capping study**.

What is currently promising:

- nominal cover-depth treatments of approximately 30 cm, 50 cm and 70 cm;
- public summaries state that post-construction soil analysis found good control of the placed thickness;
- the study may contain stronger construction evidence than the recently rejected landfill candidates.

What has not yet been proven:

1. plot dimensions large enough to retain at least 30–40 m clean radar interiors;
2. exact mapped or coordinate-tied plot geometry;
3. actual final measured treatment depths with numerical variability or uncertainty;
4. matching surface material, slope, grading and vegetation across a clean depth pair;
5. proof that the plots remained intact and stable during the Sentinel-1 era after 2014.

**Immediate next action:** recover and inspect the full Syncrude report and later site records for those five items. Do not run radar values first.

## Parallel active routes

### 1. Aurora Soil Capping Study — active recovery route

PR #41 is open as a temporary recovery-only PR:

- PR: `#41`
- branch: `agent/aurora-cover-study-recovery-20260728`
- state: open draft
- merge: **do not merge**

Aurora is one of the strongest designs found:

- 36 replicated one-hectare cells;
- published treatment layout;
- numerical cover-depth designs;
- promising matched pair:
  - Treatment 10: 30 cm peat + 120 cm blended B/C subsoil = 150 cm total;
  - Treatment 11: 30 cm peat + 70 cm blended B/C subsoil = 100 cm total;
- same nominal surface material and same nominal subsoil type for that pair;
- long monitoring history and a usable post-construction Sentinel-1 period.

Remaining Aurora blockers:

- the public papers cite, rather than reproduce, the decisive 2013 construction/as-built report;
- exact coordinate-tied cell polygons are not yet recovered in usable form;
- final measured as-built depths and numerical construction uncertainty are not yet public;
- the public watershed database is permission-controlled.

Next Aurora action:

- finish inspecting the recovered Korbas thesis, HESS paper, rendered treatment map and any public supporting datasets;
- search specifically for measured installed profile depth, cell corners, GIS geometry, construction tolerances or field variability;
- close PR #41 without merge if those items cannot be recovered.

### 2. Tyrone Dam 3X — external-record wait

New Mexico EMNRD GovQA request:

```text
reference = N000019-070026
submitted = 2026-07-28
status = pending
```

The request seeks the June 2008 3X construction-quality report, appendices, survey/GIS/CAD records and post-2014 stability records.

Strong Tyrone evidence already available:

- Test Plot 5 measured mean: 26.8 inches;
- Test Plot 5 95% interval: 25.8–27.8 inches;
- Test Plot 6 measured mean: 37.4 inches;
- Test Plot 6 95% interval: 33.5–41.3 inches;
- both plots are full-scale and use the same broad cover-material and revegetation program.

Remaining Tyrone blockers:

- exact coordinate-tied Test Plot 5/6 polygons;
- exact plot-specific stable Sentinel-1 observation period;
- a defensible confirmed control if Tyrone is to support Option 4;
- the missing June 2008 3X CQA/as-built package.

When the response arrives:

1. preserve the original files unchanged;
2. inventory every file and page;
3. inspect survey coordinates, CAD/GIS layers, measured final thicknesses, uncertainty and stability records;
4. decide separately whether Tyrone can support:
   - one Option 1 positive site group;
   - an Option 4 shallow/deep/control package;
5. do not create a calibration row until all required gates pass.

### 3. Faro Mine pilot — active near-miss

The Faro Landform, Cover and Revegetation Pilot remains promising but not ready.

What passes:

- 15 full-scale panels constructed in 2022;
- nominal 0.3 m, 0.6 m and 1.0 m treatments;
- GPS-controlled grading and construction quality-control procedures;
- vegetation and continuing activity visible through 2025;
- possible 0.6 m versus 1.0 m comparison.

What is missing:

- exact public panel design matrix proving a truly matched pair;
- coordinate-tied panel boundaries;
- actual final measured panel thicknesses;
- numerical uncertainty or tolerance tied to each panel;
- proof that material, slope, placement method and revegetation match for the selected pair.

Reopen only to recover those exact records.

### 4. Aitik WRD6 trial — active near-miss

What passes:

- two adjacent plateau trials, each approximately 50 m × 50 m;
- same nominal 0.3 m surface layer;
- same nominal 0.3 m compacted layer;
- middle till thickness differs, producing approximately 1.6 m versus 2.1 m total covers;
- constructed in 2013;
- 2025 reporting indicates continued monitoring and good performance.

What is missing:

- official surveyed trial corners or coordinate-tied polygons;
- final measured as-built thickness values;
- numerical construction uncertainty;
- exact exclusions for monitoring infrastructure and clean interiors.

Aitik reached a hard public-record blocker. Do not approximate its geometry from satellite imagery.

## Work completed in this session

### Option 5 implementation — merged

PR #35 was merged.

Main result:

- the app exposes the existing PCA anomaly summaries in the established classifier-results area;
- the panel is labelled `Radar anomaly review — NOT DEPTH`;
- output includes object count, total object area, median anomaly, strongest anomaly and ranked objects;
- the score is explicitly described as unitless, within-run only, not probability, not physical confirmation, not measured change and not a depth estimate;
- `Depth estimate: not available` remains preserved;
- no depth stage, calibration row, model training or Earth Engine change was introduced.

Verification at merge:

```text
frontend production build = passed
full test suite = 1150 passed, 31 skipped
committed SPA assets = synchronized
```

Relevant merged document:

- `docs/OPTION1_OPTION5_COMBINED_PLAN_START_2026-07-28.md`

### Option 1 batches 1–4 — merged documentary results

Twenty new candidates were screened in four bounded batches. No candidate passed.

Merged PRs:

- PR #36 — Batch 1;
- PR #37 — Batch 2;
- PR #38 — Batch 3;
- PR #39 — Batch 4.

Batch finalists and fatal blockers:

- Olympic View: repeated one cover profile or different cover assembly; no two measured as-built depth polygons.
- Lowry Landfill: broad/minimum-only thickness statements; no mapped measured pair or uncertainty.
- Fort Dix: engineered cap versus existing landfill cover; not a confirmed control; no measured pair or equivalent surface history.
- Mather AFB: two capped landfill areas, but no coordinate-tied measured depths or uncertainty; Site 4 is a consolidation landfill with added infrastructure.

No Option 1 Earth Engine query was run for any batch.

### Deep-recovery phase after Batch 4

The workflow changed from repeated low-yield five-candidate batches to deep recovery on strong near-misses.

#### Detour Lake Mine — closed

PR #40 was closed without merge.

What was proven:

- 10-hectare operational trial;
- 13 plots;
- nominal 0, 0.3, 0.7 and 1.0 m treatments;
- construction in 2019;
- five years of monitoring and generally stable performance.

Why it failed:

- thickness is confounded with slope, aspect, surface grading, peat content and revegetation;
- no clean matched pair differing mainly by depth;
- no usable coordinate-tied plot polygons;
- no published final measured thicknesses with numerical uncertainty.

#### Silver Bow Creek floodplain remedy — closed

PR #42 was closed without merge.

What was proven:

- approximately 1,550 restored acres;
- reach-level completion mapping;
- excavation to predetermined design depths;
- verification sampling and long-term monitoring.

Why it failed:

- no public actual final measured depths for two broad zones;
- no coordinate-tied depth polygons;
- no numerical as-built uncertainty;
- no clean matched pair where depth is the principal difference.

#### John Sevier Bottom Ash Pond — closed

PR #43 was closed without merge.

What was proven:

- the exact official TVA History of Construction report was recovered;
- large closure area completed and capped in 2017;
- coordinate-controlled subgrade plan;
- surveyed final-grade drawings;
- continuous sod and long-term closure infrastructure.

Why it failed:

- one continuous cap system only;
- no second final depth condition;
- subgrade contours are design/proposed rather than an explicit final measured as-built thickness surface;
- no coordinate-tied absolute thickness values or numerical uncertainty.

#### Faro Mine — kept as near-miss

Not rejected, but blocked by the missing exact matched-panel matrix, polygons and measured final thickness uncertainty.

#### Syncrude 1990 — current foreground candidate

This is the precise place where the next session should resume.

## Historical routes that must not be repeated

### Option 2 RMA ordering test — closed inconsistent

PR #34 was closed without merge.

Validated result:

```text
acquisitions = 82
usable months = 33
3-foot zone above 2-foot zone = 20/33 months = 60.6%
Wilson 95% interval = 0.4368 to 0.7532
median monthly difference = +0.3678
positive seasons = 2/4
final decision = ordering_inconsistent
```

The QA passed. The failure was seasonal inconsistency, not missing radar data.

Do not:

- cherry-pick summer/fall;
- reverse the expected direction after seeing results;
- change the metric post hoc;
- use paid imagery to rescue this specific failed test;
- create a calibration row from RMA.

### Option 4 feasibility — tested, not ready

Public evidence was tested first. Neither Tyrone nor Sconondoa currently supplies a full three-zone local package.

Required local package:

- measured shallow reference;
- measured deeper reference;
- confirmed control;
- exact polygons;
- comparable surfaces;
- enough clean pixels;
- stable observation period.

No Option 4 Earth Engine query has run.

## How the work was done

The next session must use the same evidence-first workflow.

### Step 1 — cheap documentary screen before radar

Reject immediately when any fatal condition is clear:

- construction incomplete;
- no post-construction Sentinel-1 period;
- only one cover/depth condition;
- candidate is covered versus uncovered rather than two numerical conditions;
- clean interior below about 30–40 m after exclusions;
- surfaces, slope, material, vegetation or grading are obviously different;
- active reconstruction or disturbance invalidates stability.

### Step 2 — decisive official-record review

Only survivors receive deep review for:

- final measured as-built depth, not merely design or minimum thickness;
- numerical uncertainty, interval, tolerance or survey accuracy;
- coordinate-tied polygon geometry;
- an exact second depth condition or confirmed control;
- matching radar-facing near-surface construction;
- stable post-construction observation dates;
- sufficient clean interior after excluding roads, drains, instruments, swales and boundaries.

### Step 3 — fail closed

If the document is not public or does not expose the required measurement, mark the candidate as a near-miss or external-record blocker. Do not infer a pass.

Examples of prohibited substitutions:

- design depth for measured as-built depth;
- broad site boundary for treatment polygon;
- nearby land for a confirmed control;
- satellite-estimated corners for official geometry;
- qualitative `good construction control` for numerical uncertainty;
- one landfill area for a negative control merely because its cover differs.

### Step 4 — use isolated recovery PRs only when necessary

Temporary recovery branches may download large official or open-access records and extract searchable text or figures.

Rules:

- label the PR `recovery only` or `do not merge`;
- do not add recovery workflows to main;
- close the PR without merge after the decision;
- preserve official files and hashes in artifacts when possible;
- record the final pass/fail reason in the PR body or a main-branch result document.

### Step 5 — radar only after documentary pass

For Option 1, do not run Earth Engine merely because a site is promising.

A candidate must first pass:

```text
full-scale clean zones = yes
final measured numerical depths = yes
numerical uncertainty = yes
coordinate-tied geometry = yes
matched radar-facing surfaces = yes
exact second depth or confirmed control = yes
stable Sentinel-1 period = yes
```

Only then:

1. preregister the radar comparison;
2. execute the bounded query;
3. validate spatial and temporal QA;
4. decide whether a calibration record is defensible.

One successful site is not enough for a global model.

## Required reading for the next session

Read these in order.

### Canonical strategy and active combined plan

1. `docs/DEPTH_NUMERICAL_ESTIMATION_OPTION_REFERENCE.md`
2. `docs/OPTION1_OPTION5_COMBINED_PLAN_START_2026-07-28.md`
3. `docs/DEPTH_OPTION4_LOCAL_AOI_FEASIBILITY_RESULT_2026-07-28.md`

### Tyrone pending route

4. `docs/DEPTH_OPTION3_TYRONE_DAM3X_DECISIVE_RECORD_RECOVERY_RESULT_2026-07-28.md`
5. PR #33 body and discussion — closed recovery, records request still pending

### Option 1 merged batches

6. `docs/DEPTH_OPTION1_GLOBAL_BATCH1_CHEAP_SCREEN_2026-07-28.md`
7. `docs/DEPTH_OPTION1_GLOBAL_BATCH1_FINAL_RESULT_2026-07-28.md`
8. `docs/DEPTH_OPTION1_GLOBAL_BATCH2_CHEAP_SCREEN_2026-07-28.md`
9. `docs/DEPTH_OPTION1_LOWRY_LANDFILL_DECISIVE_RESULT_2026-07-28.md`
10. `docs/DEPTH_OPTION1_GLOBAL_BATCH3_CHEAP_SCREEN_2026-07-28.md`
11. `docs/DEPTH_OPTION1_FORT_DIX_DECISIVE_RESULT_2026-07-28.md`
12. `docs/DEPTH_OPTION1_GLOBAL_BATCH4_CHEAP_SCREEN_2026-07-28.md`
13. `docs/DEPTH_OPTION1_MATHER_AFB_DECISIVE_RESULT_2026-07-28.md`

### Closed experimental/recovery PRs

14. PR #34 — RMA ordering test, closed inconsistent
15. PR #40 — Detour Lake, closed without merge
16. PR #42 — Silver Bow, closed without merge
17. PR #43 — John Sevier, closed without merge

### Active recovery PR

18. PR #41 — Aurora recovery only, open draft, do not merge

### This handoff

19. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29.md`

## Next steps

### Immediate — Syncrude 1990

1. Recover the full 1994 capping-study report and later follow-up records.
2. Extract the exact experimental layout and plot dimensions.
3. Determine whether any 30/50/70 cm pair is at least 30–40 m wide after exclusions.
4. Recover measured post-construction thickness statistics, not just nominal design values.
5. Recover numerical spread, tolerance, confidence interval or survey accuracy.
6. Confirm matching cover material, surface treatment, slope and revegetation.
7. Confirm plot survival and stability through a post-2014 Sentinel-1 period.
8. Issue one clear decision:
   - `GOOD TO GO for documentary radar screen`, or
   - `NOT GOOD TO GO`, with the first fatal blocker.

### Parallel — finish Aurora PR #41

1. Inspect all recovered text and figures.
2. Recover exact cell geometry and installed-depth statistics if present.
3. Test the 100 cm versus 150 cm matched pair.
4. Close PR #41 without merge after the final decision.

### External wait — Tyrone

1. Monitor GovQA request `N000019-070026` manually when a response arrives.
2. Process the package immediately using the Tyrone steps above.

### After the first documentary pass

1. Create a dedicated candidate branch.
2. Write a preregistered radar protocol before viewing values.
3. Run one bounded Earth Engine comparison.
4. Keep depth disabled unless the evidence and radar result both pass.
5. Record one candidate group only; do not start training.

## Short roadmap

### Roadmap A — useful app now

- Option 5 anomaly output remains available in the app.
- Preserve the `NOT DEPTH` language and no-depth contracts.
- Do not relabel anomaly as depth, probability, confirmation or measured change.

### Roadmap B — first defensible calibration site

- finish Syncrude;
- finish Aurora;
- process Tyrone response;
- reopen Faro or Aitik only for their specifically missing as-built/geometry records.

Goal: one fully documented candidate group. This still will not enable global depth.

### Roadmap C — global depth dataset

After the first pass, repeat only with independent sites until there are separate:

- training groups;
- validation groups;
- untouched holdout groups;
- confirmed negative/control groups.

No site or group may be reused across splits.

### Roadmap D — app depth enablement

Enable numerical depth only after:

- enough independent rows exist;
- training succeeds;
- validation succeeds;
- holdout performance is acceptable;
- uncertainty and applicability limits are exposed in the app;
- the output cannot be confused with Option 5 anomaly.

## Things the next session must not do

- Do not discuss or depend on historical notebook parity unless the user explicitly requests it.
- Do not restart random broad candidate batches before finishing Syncrude and Aurora.
- Do not reopen closed candidates without new concrete evidence.
- Do not use nominal design thickness as calibration truth.
- Do not assume a control area.
- Do not draw approximate treatment polygons and call them official.
- Do not run Option 1 Earth Engine analysis before the documentary gate passes.
- Do not train a model with zero or one usable site group.
- Do not enable depth in the app.
- Do not remove or weaken the Option 5 `NOT DEPTH` wording.

## Repository and PR state at handoff

```text
main baseline after merged Option 1 Batch 4 = 31ceaa97b0e6fc1036956b1b2f7ebbf95bb8d771
PR #35 Option 5 anomaly foundation = merged
PR #36 Option 1 Batch 1 = merged
PR #37 Option 1 Batch 2 = merged
PR #38 Option 1 Batch 3 = merged
PR #39 Option 1 Batch 4 = merged
PR #40 Detour recovery = closed, unmerged
PR #41 Aurora recovery = open draft, do not merge
PR #42 Silver Bow recovery = closed, unmerged
PR #43 John Sevier recovery = closed, unmerged
```

## Handoff command for the next session

Resume with:

> Read `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29.md` and every item in its required-reading section. Continue the strict Option 1 search from the Syncrude 1990 capping study. Finish Syncrude first, finish Aurora PR #41 in parallel, and keep Tyrone pending. Do not run Earth Engine until one candidate passes every documentary gate. Always report `GOOD TO GO` or `NOT GOOD TO GO`, current status and the exact next step in plain English.
