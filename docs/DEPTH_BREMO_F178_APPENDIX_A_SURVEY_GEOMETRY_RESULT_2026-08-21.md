# F178 — Bremo West Ash Pond Appendix A survey-geometry result

Date: 2026-08-21

## Purpose

Inspect the actual March 25, 2020 Bremo West Ash Pond CQA report Appendix A and decide whether it contains real numerical measured geometry usable for the frozen external-elevation validation gate.

This step follows F177. F177 left the 327,323 yd3 Visual-Clean removal quantity classified only as an approximate, volume-derived quantity because the accessible narrative did not prove that it was computed from survey-to-survey earthwork surfaces.

## Source inspected

Official Virginia DEQ package:

- `Closure by Removal Construction — Bremo Power Station — West Ash Pond (VDEQ Permit No. 618)`
- Golder Associates Inc.
- Project No. 19-133736
- March 25, 2020
- DEQ package file supplied in Project Sources as `SWP618 PartialClosureApproval by Removal West Ash Pond and CQA Rpt Part 1 of 2 Narrative App A B.pdf`

Relevant report text states that:

- a topographic survey was performed after the Visually Clean (VC) condition was accepted;
- at least six inches of over-excavation followed;
- a final survey was then performed;
- the surveyor prepared a comparison showing elevation differences between the VC and over-excavation surveys to verify six-inch removal;
- the surveys were prepared by a licensed Professional Land Surveyor and included in Appendix A.

## Appendix A direct inspection

Appendix A contains three survey sheets.

### 1. Visual Clean Survey

PDF page 18 is a Flora Surveying Associates sheet titled:

> `VISUAL CLEAN SURVEY`

Drawing identifier shown on the sheet: `VC-01`.

The sheet is at approximately 1 inch = 50 ft scale and contains the surveyed VC surface geometry/contours.

### 2. Closure by Removal Thickness Survey

PDF page 19 is a Flora Surveying Associates sheet titled:

> `CLOSURE BY REMOVAL THICKNESS SURVEY`

Drawing identifier shown on the sheet: `CBR-02`.

This is the decisive artifact.

The legend explicitly identifies:

> `SURVEY POINT AND THICKNESS`

The sheet contains dense numerical thickness values distributed across the West Ash Pond footprint. Visible examples include values around 0.50–0.70 ft and larger values above 1 ft in some areas.

The survey notes state:

- information shown was field surveyed between 6/4/2017 and 1/30/2020;
- horizontal reference is Virginia State Plane Coordinate System South Zone, NAD83;
- elevations are referenced to NAVD88;
- survey control was supplied by others.

The sheet is signed/sealed by a Virginia Professional Land Surveyor from Flora Surveying Associates.

### 3. Closure by Removal Survey

PDF page 20 is a Flora Surveying Associates sheet titled:

> `CLOSURE BY REMOVAL SURVEY`

Drawing identifier shown on the sheet: `CBR-01`.

It plots the 21 test-pit locations and gives numerical top and bottom elevations for the test pits. Examples visible directly on the drawing include:

- Test Pit 21: top 219.04 ft, bottom 218.30 ft → 0.74 ft difference;
- Test Pit 20: top 210.83 ft, bottom 210.08 ft → 0.75 ft difference;
- Test Pit 15: top 209.05 ft, bottom 208.22 ft → 0.83 ft difference;
- Test Pit 19: top 197.73 ft, bottom 196.71 ft → 1.02 ft difference;
- Test Pit 16: top 204.24 ft, bottom 203.53 ft → 0.71 ft difference;
- Test Pit 14: top 207.10 ft, bottom 206.12 ft → 0.98 ft difference;
- Test Pit 17: top 203.20 ft, bottom 202.47 ft → 0.73 ft difference;
- Test Pit 18: top 202.92 ft, bottom 202.20 ft → 0.72 ft difference.

These are direct survey-elevation differences, not volume/area normalization.

## Relation to the 50 ft x 50 ft survey grid

The approved closure-by-removal plan in the same DEQ package explicitly labels a:

> `50' x 50' PRE AND POST-EXCAVATION SURVEY GRID`

Therefore the Appendix A thickness sheet is not merely a qualitative contour exhibit. It is the product of a planned pre/post excavation survey comparison over the closure footprint.

## F178 decision

### Measured-geometry existence gate: PASS

Bremo now has direct official evidence of measured pre/post survey geometry for the six-inch over-excavation step.

The strongest evidence is the Appendix A `CLOSURE BY REMOVAL THICKNESS SURVEY`, which publishes numerical survey-point thicknesses, plus `CBR-01`, which publishes top/bottom elevations at the test pits.

The six-inch design threshold is:

- 0.50 ft
- 6 in
- 0.1524 m

This is directly at the project’s frozen ~0.15 m historical-surface accuracy gate and is therefore a useful independent reference for testing whether an elevation-difference workflow can resolve a change of that magnitude.

## Important limitation

This result does **not** upgrade the earlier 327,323 yd3 Visual-Clean removal quantity to a measured full-depth anchor.

The approximately 3.64 m pond-wide value remains labeled:

> **volume-derived pond-wide average reference**

The Appendix A survey pair directly validates only the later VC-to-over-excavated thickness step.

Do not relabel 3.64 m as measured depth.

## Scientific status after F178

Bremo is no longer blocked on the question:

> “Does a real numerical survey-to-survey reference exist?”

For the six-inch over-excavation step, the answer is now **yes**.

Still required before claiming numerical-depth validation complete:

1. georeference/digitize a bounded subset of Appendix A thickness points (or recover source survey/CAD data);
2. pair those measured thicknesses with the candidate external/historical elevation surface being tested;
3. compute the frozen residual metrics without tuning to the known Bremo answers;
4. require the existing gates:
   - RMSEz <= 0.15 m;
   - abs median vertical residual <= 0.05 m;
   - 95th-percentile abs vertical residual <= 0.30 m;
   - residual-plane drift <= 0.10 m across target footprint.

## Next action — F179

Use the Appendix A survey package to build a small, auditable Bremo reference set:

- select clearly readable survey/test-pit points;
- record their measured thicknesses and locations from the State Plane-referenced drawing;
- convert feet to metres;
- define a clean bounded validation footprint;
- then test the candidate elevation surface against those fixed measured values.

Do not return to broad site searching while this newly recovered measured reference remains testable.
