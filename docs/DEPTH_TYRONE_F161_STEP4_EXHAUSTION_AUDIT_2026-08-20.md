# Tyrone depth — F161 Step-4 exhaustion audit — 2026-08-20

## Purpose

Stop the Step-4 repair from cycling through technology names after F160. Inventory every physically plausible source class screened so far and determine whether any distinct **public/project-available** source can still provide a trustworthy immediate post-grading / pre-cover Tailing Dam 3X surface under the frozen historical-surface accuracy gate.

## Frozen scientific requirement

The target remains a 3X land surface acquired or valid **after reclamation grading began in September 2004 and before cover placement began in May 2005**.

Historical-surface acceptance remains frozen before depth holdouts are used, including:

- `RMSEz <= 0.15 m`;
- absolute median vertical residual `<= 0.05 m`;
- 95th-percentile absolute vertical residual `<= 0.30 m`;
- residual-plane drift `<= 0.10 m` across the 3X footprint.

Known TP/test-pit depths remain holdout truth only.

## Exhaustion matrix

| Source class | Result | Step-4 decision |
|---|---|---|
| Known 2008 CQAR/as-built topography | Recovered, but final/post-cover | Not the historical substrate |
| 2018 lidar | Recovered/documented final/current surface | Useful only as later surface/reference, not pre-cover |
| May-3-2004 PDTI AutoCAD/TIN/25-ft grid topography | Real mine-wide elevation surface | **Too early**; predates Sep-2004 grading |
| Public 3X grading/design CAD / exact BER surface | Extensively searched, not recovered | Potentially useful only if a real file surfaces with construction-conformance evidence |
| CAES machine-control / conventional GPS construction surface | Construction use is proven | **Potentially decisive but not recovered publicly** |
| Numerical cut/fill / top-surface grading correction | Not recovered | Cannot transform May-2004 surface without inventing grading |
| CQAR missing native DWGs / 17-sheet set | Existence proven; known sheets are final/as-built | No pre-cover surface recovered |
| Internal Phelps Dodge/PDTI GIS / Bill Seibert coverages | Internal environment and 3X projects proven | No post-grading 3X surface recovered |
| Quarterly PDTI Pit maps | Survey-derived pit/stockpile record | **Closed F159**: 3X tailing surface not in mapped spatial units |
| February-2004 Tyrone mine aerial / stereo | Officially documented | **Closed F158**: too early |
| Sep-2004–Apr-2005 federal/NAPP/EDAC historical aerial | Searched | No usable construction-window stereo source recovered |
| November-2004 construction photos | One same-epoch overview recovered | **Closed F160**: no same-epoch stereo/SfM pair |
| Pre-cover airborne lidar | Searched | No construction-window 3X lidar recovered |
| 2005/2006 statewide NM DTM | Real later DTM | **Too late**: source flying began after cover placement |
| Historical commercial satellite stereo — IKONOS / QuickBird / SPOT-5 | Technology screened | **Closed F155**: published vertical performance exceeds 0.15 m gate |
| ICESat-1 / GLAS Laser-3A | Correct timing, actual NASA CMR screen run | **Closed F154**: GLAH14 `COUNT: 0` over real 3X bbox |
| ASTER stereo DEM | Available class | NASA reports typical scene DEM vertical RMSE about 10–25 m; fails gate |
| SRTM | Near-global DEM | Acquired February 2000 and about 15 m vertical accuracy; wrong date and fails gate |
| Envisat ASAR / repeat-pass InSAR DEM route | 2004-era radar class | ~20–30 m image resolution and DEM phase affected by atmospheric error; not a 0.15 m absolute graded-surface solution |
| Airborne IFSAR | High-resolution radar DEM class | Published USGS example reports vertical accuracy <1 m; still materially above 0.15 m, and no Tyrone construction-window product surfaced |
| Cartosat-1 stereo | Later stereo satellite | Launched May 5, 2005; not available during Sep-2004–Apr-2005 target window |
| Lysimeter excavation / monitoring geometry | Sparse local construction information | Not a full surface; using excavation/depth information risks circularity |
| Reclamation cost/model/takeoff records | Screened | Modeled quantities, not actual surveyed 2004–2005 surface |
| MMD/operator historical GIS submissions | Screened | No historical 3X topographic package recovered publicly |

## Broad remote-sensing omission check

F161 explicitly checked common technology classes that might otherwise look like untested alternatives:

- NASA describes ASTER scene DEM vertical RMSE as generally 10–25 m.
- NASA describes SRTM as a February-2000 mission with roughly 15 m vertical accuracy.
- ESA describes Envisat ASAR resolution on the order of 20–30 m and notes atmospheric-delay effects can impair interferometric DEM heights.
- A USGS airborne IFSAR example reports vertical accuracy better than 1 m, still not near the frozen 0.15 m gate.
- ISRO states Cartosat-1, its first in-orbit stereo mapping satellite, launched May 5, 2005.

These classes therefore do not create a viable overlooked public Step-4 path.

## F161 scientific conclusion

**STEP 4 IS EXHAUSTED ON THE CURRENT PUBLIC + PROJECT-AVAILABLE EVIDENCE.**

This does **not** mean the physical historical surface never existed.

The construction record proves that grade-control/survey information existed during construction. The remaining scientifically plausible solution is an **unpublished/internal construction record**, not another generic public remote-sensing product.

Steps 5–8 remain **NOT REACHED**.

## Minimum external record that would unblock Step 4

Any one of the following could reopen Step 4 if it is genuine, spatially covers the usable 3X top surface, and can be independently tied to the required time window and vertical datum:

### A. Best case — actual surveyed construction surface

A dated 3X post-grading/pre-cover survey acquired between Sep-2004 and before cover placement in May-2005, for example:

- conventional GPS survey points / breaklines;
- CAES as-built/export surface;
- TIN / LandXML / DXF / DWG / DEM / XYZ surface;
- surveyor finish-grade / subgrade acceptance surface.

### B. Machine-control design + independent conformance evidence

The actual 3X CAES/grading design surface may be usable **only if** independent construction survey/acceptance records prove the built substrate conformed closely enough to pass the frozen vertical gate. The design model alone is not automatically an as-built surface.

### C. Quantitative transform of the May-2004 surface

A spatially explicit cut/fill or grading-correction dataset could transform the May-2004 surface only if its accuracy is documented strongly enough to satisfy the frozen gate **without using known cover-depth answers**.

## What does NOT unblock Step 4

- another final/as-built surface after cover placement;
- another low/medium-resolution DEM;
- satellite imagery with no metric vertical performance near 0.15 m;
- a single construction photograph;
- nearby but non-intersecting laser/radar observations;
- design thickness values or known TP/test-pit depths;
- modeled reclamation quantities;
- a generic statement that CAES/GPS was used without the actual coordinates/surface.

## Route status after F161

- Original direct-elevation method: **BLOCKED at Step 4; public/project repair exhausted**.
- Step 5 alignment: **NOT REACHED**.
- Step 6 subtraction: **NOT REACHED**.
- Step 7 TP5/TP6/TP7 validation: **NOT REACHED for this elevation method**.
- Step 8 TP1/TP2/TP3 + 43-pit validation: **NOT REACHED**.
- Route A recorded-depth lookup: separate; do not switch without explicit user instruction.
- Classifier/UI/NB formula: unchanged.

## Exact next action

### F162 — identify the narrowest plausible custodian/source request, without contacting anyone

Do not perform another broad data hunt.

Using the proven project fingerprints — M3 project `03141.01`, 3X CQAR/BER, CAES + conventional GPS construction, Phelps Dodge/PDTI GIS environment, and Golder job `053-2365` — identify which organization/archive is most likely to retain one of the minimum records above and exactly what filenames/record descriptions should be requested.

F162 is research/preparation only. **Do not send an email, records request, or purchase anything without explicit user approval.**