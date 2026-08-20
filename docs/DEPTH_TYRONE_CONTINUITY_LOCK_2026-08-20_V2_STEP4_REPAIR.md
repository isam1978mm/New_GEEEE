# Tyrone depth continuity lock V2 — Step 4 repair progress — 2026-08-20

## Purpose

This file extends `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20.md` with the additional Step-4 repair work completed after PR #121.

Future sessions must read both continuity-lock files and `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V1.md` before doing new Tyrone depth work.

Do not reconstruct this work from memory. Do not ask the user to re-upload sources listed in the continuity locks. If a tool cannot open a local-only project source, call that a tool-access limitation, not file absence.

## Route position remains unchanged

The original physical direct-elevation plan is still at **Step 4 — recover/build a trustworthy immediate pre-cover/post-grading 3X surface**.

Steps 5-8 have still **not been validly reached**.

Route A recorded-depth lookup remains a separate product path and must not silently replace the direct-elevation repair path.

## Direct inspection of the actual project-source CQAR drawings

The four known CQAR drawing images were inspected again directly at high resolution from the project-source ZIP.

### `3X_CQAR_004_R0`

Verified title:

`TAILING DAM 3X — POSTCONSTRUCTION SITE OVERVIEW`

Verified title-block facts:

- AS-BUILT;
- date `07/17/08`;
- M3 project no. `03141.01`;
- drawing no. `3X CQAR-004 R0`;
- **Sheet 5 of 17 sheets**;
- native plot/source path printed on drawing:
  `P:\2003\03141.01\Civil\3X\3X CQAR\3X_DCQAR_004_R0.dwg`;
- title-block personnel on 03/14/07:
  - Drawn by `DC`;
  - Checked by `TO`;
  - Project Manager `DR`.

The revision history shows post-construction document development/review, ending with `AS-BUILT ISSUED WITH CQAR` on 07/17/08. Therefore the missing sheets in this 17-sheet set must **not** be assumed to be the June-2004 design/pre-cover drawings merely because they are missing from the local four-sheet subset.

### `3X_CQAR_006_R0`

Verified title:

`TAILING DAM 3X — NORTH TOPOGRAPHY`

Verified:

- AS-BUILT;
- drawing `3X CQAR-006 R0`;
- **Sheet 7 of 17 sheets**;
- source DWG family `3X_DCQAR_006_007_R0.dwg`;
- mapped test plots/test pits and cover-depth tables;
- match-line reference only to drawing 007.

### `3X_CQAR_007_R0`

Verified title:

`TAILING DAM 3X — SOUTH TOPOGRAPHY`

Verified:

- AS-BUILT;
- drawing `3X CQAR-007 R0`;
- **Sheet 8 of 17 sheets**;
- same source DWG family as 006;
- match-line reference only to drawing 006.

### `3X_CQAR_010_R0`

Verified title:

`TAILING DAM 3X — AREA FOOTPRINTS`

Verified:

- AS-BUILT;
- drawing `3X CQAR-010 R0`;
- **Sheet 11 of 17 sheets**;
- source path ending `3X_DCQAR_010_R0.dwg`.

### CQAR cross-reference result

The four known sheets do **not** contain a missed reference to a 2004 pre-cover/subgrade drawing. The only sheet-to-sheet cross-reference found is the 006/007 match line.

Do not infer the contents of drawings 000-003, 005, 008-009, or 011+ from numbering. Searches for inferred neighboring drawing/DWG names did not produce public evidence.

## M3 project/personnel fingerprints

M3 project number `03141.01` is verified on the drawings.

Searches for:

- `03141.01` + 3X/Tyrone;
- `M3-PN03141`;
- `PN03141`;
- exact known `3X_DCQAR_*.dwg` filenames;
- exact known sheet titles;
- `DCQAR` archive-path fragments;

did not recover a public M3 drawing/CAD package.

Public M3/SEC resume material identifies **Daniel Roth, P.E.** as M3's `Project Manager / Chief Engineer` for `Freeport McMoRan, Tyrone Mine Tailing Impoundment and Stockpile Reclamation`. This strongly supports title-block `DR = Daniel Roth`.

Do not assign names to `DC` or `TO` without evidence; public searches did not resolve them to a useful Tyrone project description.

## 2004 Tyrone engineering-topography trail — stronger evidence recovered

The official Supplemental Materials Characterization study documents a real mine-wide historical topography workflow:

- source: **PDTI Engineering topographic data in AutoCAD files**;
- source handoff attributed to **D. Benavidez, May 3, 2004**;
- 1995-2004 topography covered the **full Tyrone Mine extent**;
- Tyrone had engineering surveys at least annually since 1995;
- aerial surveys were conducted from 2000 through 2004;
- vector elevation features were converted to **TIN surfaces**;
- TINs were converted to **25 ft x 25 ft raster elevation grids** for topographic/volumetric work.

This is real evidence that a May-2004 mine-wide elevation surface existed.

Important limitation: **May 3, 2004 is before 3X reclamation grading began in September 2004.** It is therefore not automatically the immediate pre-cover/post-grading surface.

The same study says a `2004 surface` was displayed in its cross-sections, but those outputs are stockpile-study cross-sections, not a recovered 3X surface.

Searches for a printed/indexed `3X + 2004 surface/topography` figure did not recover one.

## Bill Seibert / PDTI GIS archive trail

Multiple official Tyrone figures cite:

`Tyrone Mine Coverages, Bill Seibert, 2004`

An independent source identifies Bill Seibert among Phelps Dodge geologists supplying Tyrone technical data. Treat this as an internal Phelps Dodge/Tyrone dataset, not a public commercial survey product.

Related official reports expose historical GIS project paths including:

- `S:\PROJECTS\PDTI_DB_GIS\GIS\...`;
- a 3X-specific project path:
  `S:/PROJECTS/PDTI_DB_GIS/GIS/MXDS/LT05.0045/CONDITION 87/AREA1.MXD`;
- EnviroGroup/PD-0447 GIS paths such as:
  `R:\PD-0447(Phelps-Dodge)\EGL_Directory\GIS_Ops\Project_Files\...`.

This proves the historical PDTI GIS environment contained 3X-specific project data and surface-contour work elsewhere at Tyrone.

It does **not** recover the 3X post-grading/pre-cover elevation surface.

A Condition-82 figure over 3X contains contours, but they are explicitly **groundwater-elevation contours**, not land-surface contours. Do not misuse them.

## 2005 Final Supplemental Materials report

The 2005 Final Report is publicly listed and an indexed transmittal says electronic copies were too large to email and were delivered on CDs.

However:

- no CD/file manifest has been recovered;
- no underlying AutoCAD/TIN/grid file has surfaced;
- an indexed September-2005 figure still cites `Tyrone Mine Coverages, Bill Seibert, 2004`;
- no source-supported evidence of a newer post-grading 2005 terrain dataset has been found.

Do not promote the 2005 report to a post-grading surface source without new evidence.

## 2004 aerial-survey limitation

The public record verifies aerial surveys through 2004, but searches did **not** recover:

- a post-September-2004 survey date;
- an outside survey/photogrammetry contractor;
- a recoverable 2004 stereo/DEM product;
- a late-2004 Tyrone land-surface dataset.

Do not assume `2004 aerial survey` means post-grading.

## Construction grading facts remain decisive

The public 3X construction/as-built report states:

- top-surface grading was described as **minor grading** using a 14H motor grader;
- major regrading occurred on the slopes using D8R dozers;
- CAES was used for grade control/equipment operations;
- conventional GPS surveys complemented CAES.

Searches did not recover a numerical top-surface cut/fill amount, grading tolerance, pre/post-subgrade elevation table, or survey residual adequate to prove the top-surface grading was below the frozen elevation-error gate.

Therefore `minor grading` must **not** be assumed to mean `<0.15 m`.

The June-2004 Tetra Tech cover-design report remains cited publicly, but public records do not reproduce a grading surface, spatial cut/fill geometry, or exact 3X grading-plan DWG.

## Later-citation / DWG searches

A useful Tyrone precedent exists for another facility: a Golder report cites an exact grading CAD filename, `2a-2b REGRADE PLAN_rev1.dwg`.

Using that precedent, searches were performed for 3X variants of:

- `REGRADE PLAN`;
- `GRADING PLAN`;
- `SUBGRADE PLAN`;
- design topography;
- `.dwg`;
- exact M3 project no. `03141.01`.

No source-supported 3X grading-plan filename surfaced.

This branch is exhausted unless a genuinely new document names a 3X grading/design file.

## 2012 retention warning

A 2012 Tyrone reclamation-cost study says M3 could provide intermediate field-data surfaces for two stages of the 7A Far West Stockpile, but states that the `intermediate construction data needed to enable a similar calculation is not available` for other reclaimed features at Tyrone.

This statement is **not specific enough to prove the 3X CAES/GPS files were destroyed or never retained**. Do not overstate it.

But it materially weakens any assumption that a later regulatory file will necessarily contain the 3X intermediate construction surface.

## 2023 WSP 3X drawing check

A 2023 WSP Task-3 precipitation-analysis report contains a drawing titled:

`TYRONE 3X TAILING IMPOUNDMENT AS-BUILT`

The web index describes a legend including `existing/regraded contours`.

The public PDF is too large/unreliable for the current web viewer and direct runtime download failed. Searches of indexed text did not recover:

- a legacy M3 source drawing;
- a survey date/source;
- client-supplied CAD filename;
- LiDAR/DEM source tied to the legacy reclamation surface.

Do not infer what dates the `existing/regraded contours` represent without direct source evidence.

## Public M3 archive/personnel result

M3's current portfolio confirms it was Project Manager and Engineer of Record for design/implementation of Tyrone tailing-dam reclamation.

Public Daniel Roth resumes confirm the Tyrone reclamation project role but do not name the 3X grading model, BER drawing set, survey deliverables, or CAES files.

Searches of archived/current M3 portfolio material did not expose the missing design package.

## Regulatory/financial-assurance trails checked

Exact permit actions `Modification 06-6` and `Modification 07-1` were identified as partial financial-assurance releases involving 3X.

The current EMNRD archive does not expose the original 2006-2008 approval/application files. Later linked financial-assurance PDFs could not be read reliably by the current tools and exact-filename searches did not reveal 3X survey/grading attachments.

Do not repeat broad searches of these modification IDs unless a new archive location appears.

## Current scientific status after this addendum

Still **BLOCKED at Step 4**.

### Proven

- final/current surface candidate exists;
- 3X construction used CAES + GPS grade control;
- a May-2004 mine-wide AutoCAD/TIN/grid topographic dataset existed;
- an internal Phelps Dodge/PDTI GIS environment with 3X-specific projects existed;
- the known CQAR set contains at least 17 sheets and the four project-source sheets are postconstruction/as-built;
- exact M3 project/DWG fingerprints are known.

### Not recovered

- immediate post-grading/pre-cover 3X surface;
- usable 3X CAES/GPS point/surface export;
- spatially tied 3X grading-design surface proven equivalent to as-graded substrate;
- numerical top-surface grading correction/tolerance sufficient to convert May-2004 topography into immediate pre-cover surface;
- full 17-sheet CQAR index/package;
- late-2004 post-grading aerial/topographic survey.

### Steps 5-8

Remain **NOT REACHED**, not failed.

## Exact continuation rule

Do not repeat:

- CQAR four-sheet inspection;
- exact known DWG filename searches;
- `03141.01` / `M3-PN03141` searches;
- generic BER/Tetra Tech/CQAR searches;
- Bill Seibert/May-2004 generic discovery;
- 06-6/07-1 broad search;
- generic CAES/vendor-publication search;
- Greystone/DBS&A/ARCADIS organizational speculation.

Continue only if a genuinely new source can provide one of:

1. a 3X-specific post-grading/pre-cover surface;
2. an exact 3X grading/design drawing or CAD filename not already searched;
3. a late-2004 survey/aerial product after grading and before cover placement;
4. quantitative top-surface grading data accurate enough to transform the May-2004 surface without using depth holdouts;
5. a new archive/custodian that is not the already-exhausted EMNRD public/records path.

No classifier/UI/NB/depth-logic changes are authorized by this document.
