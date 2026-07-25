# J.C. Weadock Confirmed Removal Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** strongest physically confirmed no-target lead; exact final boundary and clean timing still incomplete  
**Purpose:** record the bounded evidence recovered from the official J.C. Weadock Bottom Ash Pond closure-by-removal package

## Plain-English result

J.C. Weadock Bottom Ash Pond is now the strongest confirmed no-target lead in the project.

Official Consumers Energy and EGLE-backed records establish that CCR was removed between February and July 2020. The removal was checked using a 50-foot grid, photographs, elevation comparisons, color testing, microscopy where needed, regulator review, and professional-engineer certification. Areas that failed the checks were excavated again. The area was then backfilled with clean fill, graded for drainage, and vegetated.

This evidence is stronger than J.H. Campbell because the public certification gives the grid spacing and the number of verification nodes.

It still cannot become a calibration row because the public map labels the excavation boundary as approximate, the exact Figure 3 grid-node drawing has not been recovered, and a clean unchanged Sentinel-1 period has not been verified.

## Official removal evidence

The November 2023 Closure by Removal Certification states that:

- the plant stopped operating in May 2016;
- hydraulic loading to the pond stopped in April 2018;
- CCR excavation occurred from February through July 2020;
- a 50-foot verification grid was created across the pond;
- 237 grid nodes covered the original pond limits;
- 35 additional grid nodes covered the expanded excavation around the chemical-treatment basins;
- photographs were taken at at least half of the nodes;
- colorimetric analysis was performed at at least one quarter of the nodes;
- microscopy was used where soil color made color testing unreliable;
- failed nodes triggered further excavation and retesting;
- final excavation elevations were checked against prior borings and engineering records;
- EGLE agreed that the bottom ash had been removed;
- a qualified professional engineer certified the closure;
- the excavation was backfilled with clean fill and vegetated.

Recovered verification summary:

```text
verification_grid_spacing_ft = 50
original_pond_grid_nodes = 237
expanded_area_grid_nodes = 35
total_grid_nodes = 272
photographic_node_coverage_minimum = 50_percent
colorimetric_node_coverage_minimum = 25_percent
regulator_concurrence = yes
professional_engineer_certification = yes
clean_fill_backfill = yes
vegetated_final_surface = yes
```

## Exact-boundary limitation

The July 2023 official site figure states that its displayed excavation boundary was based on:

`Figure 3: CCR Removal Documentation - Sample Grid Nodes, Rev. C, dated 08/26/2020.`

However, the public site figure still labels the displayed boundary as approximate.

Therefore:

```text
physical_no_target_confirmation = yes
mapped_verification_grid_exists = yes
exact_grid_node_map_recovered = no
exact_surveyed_removal_boundary = no
private_geometry_extracted = no
clean_sentinel1_window_verified = no
eligible_negative_calibration_row = no
```

## Comparison with current leading sites

```text
strongest_positive_depth_site = J.R. Whiting Ponds 1 and 2
strongest_confirmed_no_target_site = J.C. Weadock Bottom Ash Pond
```

J.C. Weadock and J.R. Whiting are separate physical site groups. Weadock could potentially provide an independent negative group, but it cannot be represented as the same-site negative comparison for Whiting.

## Decision

Do not create a negative calibration row yet.

The physical removal evidence is good enough. The remaining blocker is now narrow and clear: recover the final August 2020 verification-grid drawing or another exact as-built excavation boundary, then verify a stable Sentinel-1 observation period.

## Next bounded action

Continue only with:

1. Figure 3, `CCR Removal Documentation - Sample Grid Nodes`, Rev. C, dated August 26, 2020;
2. the August 2020 Golder CCR Removal Documentation Report;
3. EGLE's November 30, 2020 approval or concurrence package and attachments;
4. final grading or as-built drawings of the restored pond footprint;
5. official inspection or aerial records proving the restored surface remained unchanged.

Current project readiness remains:

```text
usable_calibration_rows = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```
