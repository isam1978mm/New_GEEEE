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
5. Washington Ecology SEPA records for the Elk Plain Crossing development and Future Park area.

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

**Open and potentially terminal.**

Public SEPA material describes the broader Future Park area as about **2.27 acres**, approximately **0.92 hectares**. The exact capped polygon still needs confirmation from the survey boundary.

This is close to, but not clearly above, a one-hectare screening threshold. Its narrow shape, nearby road, grading, slopes, and surrounding development may create mixed Sentinel-1 pixels. Elk Plain cannot count as a qualifying site group until the exact capped area and usable isolated interior are measured.

Possible terminal classification:

`rejected_scale_or_sensor_mismatch`

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

1. Measure or confirm the exact capped footprint and determine whether it has a sufficiently large isolated interior for Sentinel-1.
2. Check the related survey-control notes, certification, record survey, or signed/sealed version for a numerical vertical accuracy or registration bound and a common datum.
3. If scale passes and Gate 2 can be resolved, check observation-date depth and Sentinel-1 coverage.
4. Assess whether any independent confirmed negative exists and whether the surface-construction confound can realistically be controlled.
5. Reject at the first unrecoverable failure using the correct gate-specific reason.

---

# Candidate Mining Started

The first follow-on search has begun in official Arkansas ADEQ landfill records.

A 2023 public record (ADEQ document 85246) requires a final signed and sealed **Final Cover as-built with elevation points table** and AutoCAD deliverables. This is only a lead: the requirement does not prove that the completed as-built table is publicly available or that it includes uncertainty, observation-date confirmation, negatives, or radar linkage.

Current status:

`candidate_under_review`

Next check: locate the matching completed closure/CQA submission and determine whether it contains measured layer surfaces, numerical tolerance or a stable control area, exact dates, and a large isolated footprint.
