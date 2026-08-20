# Tyrone depth continuity lock V3 — F100–F152 checkpoint — 2026-08-20

## Purpose

This file extends the Tyrone Step-4 continuity chain so a future session does not restart from F34/F99 or repeat the already-traced repair branches.

Read this together with:

- `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20.md`
- `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V2_STEP4_REPAIR.md`
- `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V1.md`

This checkpoint records the F100–F152 chronology supplied in the controlling session. It is a continuity record of work already reported in that session; where a later session needs to rely on a scientific fact for a new conclusion, verify the underlying source again if practical rather than silently strengthening the claim.

## Route position

The original direct-elevation plan remains at **Step 4 — recover/build a trustworthy immediate post-grading / pre-cover 3X surface**.

Steps 5–8 remain **NOT REACHED**.

Route A recorded-depth lookup remains separate and must not replace the direct-elevation repair path.

## F100–F121 — construction-record and independent-control branches

The session continued after V2 with targeted searches for:

- subgrade acceptance / grade verification / GPS survey / finish-grade / CAES model records;
- contemporaneous 2004–2005 construction progress evidence;
- agency comments and construction photographs;
- 2003 Condition 76 / Condition 29 work plans;
- Golder project `053-2365` companion deliverables;
- construction-photo captions and lysimeter GPS-survey evidence.

Key reported results:

1. No separate public 3X subgrade-acceptance / grade-verification / CAES-model file surfaced.
2. A later Tyrone earthwork record lists Tailing 3X final grade in late 2005, but not a usable survey surface.
3. Contemporary construction-photo captions narrowed the test-plot chronology:
   - general overview — Nov 2004;
   - cover placement — May 2005;
   - scarified seedbed / seeding complete — June 2005.
4. The annual-report photo appendix did not itself provide surveyed elevations.
5. The 2003 Tetra Tech Condition 76/29 work plans were confirmed by later reports but their PDFs/drawings were not recovered publicly.
6. The 2006 test-plot As-Built report again confirmed subgrade grading with 14H grader + CAES + conventional GPS and said final construction details would be in the separate 3X CQDAR/CQAR package.
7. Lysimeter locations were reported as GPS-surveyed before construction, but no absolute elevation table / survey-coordinate deliverable surfaced. Do not use lysimeter excavation depths to manufacture the pre-cover surface because that would risk circularity.

## F122–F140 — 2005 DTM / historical-image and cost-estimate branches

A new statewide 2005/2006 New Mexico imagery/DTM route was screened.

Reported facts:

- statewide 1 m imagery was acquired with a Zeiss DMC camera;
- Bohannan-Huston produced a 10 m DTM using stereo/spatial autocorrelation from that imagery;
- 3001, Inc. flew the imagery;
- the DTM was intended for distribution in FLT/DEM/XYZ/contour/hillshade forms;
- project metadata placed the source-imagery program in the 2005–2006 summer flying seasons, beginning in July 2005.

Because project construction evidence already showed cover placement in May 2005 and seeding complete in June 2005, this statewide DTM route was reported **CLOSED as a pre-cover Step-4 source**. It may be an early post-reclamation/final-surface reference, but not the immediate pre-cover substrate.

The session then narrowed the admissible historical-image window to approximately:

> **after grading began in September 2004 and before cover placement in May 2005**.

Additional branches screened and reported closed/no solution:

- Sep-2004–Apr-2005 NAPP/federal aerial search;
- EDAC/PWT historical-film collection for 2004–2005;
- free EDAC/NARA digitized historical archive (too old for the window);
- pre-cover airborne LiDAR search;
- 2013 MWH reclamation-cost / takeoff material as a proxy for actual 3X grading quantities.

The MWH/cost-estimate material was explicitly rejected as an as-built grading source because its 3X entries were modeled/revegetation-maintenance inputs rather than actual 2004–2005 cut/fill observations.

## F141–F150 — contemporaneous state records and MMD GIS branch

A contemporaneous State of New Mexico 2004 Mining Act Reclamation Program report was reported to show Tyrone 3X work underway in Nov 2004 and describe the outslope as recently regraded in preparation for drains, cover and seeding.

This improved timing confidence but did not provide 3X survey elevations or grading quantities.

The session also identified a separate records class from later MMD annual-report/GIS practice:

- operator pre/post-treatment reclaimed-area information;
- digital maps requested as AutoCAD or ESRI shapefiles;
- date-layer overlays with topography and mine features.

No public historical 3X operator-submitted GIS/topography package was recovered from the current MMD map systems. This branch was therefore not treated as a solved surface source.

## F151–F152 — newest candidate: ICESat-1 / GLAS

The newest distinct direct-elevation source class screened was **ICESat-1 / GLAS laser altimetry**, not a radar/satellite-feature proxy.

Reported timing fact:

- GLAS Laser 3A operated approximately **3 Oct–8 Nov 2004**, inside the admissible construction window after grading began and before May-2005 cover placement.

Reported collection identification:

- NASA/NSIDC **GLAH14 Version 34** land-surface altimetry collection;
- collection identifier reported in-session as `C2153551318-NSIDC_CPRD`.

Crucially, the session had **not yet established whether any Laser-3A GLAH14 ground track actually crossed Tailing Impoundment 3X**.

## Exact current continuation point

Do **not** restart F34–F152.

The next scientific action is:

### F153 — spatially test Laser-3A GLAH14 coverage against the real 3X footprint

1. Use the exact 3X AOI / project geometry already present in the project source.
2. Query GLAH14 granules for the Laser-3A date window (Oct–Nov 2004).
3. Determine whether any GLAS footprint / track intersects 3X or comes close enough to provide independent control over the relevant top surface.
4. If **no track intersects 3X**, close the GLAS branch immediately.
5. If a track intersects, inspect footprint count, spacing, quality flags, horizontal geolocation, elevation corrections and whether the points fall on bare/usable terrain.
6. Do not compare against Tyrone cover-depth holdouts during this screen.

## Continuity rules

- Do not claim a GLAH14 crossing until spatially verified.
- Do not treat a nearby GLAS shot as a full surface.
- Do not loosen the frozen historical-surface accuracy gate.
- Do not use known TP/test-pit depths to fit or vertically shift the candidate surface.
- Do not change classifier, UI, NB formula, interpolation logic or production depth behavior.
- No email, purchase or payment without explicit user approval.
- Every meaningful step must report: **what was done / current status / exact next action**.
