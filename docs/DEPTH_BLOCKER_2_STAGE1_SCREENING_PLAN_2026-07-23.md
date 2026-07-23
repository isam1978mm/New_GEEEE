# Depth Blocker 2 - Stage 1 Candidate Screening

**Date:** 2026-07-23  
**Mode:** Public-document research  
**Repository branch:** `main`

## Goal

Find public records that can support real Sentinel-1 relative-depth research.

A site is not "good to go" merely because a cover depth is known. It must pass the full screening ladder, especially observation-date depth, confirmed negatives, and radar linkage.

## Hard stopping rule

Screen no more than **15 candidates across at least 6 independent facilities**.

Stop the public-source search if fewer than **3 independent site groups** pass Gates 0-4 and have a realistic path through the confirmed-negative gate. At that point, recommend a different evidence route instead of searching indefinitely.

## Gate ladder

0. Correct target family, large enough for Sentinel-1, and isolated from neighboring work.
1. Independently measured depth from the final surface to the buried interface.
2. Numerical uncertainty, either published or defensibly calculated.
3. Depth still valid on the Sentinel-1 observation dates.
4. Suitable Sentinel-1 images exist before and after the event.
5. Moisture, vegetation, terrain, season, viewing angle, construction, and settlement can be controlled.
6. Enough independent facilities exist for train, validation, and untouched holdout.
7. Confirmed no-target comparison areas exist at Sentinel-1 scale.
8. Controlled radar differences actually track verified depth.

Reject a candidate at the first unrecoverable failure. A hold is allowed when a clearly obtainable public document could resolve the missing item.

## Uncertainty routes

### Route A - data-derived consistency

Use **combined spatial-block resampling plus an unchanged-area accuracy floor**.

Do not use single-point leave-one-out.

Required evidence:

- before-survey elevations;
- after-survey elevations;
- point locations or enough geometry to form spatial blocks;
- an overlapping area documented as unchanged and stable between surveys.

Required label:

`depth_reference_method = derived_survey_consistency`

The result must be marked:

`estimated from survey data - not published instrument accuracy`

The record must also state the block method, unchanged-area residual, registration/systematic term, and final combined uncertainty.

### Route B - published survey-control bound

An unchanged-area floor is preferred, but it is not the only defensible route.

Gate 2 may also pass when a signed/sealed survey record or related certification gives a **numerical vertical accuracy, registration tolerance, or control-network bound**, and documents that the before and after surveys use the same project control and vertical datum.

The record must cite the exact published bound and explain how it applies to the before/after surface difference. A shared firm, shared drawing, close survey dates, or a professional seal alone is not enough without a numerical bound.

A before/after map alone does not automatically pass.

## Stage 1 workflow

1. Work Elk Plain as the first example.
2. Screen 10-15 candidates across at least 6 facilities, prioritizing completed projects from 2015 onward with both as-built surveys and later settlement/topographic surveys.
3. Extract named documents, measured depth, uncertainty, dates, mapped extent, site isolation, and comparison-area evidence.
4. Check public Sentinel-1 acquisition availability.
5. Record each candidate as pass, hold, or rejected using the existing decision vocabulary.
6. Deliver a row-ready table in chat. No model fitting and no blocker-reopened claim.

---

# Work Log - Elk Plain County Shop

## Public records checked

1. **Survey of Cap Thickness Map**, AHBL, drawing C1.0, dated May 17, 2024; posted by Washington Ecology on June 18, 2024.
2. **AOC #14 Interim Action Completion Technical Memorandum**, Herrera, dated April 5, 2024.
3. **Ecology Feedback on Survey of Cap Thickness Map**, dated June 25, 2024.
4. **Cap Inspection Plan**, dated September 13, 2024.
5. **2025 Q4 Progress Report**, dated December 2, 2025.
6. Washington Ecology cleanup-site record, including the current NFA and environmental-covenant listing.

## Gate 1 - measured depth

### Before-survey elevations

**Found.**

The as-built drawing contains a panel titled **Survey of Consolidated Contaminated Soils Prior Soil Cap** with surveyed spot elevations and contours. The technical memorandum identifies the survey date as **August 16, 2023**.

### After-survey elevations

**Found.**

The drawing contains a panel titled **As-Built Survey Post Clean Soil Cap at Future Park Area** with spot elevations and contours. The technical memorandum identifies the survey date as **September 8, 2023**.

### Direct depth meaning

**Strong pass for the depth definition.**

For this clean-soil cover, the buried interface is the surveyed pre-cap contaminated-soil surface. Therefore, post-cap surface minus pre-cap surface is a direct measurement of cover thickness and depth to the buried interface, not a design-only estimate.

## Gate 2 - uncertainty

### Surveyed unchanged ground outside the cap

**Not confirmed.**

The drawing shows surrounding ground, roads, and slopes, but it does not label any overlapping area as unchanged and stable between the two surveys. The completion memorandum says the cap and surrounding disturbed areas were hydroseeded and describes ongoing or future grading. The visible surround cannot safely be treated as a zero-change control.

### Published survey-control route

**Hold pending one focused document check.**

Both survey panels appear on the same AHBL project drawing and the surveys were performed about three weeks apart. A related signed/sealed survey certification or survey-control note could provide a numerical registration or vertical-accuracy bound and confirm a shared datum.

The currently posted public C1.0 copy is marked **REVIEW SET**. Its visible title block, notes, and parsed PDF text do not state a numerical survey accuracy, registration tolerance, control-network accuracy, or vertical-datum bound. That public copy does not yet clear Gate 2, but a clearly related survey-control document could still resolve it.

### Gate 2 status

`evidence_verified_pending_support`

Do not classify Elk Plain as `rejected_missing_uncertainty` until the related survey-control notes or certification have been checked once. If no numerical bound is found and no unchanged overlap area exists, then Gate 2 becomes an unrecoverable uncertainty failure.

## Gate 0 - scale and isolation

### Gross scale

**Preliminary pass.**

The December 2, 2025 official progress report identifies a **5.31-acre parcel where contaminated soils were capped in place**. This is about **2.15 hectares**, so Elk Plain is not automatically too small for Sentinel-1.

This corrects the earlier use of a 2.27-acre park figure from an older broader-development record. That figure was not a reliable measurement of the capped parcel.

### Usable isolated interior

**Still open.**

The cap drawing shows a multi-acre footprint, but the exact capped polygon and the interior remaining after edge, road, slope, and mixed-pixel buffers still need measurement. Nearby grading and residential development may reduce the clean usable interior even though the gross parcel exceeds one hectare.

Current Gate 0 status:

`evidence_verified_pending_support`

A scale rejection is now justified only if the measured cap interior is too narrow or too mixed after buffering, not from the parcel acreage alone.

## Gate 3 - observation-date depth

**Hold.**

The depth surveys are close together in August and September 2023, and the cleanup work continued through October 2023. This creates a defensible near-construction observation window if matching Sentinel-1 acquisitions exist.

However, Ecology also stated that additional final grading would occur during later park and surrounding-area development. The current public record lists a recorded environmental covenant and a Site NFA decision in March 2026, but no later topographic survey has yet been found that re-measures the cap surface.

Gate 3 can pass by either:

1. using Sentinel-1 observations close to the September 8, 2023 as-built surface; or
2. finding a later survey that confirms the surface elevation for later Sentinel-1 dates.

Do not assume that the 2023 depth remained unchanged through later grading.

## Gate 4 - Sentinel-1 coverage

**Open.**

The ASF and Copernicus public catalogues are the approved sources for the exact pre/post acquisition check. The catalogue query must record acquisition dates, orbit direction/path, polarization, and valid coverage over the cap. General mission availability is not enough.

## Gates 7-8 - negatives and radar linkage

**High-risk and potentially terminal.**

The cap and nearby ground were graded and hydroseeded. Therefore:

- no adjacent area has yet been confirmed as an undisturbed no-target comparison;
- the cap event is time-matched with major surface changes in roughness, moisture, drainage, and vegetation;
- a Sentinel-1 change may reflect the fresh surface work rather than the depth of the buried interface.

A negative would likely need to come from a separate independently documented stable site, not the immediately disturbed surround.

Even with perfect depth and uncertainty records, Elk Plain must still demonstrate that adjusted radar differences track depth after controlling for the construction surface disturbance. Failure at that stage is a radar-linkage or sensor-mismatch rejection.

## Elk Plain decision

**Not good to go, but not rejected yet.**

Current classification:

`evidence_verified_pending_support`

Elk Plain does **not** count toward the three required independent site groups because Gates 0-4 are not complete.

## Exact next checks, in order

1. Measure the cap polygon and the usable interior after edge/road/slope buffering.
2. Check the related survey-control notes, certification, record survey, or signed/sealed version for a numerical vertical accuracy or registration bound and a common datum.
3. Query ASF/Copernicus for Sentinel-1 acquisitions close to the August 16 and September 8, 2023 surveys.
4. If those pass, assess whether the construction-surface confound can be controlled and whether an independent confirmed negative exists.
5. Reject at the first unrecoverable failure using the correct gate-specific reason.

---

# Candidate Mining - Arkansas ADEQ

## Source-class finding

Arkansas landfill rules are stronger than ordinary inventory records. Public regulations require final-cover certification reports to include as-constructed drawings showing:

- limits of final-cover construction;
- top and bottom final-cover elevations at 50-foot intervals;
- a site grid and permanent survey-control points;
- construction dates, testing locations, and professional certification.

This source class is still promising because top-minus-bottom elevations can provide direct cover thickness over large cells.

## Correction to ADEQ document 85246

The earlier description of document 85246 was inaccurate. Document 85246 is a **March 2024 response concerning an exposed geomembrane cover at Two Pine Landfill**, not itself a completed final-cover as-built table.

The correct evidence is:

- Arkansas rules require detailed as-constructed final-cover drawings;
- the Two Pine public facility index lists an **Exposed Geomembrane Cap Construction Quality Assurance Report Certification Report**, dated December 29, 2025;
- the facility remained active, and the listed work concerns a cap demonstration/repair rather than a cleanly isolated completed closure cell.

## Two Pine status

`candidate_under_review`

Two Pine is not yet a positive candidate. The December 2025 CQA report must be checked for actual top/bottom elevations, numerical survey tolerance, exact area, and construction dates. Even if those fields exist, the active-landfill setting and repair activity may fail isolation, observation-date validity, negatives, or radar linkage.

## Arkansas next action

1. Inspect the December 29, 2025 Two Pine CQA certification report.
2. Reject it immediately if it is only an exposed-surface repair or lacks a buried-interface depth.
3. Use the ADEQ facility index to find completed closure cells with the same required top/bottom elevation drawings.
4. Prefer closed/post-closure facilities with later settlement or topographic monitoring.
