# Depth Blocker 2 - Stage 1 Screening Results

**Date:** 2026-07-23  
**Mode:** Public-document research only  
**Branch:** `main`

This file records screening decisions made under `DEPTH_BLOCKER_2_STAGE1_SCREENING_PLAN_2026-07-23.md`.

## Current result table

| Facility | Decision | First unresolved or failed gate | Current classification |
|---|---|---|---|
| Elk Plain County Shop, Washington | HOLD - not good to go | Gate 2 survey accuracy/control bound; Gates 3, 7, and 8 also remain open | `evidence_verified_pending_support` |
| Two Pine Landfill, Arkansas | REJECTED | Gate 1: exposed geomembrane work does not provide a measured buried-interface depth | `rejected_missing_independent_depth` |
| Sunray #1 Landfill, Arkansas | REJECTED | Gate 0: approximately 0.7-acre narrow repair area is too small for the approved Sentinel-1 experiment | `rejected_scale_or_sensor_mismatch` |
| Sudbury Road Landfill, Washington | HOLD - not good to go | Actual final measured cover depths and numerical survey accuracy are not visible in the accessible public package | `evidence_verified_pending_support` |
| Recycled Aluminum Metals Co. (RAMCO), Washington | REJECTED | The contaminated material was removed before the excavation was filled and covered; no qualifying buried target remains | `rejected_out_of_finding_family` |
| Dryden Landfill, Washington | REJECTED | The final cover was built in 2003, before a usable Sentinel-1 pre/post construction experiment | `rejected_scale_or_sensor_mismatch` |
| Triune Mine, Washington | UNDER REVIEW - not good to go | The 2018 completion report must show actual cover depth, uncertainty, exact repository area, and as-built dates | `candidate_under_review` |

## Sudbury Road Landfill

### What passes

- The landfill is large: Washington Ecology describes the facility as about 125 acres.
- Cover-improvement construction was completed in 2017, inside the Sentinel-1 era.
- Public design and CQA documents require a minimum 4.8-foot soil cover and an as-built final-grade survey.
- A 2022 periodic review confirms the remedial covers continued to appear protective.

### What does not yet pass

The accessible public design documents state what had to be built and surveyed, but they do not expose the completed point-by-point top and bottom surfaces or a numerical survey-accuracy value. The named 2017 final CQA certification report is the one public document that could resolve this, but it was not readable through the portal during this review.

### Decision

**HOLD - not good to go.**

This is a hold rather than a rejection because a clearly named public final CQA report could contain the missing measurements. Even if Gate 2 later passes, the active-landfill setting still creates isolation, negative-area, and radar-linkage risks.

## RAMCO

Washington Ecology states that more than 135,000 tons of waste were removed between 2007 and 2010. The excavation was then filled and an erosion-control cover was completed in 2015.

### Decision

**REJECTED - not good to go.**

The cleanup removed the target material. The remaining feature is a backfilled excavation and surface cover, not a documented buried mass with a known depth to its top.

Classification: `rejected_out_of_finding_family`.

## Dryden Landfill

Washington Ecology states that final cover construction was completed in 2003 with about 30 inches of clean soil. Later periodic reviews report that the cap remains intact.

### Decision

**REJECTED - not good to go.**

The construction event occurred long before Sentinel-1. It cannot supply the required matched pre/post Sentinel-1 experiment, even though the later records help confirm long-term stability.

Classification: `rejected_scale_or_sensor_mismatch`.

## Triune Mine - next active lead

Washington Ecology states that the Bureau of Land Management completed cleanup in 2018 by moving about 5,500 cubic yards of mine tailings and waste rock into an onsite consolidated waste area, then covering it with a liner and clean soil. Ecology and BLM inspected the consolidated area in 2023 and reported that it appeared to be functioning as intended.

The public site index lists **Completion Report Triune Mine**, dated December 1, 2018, as a remedial action/as-built report.

### Why it deserves one detailed check

- Construction occurred in the Sentinel-1 era.
- A real engineered buried mass remains onsite.
- A later 2023 inspection exists.
- A named as-built completion report exists.

### Exact next check

Inspect the 2018 completion report for:

1. actual measured cover thickness or surveyed top/bottom surfaces;
2. numerical survey accuracy or control tolerance;
3. exact consolidated-waste-area boundary and usable interior area;
4. construction and survey dates;
5. evidence that the 2023 condition supports observation-date depth;
6. a realistic independent negative and a path to controlling surface-construction effects.

If the report contains only planned thickness or no numerical uncertainty, reject Triune at the first failed gate.

## Stage 1 tally

- Independent facilities screened or entered: **7**
- Rejected: **4**
- Hold: **2**
- Under review: **1**
- Independent site groups clearing Gates 0-4: **0**

The hard stopping threshold has not yet been reached because the approved plan allows up to 15 candidates. The search must still stop at 15 candidates, or earlier if the remaining public source classes clearly cannot produce three qualifying site groups.

## Official source references

- Washington Ecology cleanup-site pages for Elk Plain County Shop, Sudbury Road Landfill, RAMCO, Dryden Landfill, and Triune Mine.
- Arkansas ADEQ public facility records and final-cover certification requirements for Two Pine and Sunray #1.
- Washington Ecology, **Completion Report Triune Mine**, December 1, 2018, listed as a remedial action/as-built report.
