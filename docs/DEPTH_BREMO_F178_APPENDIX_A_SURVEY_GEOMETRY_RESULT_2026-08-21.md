# F178 — Bremo West Ash Pond Appendix A survey-geometry result

Date: 2026-08-21

## Purpose

Inspect the actual March 25, 2020 Bremo West Ash Pond CQA report Appendix A and decide whether it contains real numerical measured geometry usable for the frozen external-elevation validation gate.

This follows F177, which kept the 327,323 yd3 Visual-Clean removal quantity classified only as an approximate, volume-derived quantity because the accessible narrative did not prove that it was computed from survey-to-survey earthwork surfaces.

## Source inspected

Official Virginia DEQ package:

- `Closure by Removal Construction — Bremo Power Station — West Ash Pond (VDEQ Permit No. 618)`
- Golder Associates Inc.
- Project No. 19-133736
- March 25, 2020
- Project Source file: `SWP618 PartialClosureApproval by Removal West Ash Pond and CQA Rpt Part 1 of 2 Narrative App A B.pdf`

The CQA narrative states that:

- a topographic survey was performed after the Visually Clean (VC) condition was accepted;
- at least six inches of over-excavation followed;
- a final survey was then performed;
- the surveyor prepared a comparison showing elevation differences between the VC and over-excavation surveys to verify six-inch removal;
- the surveys were prepared by a licensed Professional Land Surveyor and included in Appendix A.

## Appendix A direct inspection

Appendix A contains three survey sheets.

### 1. Visual Clean Survey — `VC-01`

PDF page 18 is a Flora Surveying Associates sheet titled:

> `VISUAL CLEAN SURVEY`

The sheet is at approximately 1 inch = 50 ft scale and contains the surveyed VC surface geometry/contours.

### 2. Closure by Removal Thickness Survey — `CBR-02`

PDF page 19 is a Flora Surveying Associates sheet titled:

> `CLOSURE BY REMOVAL THICKNESS SURVEY`

This is the decisive artifact.

The legend explicitly identifies:

> `SURVEY POINT AND THICKNESS`

The sheet contains dense numerical thickness values distributed across the West Ash Pond footprint. Directly readable examples include values around 0.50–0.70 ft and larger values above 1 ft in some areas.

The survey notes state:

- information shown was field surveyed between 6/4/2017 and 1/30/2020;
- horizontal reference is Virginia State Plane Coordinate System South Zone, NAD83;
- elevations are referenced to NAVD88;
- survey control was supplied by others.

The sheet is signed/sealed by a Virginia Professional Land Surveyor from Flora Surveying Associates.

### 3. Closure by Removal Survey — `CBR-01`

PDF page 20 is a Flora Surveying Associates sheet titled:

> `CLOSURE BY REMOVAL SURVEY`

It publishes top and bottom elevations at numbered test-pit locations. These test-pit top/bottom differences are a **separate supplementary vertical check** and must not be confused with the VC-to-final over-excavation thickness values on `CBR-02`.

Important source discrepancy:

- the CQA narrative/table says **21 test pits/test holes**;
- direct inspection of `CBR-01` shows labels **Test Pit 1 through Test Pit 22**.

This discrepancy is not resolved by assumption. F179 records it explicitly.

## Relation to the 50 ft x 50 ft survey grid

The approved closure-by-removal plan in the same DEQ package explicitly labels a:

> `50' x 50' PRE AND POST-EXCAVATION SURVEY GRID`

Therefore the Appendix A thickness sheet is not merely a qualitative contour exhibit. It is the product of a planned pre/post excavation survey comparison over the closure footprint.

## F178 decision

### Measured-geometry existence gate: PASS

Bremo now has direct official evidence of measured pre/post survey geometry for the six-inch over-excavation step.

The strongest evidence is Appendix A `CBR-02`, which publishes numerical survey-point thicknesses from the VC-to-over-excavated comparison.

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

For the six-inch over-excavation step, the answer is **yes**.

Still required before claiming numerical-depth validation complete:

1. georeference/digitize a bounded subset of `CBR-02` thickness points, or recover source survey/CAD data;
2. pair those fixed measured thicknesses with the candidate elevation surface being tested;
3. compute the frozen residual metrics without tuning to the known Bremo answers;
4. require the existing gates:
   - RMSEz <= 0.15 m;
   - abs median vertical residual <= 0.05 m;
   - 95th-percentile abs vertical residual <= 0.30 m;
   - residual-plane drift <= 0.10 m across target footprint.

## Follow-on

F179 separately checks the published State Plane grid and the test-pit top/bottom elevations, including the 21-vs-22 test-pit source discrepancy.

The next decisive task remains digitization of a fixed subset of `CBR-02` survey-point thickness values.
