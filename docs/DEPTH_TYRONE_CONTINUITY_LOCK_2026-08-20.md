# Tyrone depth continuity lock — 2026-08-20

## Purpose

This file exists to prevent future sessions from reconstructing the Tyrone depth history from memory, repeating closed work, or asking the user to re-upload files that are already in the project source.

**Read this file and `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V1.md` before doing any new Tyrone depth work.**

The project source and prior documented results are authoritative. Do not replace them with assumptions.

## Mandatory continuity rules

1. **Do not assume a source is missing just because a connector cannot open it.** First check the project-source inventory and prior inspection notes.
2. **Do not ask the user to re-upload a source already listed below.** If the current tool cannot access a local-only source, state that as a tool-access limitation and use the documented prior inspection. Ask for user action only if genuinely new information is required.
3. **Do not restart broad discovery.** Continue from the exact current scientific step below.
4. **Do not silently switch routes.** The direct-elevation plan and Route A recorded lookup are separate.
5. **Do not change the classifier, unrelated UI, NB formula, or failed interpolation method.**
6. **No new email request and no payment unless the user explicitly changes that instruction.**
7. For every meaningful step, report:
   - what was done;
   - current status;
   - exact next action.
8. When evidence is unavailable, say `not recovered` or `tool cannot access it`; do not infer a missing sheet/file name from numbering alone.

## Project sources already present / already known

The user's local project source contains the following Tyrone material. These are not hypothetical leads.

### CQAR drawing images already in project source

- `data/research/tyrone_3x_cqar_drawings/3X_CQAR_004_R0__page_0001.png`
- `data/research/tyrone_3x_cqar_drawings/3X_CQAR_006_007_R0__page_0001.png`
- `data/research/tyrone_3x_cqar_drawings/3X_CQAR_006_007_R0__page_0002.png`
- `data/research/tyrone_3x_cqar_drawings/3X_CQAR_010_R0__page_0001.png`

Prior documented visual inspection established:

- `3X_CQAR_004_R0` = final/as-built 3X topographic overview;
- `3X_CQAR_006_007_R0` = final/as-built north/south topography with mapped cover-depth test pits and depth tables;
- `3X_CQAR_010_R0` = final/as-built area footprints and six test-plot regions;
- these drawings do **not** expose the missing pre-cover/subgrade surface as a separate contour set.

The CQAR drawings expose M3 project number `03141.01`.

**Do not infer that sheets 001-003, 005, or 008-009 contain a pre-cover surface unless an actual drawing index or cross-reference proves it.**

### Public-record source files already in project source

- `data/research/tyrone_3x_public_records/GR010RE_2007_Plate02_Tailing_Area.pdf`
- `data/research/tyrone_3x_public_records/GR010RE_3X_Tailing_Annual_Summary_Report.pdf`
- `data/research/tyrone_3x_public_records/GR010RE_3X_Tailing_AsBuilt_Report.pdf`
- rendered map pages under `data/research/tyrone_3x_public_records/route_b_map_pages/`
- later rendered map pages under `data/research/tyrone_3x_public_records/route_b_map_pages_20260817/`
- historical NAIP/GeoTIFF route-B files and ZIPs under the same research directory.

### 1996 NAPP source already in project/repo history

The verified stereo triplet is:

- `NP0NAPP009519108`
- `NP0NAPP009519109`
- `NP0NAPP009519110`

The split archive containing the free medium-resolution TIFFs is already represented in project data under:

- `data/research/tyrone_napp_1996/Desktop.7z.001`
- `data/research/tyrone_napp_1996/Desktop.7z.002`
- `data/research/tyrone_napp_1996/Desktop.7z.003`

Camera calibration `R2104.PDF` was already verified for camera `124257`, lens `124308`, calibrated focal length `152.773 mm`.

Do not restart calibration-file discovery.

## Original direct-elevation plan and exact status

The physical plan is:

1. inspect existing drawings for old + final ground;
2. compare 2008 as-built with 2018 lidar;
3. identify latest useful pre-September-2004 aerial source;
4. build/recover old or immediate pre-cover surface;
5. align old/new surfaces on stable ground;
6. compute `new surface - old/pre-cover surface`;
7. validate on TP5/TP6/TP7;
8. if valid, test TP1/TP2/TP3 and the 43 test pits.

### Step 0 / drawing check

**DONE — no direct solution.** Existing CQAR plates did not provide a decisive section/profile containing both pre-cover/subgrade and final surface.

### Step 1 / 2004 grading confound

**DONE — grading is a real blocker.** Reclamation included outslope and top-surface grading, drainage work and cover-subbase placement. Therefore a generic older historical surface cannot automatically be called the immediate pre-cover substrate.

### Step 2 / 2008 as-built vs 2018 lidar

**DONE.** The comparison supports 2018 lidar/DEM as the preferred final/current surface candidate and rules out a large multi-metre post-2008 shift. It is not precise settlement proof.

### Step 3 / historical stereo source

**DONE.** The 1996 NAPP triplet and R2104 calibration were identified and acquired.

### Step 4 / old-surface reconstruction and repair

**THE CURRENT BLOCKER.**

The free medium-resolution 1996 NAPP reconstruction was tested under frozen rules and failed the historical-surface accuracy gate before Tyrone depth holdouts were used. Independent surfaces disagreed at roughly metre scale (typical approximately 1.4-2.2 m; held-out RMSE approximately 2.7-4.0 m) versus the frozen `0.15 m` RMSE requirement.

After that failure, the project did **not** simply abandon the plan. It tried to repair Step 4 by recovering the true 2004 post-grading/pre-cover engineering surface.

The public search established that the following existed historically:

- M3 June 2004 `Basic Engineering Report, Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report`;
- Tetra Tech June 2004 `Cover design report: 3X tailings impoundment`;
- 2008 M3 3X CQAR/CQAR design-report trail;
- CAES used for subgrade/final grade control;
- conventional GPS surveys used with CAES;
- historical AutoCAD/topographic survey data existed in the broader Tyrone engineering workflow.

But the actual usable 3X pre-cover/post-grading CAD/TIN/grid/LandXML/CAES/GPS surface was **not recovered** from the public web or EMNRD-produced records.

EMNRD stated no additional responsive records existed beyond the already-produced package. Do not repeat the same EMNRD request/search path unless genuinely new evidence identifies another holding.

### Steps 5-8

**NOT REACHED.** They remain blocked by Step 4. Do not claim they failed; they were not validly run because the required old/pre-cover surface is missing or failed accuracy.

## Current repair target

The exact missing scientific input is:

> a trustworthy 2004 immediate pre-cover/post-grading substrate surface for 3X, or an independently verifiable equivalent surface that can pass the frozen accuracy gate.

Acceptable examples include:

- pre-cover/post-grading CAD/TIN/grid/LandXML;
- CAES design/as-built terrain export;
- GPS survey point list/cloud tied to the 3X control system;
- sufficiently dense and spatially tied pre-cover contours with adequate uncertainty/control metadata.

## What is already closed / do not repeat

- free medium-resolution 1996 NAPP for numerical depth — **CLOSED**;
- free pre-September-2004 NAIP at Tyrone — no suitable scenes — **CLOSED**;
- public Appendix A route for 3X grades — 3X absent — **CLOSED**;
- repeated exact public searches for the June 2004 BER, Tetra Tech report, 2008 CQAR and generic CAES/GPS/TIN filenames — **EXHAUSTED FOR NOW**;
- raw NB proxy to metres — **NOT VALIDATED**;
- failed scalar interpolation — **DO NOT ENABLE**;
- random new satellite-feature hunting — **DO NOT RESTART**.

Paid 14-micron NAPP remains **HELD / NOT APPROVED**.

## Route A is separate

PR #119 implemented a reviewed recorded-depth lookup for exact reviewed zones such as TP5/TP6. It reports existing measurements as `recorded_measurement`, leaves `estimated_depth_*` blank, and abstains for unknown zones.

Route A is useful product work, but it is **not the continuation of Steps 5-8 and does not solve unknown-zone estimation**.

Do not switch from the direct-elevation repair path to Route A without saying explicitly that the route has changed.

## Exact current continuation point

At the time this continuity lock was written:

- direct-elevation unknown-depth plan is still at **Step 4 repair**;
- the known CQAR sources are already in project source and must not be requested again;
- the previous inspection already established the known CQAR plates are final/as-built, not pre-cover;
- M3 project number `03141.01` is verified, but public searches using it did not recover the missing surface;
- the current task is to pursue only genuinely new evidence for the 2004 immediate pre-cover/post-grading surface, while avoiding repeated closed searches and assumptions.

If a future session cannot directly open a local-only source, it must say so and rely on the documented prior result rather than asking the user to recreate project history.
