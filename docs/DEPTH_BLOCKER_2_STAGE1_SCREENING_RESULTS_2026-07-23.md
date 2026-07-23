# Depth Blocker 2 - Stage 1 Screening Results

**Date:** 2026-07-23  
**Mode:** Public-document research only  
**Branch:** `main`

This file records screening decisions made under `DEPTH_BLOCKER_2_STAGE1_SCREENING_PLAN_2026-07-23.md`.

## Final Stage 1 decision

**No candidate is good to go.**

The approved hard stop of **15 candidates** has been reached. Public-only searching must stop here rather than continue indefinitely.

Final result:

- candidates screened: **15**;
- rejected: **12**;
- hold pending a specific missing public record: **3**;
- independent site groups clearing Gates 0-4: **0**;
- Blocker 2 status: **still blocked**.

This does not prove that depth calibration is impossible. It shows that the screened public-document route did not produce a complete contract-ready dataset.

## Final result table

| # | Facility | Decision | First unresolved or failed gate | Classification |
|---:|---|---|---|---|
| 1 | Elk Plain County Shop, Washington | HOLD - not good to go | Survey accuracy/control bound is missing; later grading, negatives, and radar linkage also remain open | `evidence_verified_pending_support` |
| 2 | Two Pine Landfill, Arkansas | REJECTED | Exposed geomembrane work does not provide measured depth to a buried interface | `rejected_missing_independent_depth` |
| 3 | Sunray #1 Landfill, Arkansas | REJECTED | Approximately 0.7-acre narrow repair area is too small for the approved Sentinel-1 experiment | `rejected_scale_or_sensor_mismatch` |
| 4 | Sudbury Road Landfill, Washington | HOLD - not good to go | Actual measured cover depths and numerical survey accuracy are not visible in the accessible CQA package | `evidence_verified_pending_support` |
| 5 | Recycled Aluminum Metals Co. (RAMCO), Washington | REJECTED | Waste was removed before the excavation was filled and covered | `rejected_out_of_finding_family` |
| 6 | Dryden Landfill, Washington | REJECTED | Final cover was built in 2003, before a usable Sentinel-1 pre/post experiment | `rejected_scale_or_sensor_mismatch` |
| 7 | Triune Mine, Washington | HOLD - not good to go | The named as-built report is public, but measured depth, uncertainty, area, and survey dates are not visible in the accessible copy | `evidence_verified_pending_support` |
| 8 | Landsburg Mine, Washington | REJECTED | Two feet of soil is documented above a liner, not from the surface to the buried industrial waste | `rejected_missing_independent_depth` |
| 9 | K Ply, Washington | REJECTED | Contaminated soil was excavated and replaced with clean fill; no qualifying mapped buried target remains | `rejected_out_of_finding_family` |
| 10 | Tecumseh Energy Center Landfill 322, Kansas | REJECTED | The report certifies minimum cover layers, but the final-cover subgrade may be soil or CCR, so actual depth to CCR is not established | `rejected_missing_independent_depth` |
| 11 | Montrose North/South Ash Impoundments, Missouri | REJECTED | CCR was removed; no positive buried target remains | `rejected_out_of_finding_family` |
| 12 | La Cygne Bottom Ash Impoundment, Kansas | REJECTED | Closure was completed by removing CCR | `rejected_out_of_finding_family` |
| 13 | Sibley Slag Settling Impoundment, Missouri | REJECTED | Closure was completed by removing CCR | `rejected_out_of_finding_family` |
| 14 | Jeffrey Energy Center Bottom Ash Pond, Kansas | REJECTED | Large closure-in-place area exists, but the final-cover subgrade may be CCR or soil and only minimum layer thickness is published | `rejected_missing_independent_depth` |
| 15 | Iatan Ash Impoundment, Missouri | REJECTED | Closure was completed by removing CCR and placing it in the onsite landfill or beneficial use | `rejected_out_of_finding_family` |

## Holds retained for one specific document check

### Elk Plain County Shop

Elk Plain has direct before/after survey-based cap thickness over a multi-acre parcel. It remains on hold only for a numerical survey-control or registration bound. Even if that record is found, later grading, confirmed negatives, and radar linkage remain difficult.

### Sudbury Road Landfill

Sudbury is large and its cover work was completed in 2017. The public design material requires an as-built survey, but the accessible copy of the final CQA package does not reveal actual point-by-point depth or numerical accuracy.

### Triune Mine

Triune has an S1-era onsite consolidated waste area and a named 2018 as-built completion report. The accessible public copy does not reveal the measurements needed to pass depth, uncertainty, scale, and observation-date gates.

These holds do not count as qualifying site groups.

## Evergy CCR source-class result

The Evergy public CCR portal is a stronger document class than ordinary landfill inventories. It provides named closure certifications, plans, final-cover drawings, construction dates, areas, professional certifications, and continuing monitoring records.

However, the completed records screened here still failed for one of two reasons:

1. **Clean closure:** the CCR was removed, leaving no positive buried target.
2. **Closure in place:** reports certify minimum cover construction, but do not publish a mapped, measured surface-to-CCR depth with numerical uncertainty. In the Tecumseh and Jeffrey reports, the final-cover subgrade may contain CCR or added soil, so the published 18-inch plus 6-inch minimum cannot automatically be treated as depth to the top of CCR.

### Tecumseh Energy Center Landfill 322

- closure in place completed in 2021;
- approximately 23.4 acres received the new final cover;
- report certifies a minimum 18-inch infiltration layer plus a minimum 6-inch topsoil layer;
- public report contains no numerical survey tolerance;
- subgrade is described as compacted and graded soil or CCR material.

Decision: **REJECTED - not good to go.** The published minimum cover does not establish actual measured depth to CCR.

### Montrose North/South Ash Impoundments

The completion package contains detailed third-party surveys, coordinates, datum information, phased excavation surfaces, and a survey-point table. These are useful engineering records, but the CCR was removed and the area was converted for another use.

Decision: **REJECTED - not good to go as a positive depth site.**

### La Cygne Bottom Ash Impoundment

The closure certification explicitly states that CCR was excavated and removed. Survey documentation verifies removal, but no buried positive target remains.

Decision: **REJECTED - not good to go.**

### Sibley Slag Settling Impoundment

The closure certification explicitly states that slag was excavated and removed.

Decision: **REJECTED - not good to go.**

### Jeffrey Energy Center Bottom Ash Pond

- approximately 65-acre closure-in-place area;
- approximately one million cubic yards of CCR;
- construction completed in 2021;
- minimum 18-inch infiltration layer plus minimum 6-inch erosion layer;
- final cover drawing and professional certification are public;
- final-cover subgrade may be CCR or soil;
- no mapped actual thickness values or numerical survey accuracy are published in the completion package.

Decision: **REJECTED - not good to go.** The depth to actual CCR is not independently established.

### Iatan Ash Impoundment

The closure plan and completion listing describe closure by removal. About 1.7 million cubic yards had been stored, and removal progress was checked with bathymetric surveys before material was moved to the onsite landfill or beneficial use.

Decision: **REJECTED - not good to go as a positive depth site.**

## Why the public-only route stopped

The recurring problem is no longer simply finding construction reports. The reports exist, but they usually provide one of these incomplete combinations:

- planned or minimum thickness instead of measured depth to the target;
- measured surfaces without numerical uncertainty;
- excellent removal surveys but no buried target left;
- valid depth records outside the Sentinel-1 era;
- small or mixed footprints;
- no confirmed negative area;
- major surface disturbance that prevents a clean radar-to-depth test.

Continuing to search similar public closure reports is unlikely to produce three independent site groups that pass Gates 0-4 and also have a realistic negative and radar-linkage path.

## Recommended next evidence route

Do not loosen the contract and do not invent uncertainty.

The next route should use a **small private or directly supplied survey dataset** from at least three independent completed sites. Each site package needs:

- digital before and after survey points or surfaces;
- survey-control accuracy or stable unchanged overlap;
- exact construction and survey dates;
- a large isolated footprint;
- later topographic or settlement confirmation when observations are not near construction;
- independently confirmed no-target comparison areas.

A controlled benign-cover experiment performed and surveyed by qualified professionals could also supply the missing evidence, but it is a separate project and requires explicit authorization. No such work is started by this Stage 1 assessment.

## Governance outcome

- Stage 1 is **complete**.
- The assistant does **not** declare Blocker 2 reopened or solved.
- No model fitting is allowed.
- No validator weakening is justified.
- The three holds may be revisited only if the exact missing public record becomes available.
- Further broad public-source searching is stopped under the approved hard rule.

## Official source references

- Washington Ecology public cleanup-site pages and document indexes for Elk Plain County Shop, Sudbury Road Landfill, RAMCO, Dryden Landfill, Triune Mine, Landsburg Mine, and K Ply.
- Arkansas ADEQ public facility records and final-cover certification requirements for Two Pine and Sunray #1.
- Evergy CCR Rule Compliance Data and Information portal and the listed closure-completion packages for Tecumseh, Montrose, La Cygne, Sibley, Jeffrey, and Iatan.
