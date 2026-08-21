# F185 — Bremo Flora source-survey record specification

Date: 2026-08-21

## Purpose

Define the smallest decisive source-data request that can replace hand-digitized Appendix A coordinates with the original measured survey geometry for the Bremo West Ash Pond Visual Clean -> six-inch over-excavation step.

This specification is intentionally narrow. Do **not** request the entire Bremo project archive if these exact records can be located separately.

## Proven identifiers

Facility:
- Bremo Power Station / Bremo Bluff Power Station
- West Ash Pond
- Virginia Solid Waste Permit SWP618
- Fluvanna County, Virginia

CQA report:
- `Closure by Removal Construction — Bremo Power Station — West Ash Pond (VDEQ Permit No. 618)`
- Golder Associates Inc.
- Project No. `19-133736`
- March 25, 2020

Surveyor:
- Flora Surveying Associates
- Bruce W. Flora, PLS

Survey project title block:
- Project No./identifier: `RYAN-BREMO`

Survey drawings:
- `VC-01` — `VISUAL CLEAN SURVEY`
- `CBR-01` — `CLOSURE BY REMOVAL SURVEY`
- `CBR-02` — `CLOSURE BY REMOVAL THICKNESS SURVEY`

`CBR-02` drawing date:
- February 28, 2020

Survey reference system:
- Virginia State Plane Coordinate System South Zone
- NAD83 horizontal datum
- NAVD88 vertical datum

Survey note range:
- field surveyed between approximately June 4, 2017 and January 30, 2020

Construction/CQA parties named in the report:
- Owner: Dominion Energy Virginia
- Earthworks contractor: Ryan Incorporated Central
- Surveyor: Flora Surveying Associates, PC
- CQA engineer: Golder Associates Inc.

## Tier 1 — decisive records

Request any one or more of the following original electronic records used to prepare `VC-01`, `CBR-01`, or `CBR-02`:

1. Survey point/coordinate table for the **Visual Clean** surface shown on `VC-01`.
2. Survey point/coordinate table for the **post six-inch over-excavation** surface shown on `CBR-01`.
3. Point-by-point or surface-to-surface **elevation-difference / thickness table** used to prepare `CBR-02`.
4. Original digital terrain/surface files for the VC and over-excavated surfaces.

Preferred machine-readable formats include, but are not limited to:
- CSV / TXT / PNEZD point files;
- LandXML;
- Civil 3D surface export;
- TIN surface data;
- DWG / DXF containing survey points or 3D breaklines/contours;
- shapefile / geodatabase feature class with XYZ values;
- any survey software export preserving point Easting, Northing, Elevation and point code/description.

## Tier 2 — provenance/support records

If Tier 1 cannot be located, request:

1. survey field-book / point-number listing corresponding to `VC-01`, `CBR-01`, and `CBR-02`;
2. electronic survey-control / benchmark file used for the RYAN-BREMO survey;
3. transmittal from Flora Surveying Associates to Ryan Incorporated Central, Dominion, or Golder delivering these survey products;
4. CAD transmittal index or drawing register that gives the original filenames for `VC-01`, `CBR-01`, and `CBR-02`;
5. earthwork/surface-comparison report or software output documenting how the `CBR-02` thickness values were calculated.

## Tier 3 — exact missing public report component

Request/recover:

> `SWP618 Closure by Removal Construction Rpt- West Ash Pond Part 2 of 2`

and inspect it specifically for:
- additional Appendix A survey material;
- Appendix C six-inch removal documentation;
- survey point tables;
- survey-file names;
- CAD/source references;
- transmittal or attachment indexes.

## Minimum fields needed for validation

For each usable survey point, the decisive minimum is:

- point identifier, if present;
- Easting;
- Northing;
- VC elevation or equivalent pre-over-excavation elevation;
- final/post-over-excavation elevation;
- or direct measured thickness/elevation difference;
- units;
- coordinate system/datum confirmation.

No owner/client/project metadata is needed beyond what is necessary to prove the point file belongs to the Bremo `RYAN-BREMO` West Ash Pond survey.

## Acceptance rules

A recovered file may replace the F180 digitized horizontal coordinates only if:

1. it can be tied directly to `RYAN-BREMO`, `VC-01`, `CBR-01`, `CBR-02`, or the West Ash Pond CQA work;
2. the coordinate system is compatible with the published State Plane South / NAD83 / NAVD88 survey;
3. point/surface values are measured survey geometry, not design grades or approximate contours;
4. no Bremo thickness truth is used to shift, fit, vertically bias-correct, or otherwise alter the source file.

## Records that are NOT substitutes

Do not accept the following as equivalent to the requested source geometry:

- the 327,323 yd3 approximate initial-removal quantity alone;
- the 17-acre pond area alone;
- the 3.64 m volume/area normalization;
- design six-inch requirement without measured post-survey values;
- raster screenshots with no recoverable spatial calibration when better original data exists;
- unrelated later final grading surfaces.

## Preferred custodian order

Based strictly on the documented project roles, check/request in this order:

1. **Dominion Energy Virginia** project/CCR records — owner and final record holder.
2. **Flora Surveying Associates** — originator of the `RYAN-BREMO` survey drawings/data.
3. **Ryan Incorporated Central** — Flora was under contract to Ryan for this work.
4. **Golder/WSP legacy project archive** — CQA engineer received/used survey results.
5. **Virginia DEQ SWP618 record** — for Part 2 and any submitted record drawings/attachments retained with the permit file.

This ordering does not assert that every custodian still holds the files; it is a search priority based on documented project roles.

## F185 decision

**PASS — the missing artifact is now precisely specified.**

The Bremo source-data route is no longer a vague request for “survey records.” It has exact project, drawing, party, datum, date, and data-field identifiers.

## Next action — F186

Run a bounded public-source search using the exact identifiers:

- `RYAN-BREMO`
- `VC-01`
- `CBR-01`
- `CBR-02`
- `Flora Surveying Associates`
- `West Ash Pond`
- `SWP618`

Search only for an actual downloadable/source survey artifact or a direct file/transmittal reference. If the exact-identifier search finds none, close public recovery and move to the custodian-request route rather than restarting broad imagery/site searches.
