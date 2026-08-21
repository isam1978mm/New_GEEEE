# F184 — Bremo source-survey deliverable screen

Date: 2026-08-21

## Purpose

After F180 froze a measured `CBR-02` truth subset and F181-F183 closed the obvious public lidar/VBMP/NAIP before-after routes on timing/coverage, test whether the official Bremo closure record exposes the **original Flora survey deliverable** behind Appendix A: CAD, point table, coordinate file, TIN/surface, electronic survey export, or another record that can reproduce the VC and over-excavation surfaces numerically.

## Sources inspected

1. Official Virginia DEQ West Ash Pond CQA package Part 1 supplied in Project Sources:
   - `Closure by Removal Construction — Bremo Power Station — West Ash Pond (VDEQ Permit No. 618)`
   - Golder Associates Inc.
   - Project No. 19-133736
   - March 25, 2020
2. Directly rendered Appendix A survey sheets:
   - `VC-01` — Visual Clean Survey
   - `CBR-02` — Closure by Removal Thickness Survey
   - `CBR-01` — Closure by Removal Survey
3. Virginia DEQ public Bremo operating-record index.
4. Dominion Energy public Bremo CCR records and related Bremo survey-derived figures.

## What the Appendix A title block proves

Direct inspection of the `CBR-02` title block establishes:

- Surveyor: **Flora Surveying Associates**
- Survey project: **RYAN-BREMO**
- Location/project: Bremo Power Station, New Canton, Commonwealth of Virginia
- Sheet title: `CLOSURE BY REMOVAL THICKNESS SURVEY`
- Drawing number: `CBR-02`
- Scale: 1 inch = 50 ft
- Drawing date: 2/28/2020
- Signed/sealed by Bruce W. Flora, Virginia Professional Land Surveyor
- Notes say information was field surveyed between 6/4/2017 and 1/30/2020 and referenced to Virginia State Plane South NAD83 / NAVD88.

The title block does **not** expose a DWG filename, point-file name, TIN filename, CSV, XML, LAS, or other original electronic survey filename.

## Embedded-file check

The supplied Part 1 PDF contains **zero embedded file attachments**.

Therefore `VC-01`, `CBR-02`, and `CBR-01` are published as drawing content only in this package; the original Flora source files are not embedded inside the supplied PDF.

## Text/index search result

A full-document search of the uploaded Part 1 for likely source-file terms (`DWG`, point file, coordinate file, electronic survey, CAD, TIN, surface file, Flora project/file references) did not recover an original electronic survey filename or attachment reference.

This negative result does not mean the source data never existed; the drawings themselves prove it did.

## Part 2 status

Virginia DEQ's official Bremo operating-record page explicitly lists:

- `SWP618 Closure by Removal Construction Rpt- West Ash Pond Part 1 of 2`
- `SWP618 Closure by Removal Construction Rpt- West Ash Pond Part 2 of 2`

The currently supplied file is Part 1.

The DEQ search/index confirms Part 2 exists, but the current web-access path did not expose a separately retrievable Part 2 document URL/content in this environment. Therefore **Part 2 was not directly inspected in F184** and no claim is made about whether it contains additional source-survey references.

## Related public-record clue

Dominion/Golder later Bremo figures state that existing pond-area conditions were based on multiple field surveys by H&B Surveying & Mapping, Flora Surveying Associates, Ryan Construction, and Glover Construction collected from 2017 through 2020 and compiled by Golder.

This strengthens provenance that electronic survey data existed in the project workflow, but those later public figures publish the compiled result, not the original Flora `RYAN-BREMO` point/surface files.

Separately, some Bremo DEQ/Golder drawings expose internal Golder DWG paths for engineering drawings. That demonstrates that source-path metadata can survive into published sheets, but the Flora Appendix A `CBR-02` title block itself does not publish such a path.

## F184 decision

### Original Flora electronic survey deliverable: NOT RECOVERED

What is now proven:

- the exact survey organization and PLS;
- project identifier `RYAN-BREMO`;
- exact drawing identifiers `VC-01`, `CBR-01`, `CBR-02`;
- coordinate/vertical datum;
- survey date range;
- direct numerical measured-thickness drawing content;
- a public DEQ Part 2 exists.

What remains missing:

- original point table / coordinate export;
- original CAD/DWG/DXF;
- original TIN/surface or survey comparison model;
- any electronic file containing the paired VC and six-inch surfaces;
- direct inspection of West Ash Pond CQA Part 2.

## Scientific status

This does **not** invalidate F180. The frozen `CBR-02` thickness labels remain direct measured survey-to-survey references.

It does mean that the pilot horizontal coordinates remain digitized from the published State Plane grid rather than imported from original survey points.

Numerical depth validation is still not complete because no independent historical/elevation product matching the 2019-2020 interval has yet survived the timing/coverage/accuracy gates.

## Next action — F185

Create an exact **source-survey recovery specification** using the identifiers now available, so any records search or custodian request asks for the smallest decisive artifact instead of requesting the entire Bremo archive.

Priority requested artifacts:

1. Flora `RYAN-BREMO` point file / coordinate table used for `VC-01`;
2. Flora `RYAN-BREMO` point file / coordinate table used for `CBR-01`;
3. the surface-comparison / thickness source used to create `CBR-02`;
4. CAD/DWG/DXF or LandXML/TIN equivalents for those three drawings;
5. West Ash Pond CQA Report Part 2 of 2 if it contains any of the above or additional survey-file references.

Do not reopen generic public imagery searches before this exact source-data route is specified and checked.
