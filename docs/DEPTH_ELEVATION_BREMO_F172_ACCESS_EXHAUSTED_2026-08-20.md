# F172 — Bremo West Ash Pond public-access exhaustion checkpoint

Date: 2026-08-20

## Purpose

Record the final public-access result after the F170 scientific pass for Bremo West Ash Pond. This prevents future sessions from repeating the same oversized-PDF and exact-title searches.

## Scientific status remains unchanged

Bremo West Ash Pond remains the strongest site-independent direct-elevation validation candidate found so far.

The required survey chronology is already established:

- 2016-06-09: H&B Surveying & Mapping field-run topography inside the West Ash Pond, before closure excavation;
- approximately 2016-07-06: closure-by-removal excavation begins;
- later: licensed PLS Visual Clean survey;
- later: licensed PLS Six-Inch Removal survey;
- survey-to-survey elevation-difference comparison used by the project to verify at least six inches of over-excavation.

The CQA report independently records:

- Initial / Visual Clean removal: 327,323 yd3;
- Six-Inch Removal: 21,690 yd3;
- Total removal: 349,013 yd3;
- 21 six-inch-deep verification test holes.

The route therefore remains scientifically valid in structure. The blocker is access to actual survey geometry.

## F172 access work completed

### Fluvanna County pre-excavation plan

Target source:

Fluvanna County Planning Commission packet, March 7, 2017, containing Attachment C / Dominion Bremo Power Station CCR Surface Impoundment Closure Major Site Development Plan.

Verified from indexed content:

- Golder project 15-20347;
- file family 1520347X01-MSDP;
- sheets 7, 8, 9 = Existing Conditions (1 of 3), (2 of 3), (3 of 3);
- existing West Ash Pond conditions use field-run topography by H&B Surveying & Mapping collected 2016-06-09;
- site datum NAD83 / NAVD88, Virginia State Plane South.

Repeated targeted searches did not recover Attachment C or sheets 7-9 as separate public files. Search results consistently return the same combined county packet, approximately 58 MB, which the current PDF viewer/runtime cannot fetch or render reliably.

### Virginia DEQ post-excavation survey package

Target source:

March 2020 West Ash Pond Closure by Removal Construction Report, Project 19-133736, specifically Appendix A.

Verified from indexed DEQ content:

- Flora Surveying Associates, PC was the surveyor;
- Bruce Flora, PLS was project manager;
- Appendix A contains licensed PLS surveys for both Visual Clean and Six-Inch Removal conditions;
- the surveyor prepared topographic contour maps and an elevation-difference comparison.

Exact-title searches for separate Visual Clean, Six-Inch Removal, Bruce Flora, Flora Surveying, Appendix A, and project 19-133736 did not recover an independently hosted survey sheet/file.

The DEQ report is searchable/indexed, but the actual PDF endpoint returns cache/fetch errors in the current viewer, so Appendix A cannot be rendered safely here.

### Other relevant confirmation

A Bremo West Pond closure-plan drawing explicitly shows a `50' x 50' PRE AND POST-EXCAVATION SURVEY GRID`, confirming that structured pre/post survey control was part of the approved closure method. This is supportive evidence but does not replace the actual measured survey surfaces.

## Decision

**Bremo West = SCIENTIFICALLY PASS / PUBLIC WEB EXTRACTION EXHAUSTED / SOURCE FILE NEEDED.**

Do not continue broad web searches for duplicate Bremo copies unless a genuinely new archive location or exact file identifier appears.

Do not reconstruct spatial elevations from search-engine text snippets.

## Exact minimum user-supplied artifact

First priority:

- Download and upload the Fluvanna County March 7, 2017 Planning Commission packet:
  `pc_complete_2017-3-7.pdf`

Only Attachment C / sheets 7-9 are needed initially. The entire PDF is acceptable if easier.

After those pre-excavation sheets are extracted, second priority:

- Virginia DEQ West Ash Pond Closure by Removal Construction Report, March 2020, Project 19-133736, preferably Part 2 / Appendix A containing the Visual Clean and Six-Inch Removal licensed survey drawings.

## Next numerical workflow after files arrive

1. Extract/render only the relevant survey sheets.
2. Preserve NAD83/NAVD88 control and sheet scale.
3. Digitize/reconstruct the June 9, 2016 pre-excavation surface.
4. Digitize/reconstruct the Visual Clean surface.
5. Use only stable survey/control alignment; no fitting to known depth answers.
6. Compute pre-excavation minus Visual Clean elevation difference over the valid common footprint.
7. Integrate cut volume and independently compare with 327,323 yd3.
8. Compare Visual Clean versus Six-Inch Removal and check the >=0.5 ft behavior plus 21,690 yd3 volume.
9. Only after these independent checks decide whether Bremo validates the direct-elevation method numerically.

## Separation from Tyrone

This does not unblock Tyrone's own Step 4. Tyrone remains blocked on its missing 2004 post-grading/pre-cover surface, while M3 and Freeport requests remain separate external-record paths.

## Guardrails

- no classifier changes;
- no UI changes;
- no NB-formula changes;
- no use of known Tyrone depth holdouts to fit or shift Bremo surfaces;
- no numerical validation claim until actual survey geometry is recovered and checked.
