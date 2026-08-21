# F170 — Bremo West Ash Pond survey-surface recovery

Date: 2026-08-20

## Route position

This is the new site-independent direct-elevation validation route opened at F165. It does not change Tyrone Step 4 status. Tyrone remains blocked pending its own 2004 post-grading/pre-cover surface or private construction records.

Bremo West Ash Pond is currently the strongest elevation-only validation candidate.

## What F170 verified

### Pre-excavation surface

The public Fluvanna County March 7, 2017 planning-commission packet contains the December 2016 Bremo Major Site Development Plan, Golder project 15-20347 / file 1520347X01-MSDP.

The plan states that existing conditions within the West Ash Pond use:

- FIELD RUN TOPOGRAPHY BY H&B SURVEYING & MAPPING;
- collected 2016-06-09;
- within the limits of the West Ash Pond only;
- datum NAD83 / NAVD88, Virginia State Plane South.

The drawing index identifies sheets 7, 8 and 9 as EXISTING CONDITIONS (1 OF 3), (2 OF 3), and (3 OF 3).

The West Ash Pond CQA report states closure-by-removal construction began approximately 2016-07-06. Therefore the 2016-06-09 H&B field topography is genuinely pre-excavation.

### Post-excavation surfaces

Virginia DEQ's public Bremo operating-record page lists the West Ash Pond Closure by Removal Construction Report in two parts.

The March 2020 CQA report, project 19-133736, states:

- after visually clean conditions were achieved and accepted, the area was surveyed;
- the surveyor compiled a topographic contour map for the Visually Clean condition;
- the footprint was then over-excavated by at least six inches;
- a second survey was performed;
- the surveyor prepared an elevation-difference comparison between the Visually Clean and over-excavation surveys;
- surveys prepared by a licensed Professional Land Surveyor for both conditions are in Appendix A;
- surveying was provided by Flora Surveying Associates, PC, Glenns, Virginia, with Bruce Flora, PLS, listed as project manager.

The report records:

- West Ash Pond size: about 17.0 acres;
- initial / Visually Clean removal: 327,323 cubic yards;
- six-inch removal: 21,690 cubic yards;
- total: 349,013 cubic yards;
- 21 six-inch-deep verification test holes.

These volumes are potential independent volumetric checks once a difference surface is constructed.

## Scientific decision

Bremo passes the scientific chronology/measurement-structure screen:

2016-06-09 H&B pre-excavation field survey -> excavation begins 2016-07-06 -> licensed Visual Clean survey -> licensed six-inch over-excavation survey.

This is materially stronger than Meredosia because the CQA record explicitly preserves an intermediate clean excavation-floor survey before later reshaping/fill can obscure the cut.

## F170 access result

The route is not yet numerically executable in the current tool environment.

The actual survey geometry has not been recovered:

1. The pre-excavation H&B sheets are embedded in a roughly 58 MB Fluvanna County packet. Web indexing exposes the drawing index and survey-source notes, but the PDF is too large for the current PDF viewer to fetch/render.
2. The DEQ CQA report is indexed and confirms Appendix A, but the current web environment cannot open the DEQ PDF endpoint reliably enough to render the Appendix A survey sheets.
3. Exact-name/file-fingerprint searches did not recover a smaller public duplicate of sheets 7-9 or the Appendix A survey drawings.
4. The repo does not currently contain Bremo source files under data/research.

Do not fabricate contours, coordinates, or elevations from search snippets.

## Current status

Bremo West Ash Pond: **SCIENTIFICALLY PASS / DATA-EXTRACTION BLOCKED**.

This is not a scientific rejection.

## Minimum artifacts that would unblock calculation

Either of the following is enough to reopen numerical work:

### Pre surface

- Fluvanna County March 7, 2017 packet, specifically Attachment C sheets 7-9; or
- any native/smaller copy of Golder project 15-20347, file 1520347X01-MSDP, existing-conditions sheets using H&B field survey dated 2016-06-09; or
- native CAD / survey points / contour export for that H&B survey.

### Post surface

- West Ash Pond CQA report Appendix A licensed PLS Visual Clean survey; preferably also the Six-Inch Removal survey/elevation-difference sheet; or
- native Flora Surveying CAD/points/DTM corresponding to those surfaces.

## Calculation once artifacts are available

1. Preserve survey datum/control metadata.
2. Reconstruct/digitize the 2016-06-09 pre-excavation surface.
3. Reconstruct/digitize the Visual Clean surface.
4. Align only using stable control; do not fit using known depth answers.
5. Compute pre-excavation minus Visual Clean elevation difference over the valid common excavation footprint.
6. Integrate calculated cut volume and compare independently with the reported 327,323 yd3.
7. As a second internal QA check, difference Visual Clean versus Six-Inch Removal and verify the intended >=0.5 ft over-excavation behavior and reported 21,690 yd3.
8. Only after these checks decide whether Bremo provides a trustworthy direct-elevation validation reference.

## Guardrails

- No classifier change.
- No UI change.
- No NB-formula change.
- No fitting to Tyrone TP/test-pit depth answers.
- Do not call Bremo numerically validated until actual surfaces are recovered and checked.
- Keep Tyrone M3/Freeport requests separate and active; Bremo does not magically solve Tyrone's missing 2004 surface.

## Next action

Continue the old-site elevation-only re-score while Bremo remains recoverable-but-blocked on source extraction. If a Bremo source file becomes available, Bremo takes priority immediately because it already passes the scientific structure gate.
