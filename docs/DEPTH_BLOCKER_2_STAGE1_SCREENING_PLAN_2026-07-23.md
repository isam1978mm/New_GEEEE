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

Reject a candidate at the first unrecoverable failure. A hold is allowed only when a clearly obtainable public document could resolve the missing item.

## Data-derived uncertainty method

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

## Required raw-data check

### Before-survey elevations

**Found.**

The as-built drawing contains a panel titled **Survey of Consolidated Contaminated Soils Prior Soil Cap** with surveyed spot elevations and contours. The technical memorandum identifies the survey date as **August 16, 2023**.

### After-survey elevations

**Found.**

The drawing contains a panel titled **As-Built Survey Post Clean Soil Cap at Future Park Area** with spot elevations and contours. The technical memorandum identifies the survey date as **September 8, 2023**.

### Surveyed unchanged ground outside the cap

**Not confirmed.**

The drawing shows surrounding ground, roads, and slopes, but it does not label any overlapping area as unchanged and stable between the two surveys. The completion memorandum says the cap and surrounding disturbed areas were hydroseeded and describes ongoing/future grading. Therefore, the visible surrounding ground cannot safely be treated as a true zero-change control.

## Uncertainty-method decision

- Spatial-block testing may be possible from the mapped thickness points.
- The required unchanged-area accuracy floor cannot be calculated from the currently public records.
- Block variation alone would measure precision but would remain blind to survey registration or datum offset.

## Elk Plain decision

**Not good to go.**

Elk Plain has strong directly measured depth evidence, but the combined uncertainty method cannot be completed from the public package because no stable unchanged overlap area is documented.

Current classification:

`rejected_missing_uncertainty`

Keep it in the research record as a strong measured-depth example, but stop spending additional Stage 1 time on it unless a public raw survey file or a clearly documented unchanged control area appears.

## Next active task

Move to other completed cap projects. Prioritize facilities with:

- as-built before/after surfaces;
- a documented stable control area or published survey accuracy;
- a later settlement or topographic survey;
- construction in the Sentinel-1 era;
- a large, isolated cell;
- independent confirmed comparison areas.

---

# Candidate Mining Started

The first follow-on search has begun in official Arkansas ADEQ landfill records.

A 2023 public record (ADEQ document 85246) requires a final signed and sealed **Final Cover as-built with elevation points table** and AutoCAD deliverables. This is only a lead: the requirement does not prove that the completed as-built table is publicly available or that it includes uncertainty, observation-date confirmation, negatives, or radar linkage.

Current status:

`candidate_under_review`

Next check: locate the matching completed closure/CQA submission and determine whether it contains measured layer surfaces, numerical tolerance or a stable control area, exact dates, and a large isolated footprint.
