# J.H. Campbell Confirmed Removal Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** strong physically confirmed no-target lead; exact surveyed boundary and clean timing still incomplete  
**Purpose:** record the bounded evidence recovered from the official J.H. Campbell Ponds 1-2 closure-by-removal package

## Plain-English result

J.H. Campbell Ponds 1-2 is now one of the strongest confirmed no-target leads in the project.

Official Consumers Energy records establish that CCR was removed from the former ponds in 2018. Michigan EGLE staff observed the removal process and later agreed in writing that all bottom ash had been removed. The excavated surface was checked on a grid using visual inspection, color measurement, and microscopy where needed. Areas that failed the check were excavated again. The former pond excavation was then backfilled with clean fill, graded for drainage, and vegetated.

This is much stronger than an analyst-selected background polygon.

It still cannot become a calibration row because the public map labels the excavation boundary as approximate, the exact surveyed removal footprint has not been extracted, and a clean unchanged Sentinel-1 period has not been verified.

## Official evidence

The July 2023 J.H. Campbell Ponds 1-2 Selection of Remedy Report states that:

- Ponds 1-2 were former bottom-ash ponds used until 2018;
- dewatering and ash excavation ran from June through October 2018;
- final CCR removal documentation was submitted to EGLE with a qualified-professional-engineer certification;
- EGLE provided written concurrence on October 22, 2019 that all bottom ash had been removed;
- EGLE staff observed the removal process;
- excavation proceeded to at least the base-of-CCR elevation established from plant drawings and soil borings;
- verification nodes were established using EGLE guidance;
- visible CCR triggered further excavation;
- remaining surfaces were checked by colorimetric analysis;
- nodes requiring more review were checked by microscopy;
- material above the allowed trace threshold triggered further excavation;
- the multiple lines of evidence confirmed removal of the CCR material;
- the excavation was backfilled with clean fill, graded for drainage, and vegetated;
- later groundwater wells installed inside the former pond footprint showed Appendix IV concentrations below federal groundwater-protection standards;
- the source-removal remedy was formally certified complete in 2023.

## Important boundary limit

The public Figure 1 provides:

- the former pond wetted boundaries;
- the work-plan excavation boundary;
- monitoring-well locations;
- a professional map coordinate system and drawing scale.

However, its legend explicitly calls the excavation boundary approximate.

Therefore:

```text
physical_no_target_confirmation = yes
regulator_observation = yes
engineer_certification = yes
clean_fill_backfill = yes
vegetated_final_surface = yes
exact_surveyed_removal_boundary = no
private_geometry_extracted = no
clean_sentinel1_window_verified = no
eligible_negative_calibration_row = no
```

## Site-group rule

J.H. Campbell is a separate physical site group from J.R. Whiting. It could potentially provide an independent negative site group, but it cannot serve as the same-site negative comparison for J.R. Whiting.

The former north and south ponds at J.H. Campbell belong to the same physical site group and must not be split across train, validation, and holdout as if they were independent sites.

## Current decision

J.H. Campbell is stronger confirmed-negative evidence than Go East because removal was checked on a defined verification grid, observed by EGLE, certified by a qualified engineer, and followed by clean-fill restoration.

The current public figure is still not precise enough for a calibration polygon.

Do not create a negative calibration row yet.

## Next bounded action

Continue only with:

1. the August 2019 CCR Removal Documentation Report for the verification-node map and final surveyed excavation boundary;
2. EGLE's October 22, 2019 concurrence letter and attachments;
3. final grading or as-built drawings showing the restored footprint;
4. official inspection or aerial records proving a stable post-restoration Sentinel-1 period;
5. another complete independent site group for validation or holdout.

Current project readiness remains:

```text
strongest_positive_site = J.R. Whiting Ponds 1 and 2
strongest_confirmed_negative_site = J.H. Campbell Ponds 1-2
usable_calibration_rows = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```
