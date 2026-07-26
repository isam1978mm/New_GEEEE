# John Sevier Bottom Ash Pond — Measured-Cover Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority measured-cover candidate, not yet a usable calibration row.

The John Sevier Bottom Ash Pond is stronger than a design-only cap lead. Official TVA engineering records repeatedly state that closure construction was completed and that a final 24-inch soil layer was actually placed above the eastern geomembrane cap. Annual inspections from 2019 through 2026 repeatedly report no change in unit geometry and no structural deficiencies. The 2026 inspection reports less than 0.1 foot of settlement at both monitored locations during the review period.

The candidate still cannot enter the depth-calibration pack. The publicly readable records describe the cap footprint only approximately, the large construction-history file could not be extracted, and no project-specific numerical construction or survey tolerance for the 24-inch layer has been recovered. The active gas plant and monitoring infrastructure also require exact subarea exclusion rather than use of the whole facility.

## What is confirmed

- Site: TVA John Sevier Fossil Plant, Bottom Ash Pond, Hawkins County, Tennessee.
- The coal-fired units ceased operation and were retired before the closure work; a gas-generation facility remains active elsewhere on the broader property.
- The Bottom Ash Pond stopped receiving CCR and was closed in 2017.
- Closure construction was completed in December 2017.
- CCR was removed from the western side down to native material, consolidated in the eastern side, and capped.
- The consolidated eastern CCR area is described as approximately 19 to 20 acres within the former 42-acre unit.
- The final cover system is described from bottom to top as:
  - 40-mil LLDPE geomembrane;
  - geocomposite drainage layer;
  - 18-inch cover-soil layer;
  - 6-inch vegetative cover.
- Official inspection records state that the final 24 inches of cover soil was placed, rather than merely proposed.
- A qualified professional engineer certified closure completion under the CCR Rule.
- The cap construction was reported complete in July 2017, with overall closure construction completed in December 2017.
- The 2019 and 2020 inspections recorded early post-construction settlement in inches and reported no geometry change.
- The 2021 report recorded cumulative settlement values near 0.6 foot at two instruments, while also reporting no visible instability, depression, or new area of interest.
- The 2022 inspection recorded less than 0.6 inch of settlement during its review period and no geometry change.
- The 2023, 2024, and 2025 annual inspections reported no structural areas of interest and no annual geometry change.
- The 2026 inspection recorded less than 0.1 foot settlement at both magnetic extensometers, described little to no settlement since the prior annual inspection, and reported no geometry change or structural deficiency.
- Later inspections consistently describe good vegetative cover, satisfactory drainage, no global slope instability, and no sinkholes or depressions on the capped area.
- The 2026 instrumentation map uses NAD 1983 StatePlane Tennessee FIPS 4100 Feet, but the displayed CCR unit boundary is explicitly approximate.
- Annual cover-system integrity studies are referenced for multiple years, including FY2020, FY2021, FY2022, and FY2024, but the studies were not found as separate public downloads.

## Why it is not yet usable

1. The exact surveyed polygon of the geomembrane-capped eastern area has not been extracted.
2. Public annual-inspection maps label the CCR unit and inspection extents as approximate.
3. The 98 MB History of Construction file timed out in the web fetch and could not be downloaded in the local environment.
4. The smaller liner-design file includes a closure-limits figure, but the figure could not be rendered and its parsed text does not provide polygon vertices.
5. No project-specific numerical horizontal or vertical survey accuracy has been recovered.
6. No construction-quality tolerance or measured thickness range has been recovered for the nominal 24-inch cover layer.
7. A statement that 24 inches was placed is strong engineering evidence, but the dataset contract still requires documented numerical uncertainty or a finite source-provided bounded interval.
8. Settlement was measurable after closure. A calibration interval must start only after a documented stable period and must exclude local settlement-instrument zones.
9. Minor maintenance observations such as animal burrows, vegetation overgrowth, rutting, drainage structures, wells, and instrument locations must be excluded from candidate subareas.
10. The broader property contains an operating gas plant and ongoing groundwater monitoring, so the whole facility cannot be treated as an unchanged comparison area.
11. Coal ash beneath a geomembrane cap is a heterogeneous engineered reference mass. The calibration contract must explicitly allow this finding family.

## Candidate classification

```text
candidate_status = measured_cover_candidate_pending_geometry_and_uncertainty
reference_role = potential_positive_depth_reference
reference_feature = top_of_geomembrane_above_consolidated_CCR
known_cover_nominal_m = 0.6096
actual_layer_placement_confirmed = yes
finite_depth_interval_documented = no
exact_target_geometry_available = no
coordinate_reference_system_known = yes_for_later_maps
survey_accuracy_documented = no
construction_tolerance_documented = no
stable_post_closure_interval = provisionally_supported_from_2022_through_2026
active_plant_context = yes_outside_target_area
eligible_calibration_row = no
```

## Required next steps

1. Recover and inspect the History of Construction file and the 2016 Basis of Design Report.
2. Recover any final construction as-built drawing, closure survey, or contractor quantity/quality record for the eastern cap.
3. Extract privately:
   - exact geomembrane-cap polygon;
   - coordinate system and datum;
   - final surface and geomembrane elevations;
   - measured cover thickness or accepted thickness interval;
   - project-specific survey and construction tolerances.
4. Recover the referenced annual Final Cover System Integrity Studies, especially FY2020 through FY2024.
5. Identify a stable observation interval after early settlement, provisionally beginning no earlier than the 2022 inspection period.
6. Exclude settlement instruments, piezometers, temporary wells, drainage trenches, perimeter roads, burrows, rutting, vegetation-maintenance zones, and other disturbed locations.
7. Verify exact Sentinel-1 acquisition support for the isolated cap subarea.
8. Add a private calibration row only after the uncertainty and geometry requirements pass the validator.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Strongest measured-cover lead: **John Sevier Bottom Ash Pond**
- Strongest vacant gravel-cover lead: **Auburn McMaster**
- Strongest surveyed-excavation lead: **Sconondoa Street former MGP**

## Public evidence reviewed

- TVA Bottom Ash Pond CCR document index
- Written closure and post-closure plan
- Notification of completion of closure
- Liner Design Demonstration
- FY2019 through FY2026 annual engineering inspection reports
- References to annual Final Cover System Integrity Studies
