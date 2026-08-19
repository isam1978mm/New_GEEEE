# Depth second independent site audit — 2026-08-18

## Decision

**CLOSED — NO EXISTING SECOND SITE PASSES ALL CURRENT DEPTH-EVIDENCE GATES.**

This audit was performed after the Tyrone six-plot raw Sentinel-1, terrain/northness, Landsat thermal, and Sentinel-2 NDVI/NDMI direct-signal screens failed. The purpose was to determine whether an already-researched official site could provide an independent measured-depth validation/training site before testing another feature family.

No classifier, UI, NB formula, Earth Engine production run, calibration row, or app-depth enablement was changed.

## Current Tyrone reference status

Tyrone 3X remains the only project reference with all of the following together at useful broad-plot scale:

- official measured cover depths;
- multiple depth levels;
- two surface groups;
- validated global transform;
- broad plot geometry large enough for conservative satellite extraction.

The existing NB numerical-depth route remains CLOSED / FAILED VALIDATION.

## Strongest independent-site candidates reviewed

### 1. Tyrone Dam 1

Official EMNRD recovery was rerun from PR #26.

Recovered result:

- five official PDFs recovered successfully;
- the key Dam 1 table reports impacted acres and acres with **>3 ft** cover:
  - Dam 1 Top: 254 ac impacted, 237 ac >3 ft;
  - Dam 1 Outslope: 104 ac impacted, 28 ac >3 ft;
  - 12 Ponds Top: 44 ac impacted, 44 ac >3 ft;
  - total: 402 ac impacted, 309 ac >3 ft;
- no exact second measured depth class is published in the recovered table;
- no embedded CAD/GIS/electronic files were present in the recovered PDFs.

Decision: **fails exact measured-depth pair gate.**

### 2. Sconondoa Phase 3

This is a real independent measured-depth site and is the strongest measurement/placement candidate found outside Tyrone.

- shallow zone mean measured depth: 3.511 m, range 3.292–3.658 m;
- deep zone mean measured depth: 4.881 m, range 4.633–5.090 m;
- survey transform validated with independent holdout;
- conservative placement uncertainty: 1.1 m;
- shallow polygon minimum rotated dimension: 21.1 m;
- deep polygon minimum rotated dimension: 23.2 m;
- maximum safe inscribed diameters after placement allowance: 16.637 m and 18.787 m.

Decision: **measurement and placement pass, but locked clean 20 m satellite-footprint gate fails.**

### 3. Consolidated Iron and Metal

- final engineering report and as-built drawings recovered;
- same final surface supported;
- licensed surveyor;
- stated survey vertical tolerance: 0.5 ft;
- measured cover depth range: 3.0–6.2 ft;
- a non-overlapping shallow cell has depths 3.0, 3.6, 4.2, 4.8 ft;
- shallow cell dimensions: 15.24 m × 30.48 m.

Decision: **measured-depth evidence passes, but the shallow cell cannot contain a clean 20 m footprint.**

### 4. Hoosier #1 Landfill

- coordinate-tied final measurements exist in the 1.85-acre Cell 1 South Slope area;
- measured combined barrier + protective soil thickness spans roughly 5.12–6.42 ft;
- 18 survey points are tied to coordinates.

But:

- the points do not form two broad shallow/deep polygons;
- the long strip does not prove two independent clean interiors;
- the larger older and composite cover areas do not both publish final coordinate-tied absolute measured thickness grids;
- numerical survey uncertainty was not found.

Decision: **fails two broad measured-zone and uncertainty gates.**

### 5. Rocky Mountain Arsenal Integrated Cover System

- large mapped 2-ft and 3-ft vegetated cover polygons exist;
- current coordinate-labelled map exists;
- common vegetation assessment supports comparable visible surface in principle.

But:

- recovered public records do not publish absolute final measured thickness values for the 2-ft polygons;
- monitoring reports soil-loss change, not absolute as-built depth;
- numerical survey uncertainty was not found.

Decision: **fails absolute measured as-built depth gate.**

### 6. J.R. Whiting Ponds 1 and 2

- 107 coordinate-tied final-cover control points on a 100-ft grid;
- depth is derived from record topsoil elevation minus record subgrade elevation;
- nominal shallow and deep 100-ft cells exist.

But:

- mean depth contrast between the selected cells is only 0.16 ft (0.048768 m);
- the deep cell intersects mapped drainage infrastructure;
- numerical horizontal/vertical survey accuracy was not found;
- clean execution geometry was not established.

Decision: **fails clean independent depth-pair and survey-accuracy gates.**

### 7. Plant Kraft AP-1

- confirmed CCR removal;
- post-excavation and top-of-structural-fill surveys exist;
- physical size could support 20 m footprints in principle.

But:

- verified excavation boundary is stored as a raster overlay rather than a defensible survey vector;
- automatic georeferencing was rejected;
- exact WGS84 polygon and boundary uncertainty were not established;
- stable Sentinel-1 timing was not confirmed.

Decision: **fails exact georeference/stable-timing gate.**

### 8. SLAPS

- large remediated site with survey/design records;
- excavation contours and cross-sections exist.

But the official packages recovered do not publish two completed final measured excavation-depth polygons with coordinate-tied final depths and survey uncertainty.

Decision: **fails final measured-depth polygon gate.**

## 43 Tyrone AS-BUILT test pits

The project also has 43 exact, non-censored, independently mapped Tyrone AS-BUILT test pits outside/away from the six development plots. Their depths span approximately 24–35 inches and their UTM/WGS84 positions are known.

These measurements are valuable independent point-level ground truth, but they are **point measurements**, not broad homogeneous polygons. They cannot automatically be promoted to general satellite calibration rows. Any point-level sensor experiment must preserve scale support and spatial-independence rules and must be preregistered before feature inspection.

The already-preregistered northness holdout failed its effect-size gate at both 10 m and 20 m radii (rho < 0.30).

## Final status

- second independent broad measured-depth site ready now: **NO**;
- usable additional calibration row created: **NO**;
- general numerical-depth model justified: **NO**;
- numerical app depth unblocked: **NO**;
- classifier changed: **NO**;
- NB formula changed: **NO**.

## Exact next route

Do **not** restart the same broad-site search or tune the failed C-band/terrain/thermal/optical signals.

Before any new modelling, evaluate whether a genuinely different free physical sensor family can add subsurface sensitivity at sufficient spatial resolution. The next feasibility check is **public L-band SAR availability and resolution** (for example NISAR/ALOS-class data) over Tyrone and the independent point records.

If no suitable L-band product is available at defensible resolution/support, numerical depth remains blocked pending a new independently measured broad reference site or field/calibration data.
