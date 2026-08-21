# Tyrone depth session handoff V2 — F153 start — 2026-08-20

## Purpose

This is the controlling handoff for the next Tyrone numerical-depth session after the F100–F152 continuity checkpoint.

Read this file first, then the continuity chain listed below. Do not reconstruct the project history from memory and do not restart closed searches.

## Must-read project docs

1. `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V1.md`
2. `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20.md`
3. `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V2_STEP4_REPAIR.md`
4. `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V3_F100_F152_CHECKPOINT.md`
5. this file: `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V2_F153.md`

The project source and documented prior results are authoritative. If a connector cannot open a local-only project source, call that a tool-access limitation; do not assume the source is missing and do not ask the user to recreate already-documented project history.

## User working rules that must continue

For every meaningful step, report three things explicitly:

- **what was done**;
- **current status**;
- **exact next action**.

Also preserve these safeguards:

- do not change the classifier;
- do not change unrelated UI;
- do not change the NB formula;
- do not enable the failed scalar interpolation path;
- do not use known Tyrone depth answers to fit, vertically shift, tune, select or rescue a candidate historical surface;
- no new email request and no payment/purchase unless the user explicitly approves it;
- do not restart random satellite-feature hunting;
- do not repeat closed BER/CQAR/CAES/GPS/public-archive searches unless genuinely new evidence identifies a new source.

## Original direct-elevation plan and exact position

The physical plan remains:

1. inspect drawings for old + final ground;
2. compare 2008 as-built with 2018 lidar;
3. identify useful historical imagery/elevation source;
4. recover/build trustworthy immediate post-grading / pre-cover 3X surface;
5. align old/new surfaces on stable ground;
6. compute `new surface - old/pre-cover surface`;
7. validate on TP5/TP6/TP7;
8. if valid, test TP1/TP2/TP3 and the 43 test pits.

Current position:

> **STEP 4 REPAIR — STILL BLOCKED.**

Steps 5–8 remain **NOT REACHED**, not failed.

## What had already been completed before this handoff

The continuity chain records all prior work. Important conclusions that must not be rediscovered:

- the free medium-resolution 1996 NAPP stereo reconstruction failed the frozen historical-surface accuracy gate before depth holdouts were used;
- the actual 2004 post-grading/pre-cover surface was not recovered from EMNRD records or the public web;
- known CQAR sheets are final/as-built, not pre-cover;
- the actual CQAR drawings prove a 17-sheet native M3 DWG set existed;
- exact M3 project number `03141.01` and known `3X_DCQAR_*.dwg` fingerprints are documented;
- a May-3-2004 PDTI Engineering mine-wide AutoCAD topographic dataset existed and was converted to TINs and 25 ft × 25 ft raster grids, but it predates the September-2004 grading and therefore is not automatically the immediate pre-cover surface;
- 3X grading used CAES plus conventional GPS;
- the admissible construction-window search was narrowed to approximately **after grading began in September 2004 and before cover placement in May 2005**;
- the statewide 2005/2006 New Mexico DTM was closed as a pre-cover candidate because its documented summer-2005 acquisition window is too late;
- EDAC/PWT, late-2004 federal aerial, pre-cover LiDAR, MWH cost-model, public MMD GIS, contractor/vendor and other branches recorded in V2/V3 did not recover the needed surface.

Do not restart those branches from scratch.

## What this session did

### 1. Corrected continuity/history confusion

The session initially had confusion between:

- the original direct-elevation unknown-depth plan;
- the failed 1996 stereo attempt;
- the later effort to **repair Step 4** by finding the true 2004 post-grading/pre-cover surface;
- the separate Route A recorded-depth product path.

The corrected interpretation is:

- the prior session did **not** simply stop after the 1996 failure;
- it actively tried to repair Step 4;
- Steps 5–8 were never validly reached;
- Route A is separate and does not solve unknown-zone depth.

### 2. Added permanent continuity protection

PR #121 added:

`docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20.md`

Purpose: stop future sessions from asking for project sources again, reconstructing history from assumptions, or restarting closed work.

### 3. Re-inspected actual CQAR project-source images

The uploaded/project-source drawing set was directly inspected.

Verified facts already persisted in V2 continuity:

- `3X CQAR-004 R0` — `TAILING DAM 3X — POSTCONSTRUCTION SITE OVERVIEW`, Sheet 5 of 17;
- `3X CQAR-006 R0` — `NORTH TOPOGRAPHY`, Sheet 7 of 17;
- `3X CQAR-007 R0` — `SOUTH TOPOGRAPHY`, Sheet 8 of 17;
- `3X CQAR-010 R0` — `AREA FOOTPRINTS`, Sheet 11 of 17;
- all are AS-BUILT dated 07/17/08;
- M3 project `03141.01`;
- native source paths such as `P:\2003\03141.01\Civil\3X\3X CQAR\3X_DCQAR_004_R0.dwg` are printed on the drawings;
- known 006/007 cross-reference only points to each other;
- no hidden pre-cover/subgrade reference was found on the four known sheets.

Do not re-run this inspection unless genuinely new drawings appear.

### 4. Discovered that the stronger Step-4 progress was already persisted

PR #122 was found already merged on `main`:

`docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V2_STEP4_REPAIR.md`

That document contains the extended Step-4 research through the May-2004 AutoCAD/TIN/grid trail, Bill Seibert/PDTI GIS evidence, M3/DWG searches, grading limitations, archive checks and closed branches.

### 5. Persisted the missing F100–F152 chronology

The user supplied the later session chronology through F152, which had not been visible in the repo continuity chain.

PR #123 was created and merged to `main` with:

`docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V3_F100_F152_CHECKPOINT.md`

Merge commit:

`2397f232f7924b09163c9b7605542537b94a3530`

That checkpoint records the construction-photo timing work, 2005 DTM closure, narrowed construction window, MMD GIS branch, and the newest ICESat-1 / GLAS candidate.

## Newest candidate at handoff: ICESat-1 / GLAS

The newest physically independent direct-elevation source is **ICESat-1 / GLAS laser altimetry**, not a radar/surface-signature feature.

Checkpoint facts carried from F151–F152:

- Laser 3A operated approximately **3 Oct–8 Nov 2004**;
- this lies inside the useful post-grading / pre-cover construction window;
- NASA/NSIDC land product identified as **GLAH14 Version 34**;
- reported collection identifier: `C2153551318-NSIDC_CPRD`.

Important:

> A GLAS crossing of 3X has **NOT** yet been proven.

Do not claim the branch is useful until the actual footprint/track geometry is spatially verified.

## F153 work completed in this session

### Real 3X geometry loaded

The next-session screen must use real project geometry, not an approximate Tyrone point.

The session fetched:

`data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`

This contains WGS84 polygons for TP1/TP2/TP3/TP5/TP6/TP7 derived from the official as-built drawing geometry.

For the top-surface test-plot group, the project geometry lies approximately around:

- latitude: `32.7201` to `32.7234` N;
- longitude: `-108.4192` to `-108.4167` W.

Use the geometry only for the GLAS coverage screen. The same file contains measured depth values; **do not use those depth values during the coverage/geometry screen**.

### NASA query status

The session reached the point of preparing a direct NASA/NSIDC GLAH14 spatial query for the Laser-3A date window.

The spatial query/result itself was **NOT completed before handoff**.

Therefore the GLAS branch is currently:

> **UNRESOLVED — spatial crossing unknown.**

## Exact first action for next session

### F153 — complete the GLAH14 spatial crossing test

1. Read the continuity chain first.
2. Load the WGS84 3X geometry from:
   `data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`.
3. Query NASA/NSIDC GLAH14 V34 for approximately `2004-10-03` through `2004-11-08` over the 3X footprint / a small surrounding buffer.
4. Determine whether any GLAS footprint/ground track:
   - intersects 3X;
   - intersects the top-surface area relevant to TP5/TP6/TP7; or
   - passes only nearby.
5. Report the actual minimum distance / number of shots / dates if available.
6. Do **not** reveal or use Tyrone measured depth holdouts during this screen.

### Decision rule

If **no GLAS shot/track intersects the usable 3X area**:

- close the ICESat-1 / GLAS branch immediately;
- document that closure;
- do not attempt interpolation from distant GLAS tracks.

If **GLAS shots intersect 3X**:

- inspect shot count and spacing;
- inspect quality flags;
- inspect horizontal geolocation uncertainty;
- inspect saturation/cloud/reflectivity flags as appropriate;
- inspect elevation correction fields/datum;
- determine whether the shots fall on usable bare/graded terrain rather than slopes/structures;
- only then decide whether the observations could contribute independent pre-cover control.

A few nearby shots must **not** be promoted to a full pre-cover surface.

## Frozen scientific gate remains unchanged

Do not loosen any historical-surface acceptance threshold after seeing results.

The frozen gate still includes the previously documented requirements such as:

- historical-surface `RMSEz <= 0.15 m`;
- absolute median vertical residual `<= 0.05 m`;
- 95th-percentile absolute vertical residual `<= 0.30 m`;
- residual-plane drift `<= 0.10 m` across the 3X footprint;
- independent depth validation only after the historical-surface gate passes.

Known depth measurements are holdout truth only, not fitting inputs.

## Route A status — keep separate

Route A is the reviewed recorded-depth lookup for exact known zones.

In the earlier part of the session:

- a real existing Tyrone run was selected: `0900d49a-9a9a-41ae-a193-52140e773613`;
- classifier files were hashed/frozen before Route A testing;
- the recorded-depth package was successfully built under `private\tyrone-recorded-depth`;
- no existing depth folder was present at the start;
- the actual existing-run Route A execution/verification step was **not completed** before the session switched back to the original Step-4 repair path.

Do not silently switch to Route A in the next session. Continue F153 unless the user explicitly asks to change routes.

## Current scientific status at handoff

- Original unknown-zone direct-elevation plan: **BLOCKED at Step 4 repair**.
- Step 5 alignment: **NOT REACHED**.
- Step 6 subtraction: **NOT REACHED**.
- Step 7 TP5/TP6/TP7 validation: **NOT REACHED for the elevation method**.
- Step 8 TP1/TP2/TP3 + 43-pit validation: **NOT REACHED**.
- 1996 free NAPP reconstruction: **CLOSED for numerical depth**.
- 2005 statewide DTM: **CLOSED as pre-cover source**.
- public 2004 native construction-surface recovery: **not recovered**.
- ICESat-1 / GLAS Laser-3A: **ACTIVE SCREEN, crossing not yet known**.
- Route A recorded known-depth lookup: **separate; package built, real-run verification still unfinished**.
- classifier/UI/NB formula: **unchanged**.

## Next-session opening message should be simple

The next session should tell the user, in simple English:

> We are at F153. I am not repeating the old searches. The next job is only to check whether an Oct–Nov 2004 ICESat/GLAS laser track actually crossed 3X. If it did not, this route closes. If it did, we inspect the actual laser shots before doing anything with depth.

Then proceed with the spatial query.
