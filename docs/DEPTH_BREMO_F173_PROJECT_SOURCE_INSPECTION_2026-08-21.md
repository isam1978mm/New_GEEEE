# Bremo F173 — Project-source inspection of `pc_complete_2017-3-7.pdf`

Date: 2026-08-21

## Purpose

Inspect the actual project-source PDF supplied by the user and determine whether it contains a trustworthy numerical pre-excavation surface for the Bremo Power Station West Ash Pond.

## Source inspected

`pc_complete_2017-3-7.pdf` — Fluvanna County Planning Commission packet, March 7, 2017, containing Attachment C / Dominion Bremo Power Station CCR Surface Impoundment Closure Plan drawings.

## What the source proves

The updated plan-set cover/index notes explicitly state:

- field-run topography by H&B Surveying & Mapping;
- collected on 2016-06-09;
- within the limits of the West Ash Pond only;
- site datum NAD83 / NAVD88, Virginia State Plane South.

Therefore a real field survey of the West Ash Pond existed immediately before the documented July 2016 excavation work.

## Critical contradiction in the same source

The detailed West Ash Pond existing-conditions sheet is Drawing 7.

Drawing 7:

- is Revision 0;
- carries a 2015 design/drawing date, before the 2016-06-09 H&B survey existed;
- states in its general notes that existing topography within the West Ash Pond and North Ash Pond is based on a **conceptual post-dredging surface**;
- does not identify the 2016-06-09 H&B field survey as the detailed West Pond surface source.

Drawing 14, the West Ash Pond cross-section sheet, is also a 2015 drawing and distinguishes:

- Existing Grade;
- Post-Dredging Grade;
- Proposed Final Grade.

This means the uploaded packet cannot safely be interpreted as if the detailed West Pond geometry were the June-2016 measured survey.

## File/attachment inspection

The PDF was also checked for an embedded or named H&B numerical survey source.

Result:

- no embedded PDF attachments;
- no H&B DWG filename exposed;
- no DXF;
- no CSV/XYZ point file;
- no TIN/LandXML surface;
- no explicit H&B survey job/file identifier tied to the 2016-06-09 field topography.

The plan-set CAD filenames exposed in the packet are Golder plan-drawing files such as `1520347X07.dwg`, not the underlying H&B survey deliverable.

## Decision

Bremo remains a **high-priority open elevation-validation candidate**, because the source proves that a properly timed field survey existed.

However, `pc_complete_2017-3-7.pdf` by itself does **not** provide a trustworthy numerical pre-excavation surface suitable for direct depth differencing.

Do not digitize Drawing 7 and label it the June-2016 measured pre-excavation surface.

## Exact missing artifact

Recover one of the following from the H&B / Dominion / Golder project records:

- the 2016-06-09 West Ash Pond field-survey point file;
- the corresponding H&B survey DWG/DXF;
- a TIN/LandXML/DTM surface built directly from that survey;
- another issued drawing that explicitly contains the 2016-06-09 measured West Pond topography with sufficient numerical detail and provenance.

## Route status

- Tyrone Step 4: still blocked, separate route.
- Meredosia: blocked by clean backfill hiding true excavation floor.
- John Sevier: high-priority open, missing numerical as-built subgrade surface.
- Bremo: high-priority open; timing/survey existence proven, numerical pre-excavation surface not yet recovered.
- Plant Kraft: post-surface pass / pre-surface blocked.

## Continuity rule

Do not repeat the oversized-PDF access search. The PDF is now in project Sources and has been directly inspected. The remaining Bremo task is specifically to recover the underlying 2016-06-09 H&B West Ash Pond survey deliverable or an equivalent numerical representation.
