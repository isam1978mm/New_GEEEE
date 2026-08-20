# Tyrone Pre-Cover Surface Recovery Closed; Stereo Aerial Fallback Active — 2026-08-19

## Decision

The easy/best elevation-difference route that depended on recovering an original Tyrone 3X pre-cover/subgrade electronic survey surface from EMNRD is **CLOSED as an EMNRD records-recovery path**.

Numerical depth remains **BLOCKED**. No classifier, UI, or NB formula changes are authorized or made by this decision.

The elevation-difference strategy remains the preferred physically direct replacement route, but two recovery branches are now active:

1. recover the June 2004 3X engineering/pre-cover surface from a different custodian, especially M3 Engineering or Freeport-McMoRan;
2. reconstruct a 1996 NAPP stereo surface and test whether it is accurate enough, and sufficiently uncontaminated by later grading, to support depth.

The 1996 surface must **not** be assumed to equal the cover subgrade without passing the frozen validation gates below.

## EMNRD evidence

A narrow follow-up IPRA request was submitted on 2026-08-19:

- request: `N000031-081926`
- target: original electronic pre-cover/subgrade and final/post-cover survey/design deliverables for Tailing Impoundment 3X
- requested native formats included CAES, GPS, CAD, GIS, TIN, LandXML, point/coordinate tables, surface files, DWG/DXF, shapefiles/geodatabases, plus survey-control and datum/accuracy metadata
- the request explicitly referenced the June 2004 3X Basic Engineering Report and the 2008 CQAR and asked for underlying electronic surfaces rather than duplicate PDFs

EMNRD/MMD replied on 2026-08-19 that all records responsive to the request had already been uploaded under `N000019-072826` and that no additional documents exist.

The earlier request `N000019-072826` had already been used to recover the available Tyrone 3X package. MMD stated on 2026-08-05 that 95 attachments were associated with that request, and on 2026-08-07 confirmed that no additional records existed beyond what had already been provided.

Therefore the project must not keep treating another EMNRD search for the same 3X native electronic surfaces as the active numerical-depth path unless genuinely new evidence identifies a different EMNRD holding.

## Historical engineering data are documented to have existed

Official Tyrone records establish that suitable historical topographic data once existed:

- `M3, 2004d`: **Basic Engineering Report, Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report**, prepared for Phelps Dodge Tyrone, Inc., June 2004, before 3X reclamation began.
- Tyrone Supplemental Materials Characterization records state that PDTI Engineering supplied mine-wide topographic data in AutoCAD files for 1995–2004, with annual surveys from 1995 and aerial surveys from 2000–2004.
- Those vector elevation features were used to create TIN surfaces and 25 ft × 25 ft raster elevation grids for topographic/volumetric analysis.

The current project package does not contain the needed native pre-cover surface.

## New grading-contamination finding: 1996 is not automatically the cover subgrade

Later official Tyrone closure-plan descriptions explicitly state that reclamation of 3X began with **outslope and top-surface grading** before/along with drainage construction and cover-subbase placement.

The 2013 closure/closeout update states that 3X reclamation commenced in **September 2004** and included:

- outslope and top-surface grading;
- storm-water diversions and drainage construction;
- placement of suitable cover sub-base on top and outslope surfaces.

This changes how the 1996 NAPP fallback must be interpreted.

A reconstructed 1996 terrain surface is genuinely pre-reclamation, but it is **not automatically the immediate pre-cover/subgrade surface**. Any grading between the 1996 aerial acquisition and the 2004 cover placement would appear in `after - before` along with the cover thickness.

Therefore:

> **Direct `modern final surface - 1996 surface = cover depth` is not scientifically authorized unless the reconstruction and the depth holdouts pass the frozen gates below.**

## Existing CQAR drawings checked

The project-source CQAR drawings were visually inspected on 2026-08-19:

- `3X_CQAR_004_R0.pdf` — final/as-built 3X topographic overview;
- `3X_CQAR_006_007_R0.pdf` — final/as-built north/south topography with mapped cover-depth test pits and depth tables;
- `3X_CQAR_010_R0.pdf` — final/as-built area footprints and six test-plot regions.

These drawings provide valuable final/as-built geometry and depth ground truth, but they do **not** expose the missing pre-cover/subgrade surface as a separate contour set.

## Contractor / owner archive path now active

EMNRD is no longer the only plausible custodian.

M3 Engineering & Technology remains an operating company and publicly identifies its historical role at Tyrone as Project Manager and Engineer of Record for the design and implementation of the Tyrone tailing-dam reclamation. M3's public portfolio also specifically describes the Tyrone tailings reclamation work.

Current M3 corporate contact published on its website:

- `m3@m3eng.com`
- Tucson corporate office: +1 520-293-1488

The recovery target should be narrowly identified as:

- client: Phelps Dodge Tyrone Inc. / Freeport-McMoRan Tyrone;
- M3 project number visible in the CQAR drawings: `03141.01`;
- June 2004 document: `Basic Engineering Report, Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report`;
- desired records: underlying 2004 existing/pre-cover/subgrade topographic surface, grading design surface, CAD/DWG/DXF, TIN/LandXML, survey points, or drawing volume(s) containing existing and proposed grades/contours;
- related 3X CQAR source paths shown in PDF metadata/title blocks can be supplied if useful.

Freeport-McMoRan Tyrone is a second possible owner-side archive if M3 no longer retains the files.

No contractor/owner request should be represented as already sent unless the user explicitly authorizes it.

## Fallback B status: 1996 NAPP stereo reconstruction

### Exact EarthExplorer records now confirmed

EarthExplorer's NAPP collection returns eight 1996 records intersecting the Tyrone 3X footprint. The strongest same-flight stereo triplet is:

| Entity ID | Date | Project | Project No. | Roll | Frame | Flight line | Station | Camera | Lens | Calibrated focal length | Film |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| `NP0NAPP009519108` | 1996-09-28 | NAPP | 9638 | 9519 | 108 | 1084E | 281 | 124257 | 124308 | 152.773 mm | Color Infrared |
| `NP0NAPP009519109` | 1996-09-28 | NAPP | 9638 | 9519 | 109 | 1084E | 280 | 124257 | 124308 | 152.773 mm | Color Infrared |
| `NP0NAPP009519110` | 1996-09-28 | NAPP | 9638 | 9519 | 110 | 1084E | 279 | 124257 | 124308 | 152.773 mm | Color Infrared |

These are consecutive frames on the same roll and flight line, with overlapping EarthExplorer footprints over 3X. This matches the NAPP program design of approximately 60% forward overlap for stereoscopic viewing.

A second same-area pair exists on 1996-10-11 (`N10NAPPW09639042` and `N10NAPPW09639043`), but the September 28 triplet is the preferred first reconstruction candidate because it supplies three consecutive frames over the target.

Public metadata are available without authentication. EarthExplorer exposes a Download action for the scenes, but the download-options route currently redirects to the EROS Registration System login. Therefore the exact scan product/resolution available for these frames is **not yet confirmed** and must not be assumed.

### Source references

- USGS EarthExplorer NAPP collection metadata for the entity IDs above.
- USGS NAPP archive description: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-aerial-photography-program-napp
- ASPRS Positional Accuracy Standards for Digital Geospatial Data, Edition 2 Version 2 (2024): https://www.asprs.org/Main/Main/Standards/Positional-Accuracy-Standards.aspx
- USGS Lidar Base Specification: https://www.usgs.gov/ngp-standards-and-specifications/lidar-base-specification-online

## STEP 4 — FROZEN photogrammetric and depth-validation gates

**Status: PREREGISTERED BEFORE RECONSTRUCTION. These thresholds must not be loosened after seeing the results.**

The gate is project-specific. It does not claim that 1996 NAPP photography itself meets a modern ASPRS accuracy class. ASPRS uses RMSE-based vertical accuracy reporting for elevation data, and current USGS QL2 lidar is associated with a 0.10 m RMSEz accuracy class; those standards are used only as a reference framework for reporting and not as proof that this historical reconstruction is accurate.

### Why the depth limit is 0.10 m

The independently measured Tyrone plot means include:

- TP5 mean: `0.68072 m`
- TP6 mean: `0.94996 m`
- TP6 − TP5: `0.26924 m`

If two plot estimates can each be wrong by roughly 0.15 m in opposite directions, the real TP5/TP6 separation can be erased or reversed. A 0.10 m maximum plot-mean error leaves a materially safer margin and is therefore frozen **before** any photogrammetric depth result is calculated.

### Firewall: measurements cannot be used to manufacture the surface

The known Tyrone cover depths/test-pit depths are **holdout truth only**. They must not be used for:

- bundle adjustment;
- camera calibration choices;
- horizontal registration;
- vertical offset/tilt correction;
- selection or rejection of GCPs/control patches;
- DEM smoothing/interpolation parameters;
- choosing between alternative reconstructions after seeing which one better matches depth.

Any global alignment correction must be derived only from independent stable terrain/control.

### Gate 4A — historical-surface accuracy before looking at depth

Before any 1996-to-final subtraction is interpreted as depth:

1. Split stable terrain into **alignment/control** and **check/validation** sets before optimization.
2. Use at least **20 non-overlapping stable check patches** distributed around the 3X footprint; none may be used for alignment.
3. Compare reconstructed 1996 elevation to the modern reference surface on those held-out stable patches.
4. The held-out stable-patch residuals must satisfy all of the following:
   - `RMSEz <= 0.15 m`
   - `abs(median vertical residual) <= 0.05 m`
   - `95th percentile absolute vertical residual <= 0.30 m`
   - a fitted residual plane must imply **<= 0.10 m peak-to-peak vertical drift across the 3X footprint**.
5. If any item fails, the 1996 surface is not accurate enough for the depth experiment and the route stops before depth comparison.

### Gate 4B — independent depth validation

Only after Gate 4A passes may `final/as-built elevation - reconstructed 1996 elevation` be compared with measured cover depths.

Use every spatially verified mapped 3X measured-depth reference that is valid and inside the reconstructed overlap. The validation set must contain at least **20 independent measured points**; otherwise the evidence is insufficient for a numerical-depth claim.

The candidate depth method passes only if **all** of the following are true without any post-result fitting:

- overall `MAE <= 0.10 m`;
- overall `RMSE <= 0.15 m`;
- `abs(median error) <= 0.05 m`;
- TP5, TP6 and TP7 remain in the correct shallow-to-deep order;
- each of the TP5, TP6 and TP7 reconstructed plot means has `absolute error <= 0.10 m` against its measured mean;
- no obvious spatially coherent residual pattern indicates unresolved grading/registration contamination.

If Gate 4B fails, the result may still be reported as **net historical surface change**, but it must **not** be labeled or enabled as cover depth.

### No rescue rule

After the first preregistered reconstruction/validation is run:

- do not relax the thresholds;
- do not add a fitted scalar offset using measured depths;
- do not rescale depth to the known answers;
- do not cherry-pick plots or test pits;
- do not select a different reconstruction merely because it fits the measured depth better.

A scientifically justified reconstruction failure can be diagnosed later, but any materially changed method must be treated as a **new experiment with a new preregistration before viewing its depth holdouts**.

## Current route status

| Route | Status | Reason |
|---|---|---|
| Original 3X pre-cover CAES/GPS/electronic survey from EMNRD | **CLOSED / unavailable from EMNRD** | EMNRD states no additional records exist beyond the already-produced package |
| Q1-2004 / 2004 PDTI AutoCAD/TIN/grid from EMNRD | **CLOSED from EMNRD** | Historical existence documented, native file not in retained/provided records |
| M3 / Freeport archive recovery of June 2004 3X BER/design surface | **ACTIVE RECOVERY PATH** | M3 was Engineer of Record and remains a plausible independent custodian |
| 1996 NAPP stereo identification | **COMPLETE** | Exact September 28, 1996 roll 9519 frames 108/109/110 confirmed in EarthExplorer |
| 1996 NAPP scan acquisition | **NEXT / BLOCKED ON DOWNLOAD ACCESS** | Metadata confirmed; actual scan product/resolution still requires EarthExplorer download access |
| Step 4 photogrammetric/depth acceptance thresholds | **FROZEN** | Gates above preregistered before reconstruction |
| Direct 1996-to-modern subtraction as cover depth | **BLOCKED pending Gates 4A and 4B** | 1996 is not automatically the immediate pre-cover subgrade and must pass independent validation |
| GPR / active local sensing | **HELD** | Physically direct but usually per-AOI field work and not the preferred automatic/free path |
| More empirical satellite features | **STOPPED** | Prior independent physical feature routes did not validate depth; do not resume random feature hunting |
| Numerical depth in app | **BLOCKED** | No replacement route has yet passed the frozen gates |

## Exact next action

1. Obtain the actual scan products for `NP0NAPP009519108`, `NP0NAPP009519109`, and `NP0NAPP009519110` and record their pixel/scan resolution and file metadata.
2. Before full reconstruction, calculate the expected photogrammetric vertical-error budget from the real scan resolution, focal length, frame geometry, overlap/baseline, control quality, and modern LiDAR reference.
3. If that desk error budget is already clearly worse than the frozen Gate 4A/4B limits, stop before spending more effort on reconstruction.
4. If the error budget is plausible, reconstruct once under the frozen rules and evaluate Gate 4A first.
5. Only if Gate 4A passes, reveal the held-out Tyrone depths and evaluate Gate 4B.
6. Continue the separate M3/Freeport 2004 native-surface recovery path in parallel; a genuine 2004 pre-cover surface would still be superior to the 1996 proxy.

Do not return to random Sentinel/NISAR/NB feature hunting.