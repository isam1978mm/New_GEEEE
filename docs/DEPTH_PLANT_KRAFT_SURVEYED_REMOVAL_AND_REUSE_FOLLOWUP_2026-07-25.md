# Plant Kraft Surveyed Removal and Reuse Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** confirmed CCR removal with a coordinate-bearing survey package; exact AP-1 geometry extraction and clean observation timing incomplete  
**Calibration rows created:** 0

## Plain-English result

Plant Kraft AP-1 is the strongest public empty-area geometry lead found in the current closure-by-removal search.

The official Georgia Power package includes a post-excavation topographic map, an excavation-limit drawing, and a top-of-structural-fill topographic map. The drawing identifies the coordinate system as Georgia East Zone, NAD83, and was prepared by a firm identified as consulting engineers and land surveyors.

This is materially stronger than the approximate work-plan boundaries found at J.C. Weadock, J.H. Campbell, Bremo Bluff, Possum Point, and other removal sites.

The route is still not calibration-ready. The accessible PDF text confirms that the coordinate-bearing maps exist, but the map pages could not be rendered or downloaded reliably enough to extract the AP-1 polygon. The recorded environmental covenants and county parcel records describe broader property tracts and cannot be substituted for the separate AP-1 excavation-limit line.

## Official sources checked

- Georgia Power Plant Kraft CCR and Voluntary Remediation Program document index.
- Certification of CCR Removal, including the original layout and post-removal engineering figures.
- Recorded Environmental Covenants 1, 2, and 3.
- Georgia EPD Voluntary Remediation Program records and approval letters.
- Georgia Hazardous Site Inventory, site `10415`.
- Chatham County/SAGIS parcel services and parcel records for the Plant Kraft property.
- Public records concerning plant retirement, demolition, property transfer, and port reuse.

## Removal and map evidence established

The official removal certification package contains figures identified as:

```text
PLANT KRAFT AP-1 POST EXCAVATION TOPOGRAPHIC MAP
EXCAVATION LIMITS
TOPOGRAPHIC MAP - TOP OF STRUCTURAL FILL
```

The engineering drawing text identifies:

```text
coordinate_system = Georgia East Zone
horizontal_datum = NAD83
engineering_survey_firm = KEM & Co.
map_type = post_excavation_topography_and_excavation_limits
```

The broader public record supports:

```text
physical_CCR_removal = confirmed
removal_complete_by = March 2018 or earlier
state_remediation_review = yes
soil_compliance_approved = yes
coordinate_bearing_final_map_exists = yes
exact_private_AP1_polygon_extracted = no
```

## Why parcel and covenant geometry cannot replace the AP-1 drawing

The Georgia Hazardous Site Inventory and recorded covenants identify larger Plant Kraft property tracts, including parcels associated with HSI site `10415`.

The publicly indexed main parcel is approximately 40.7 acres and is now owned by the Georgia Ports Authority. The covenant set applies to property tracts affected by the wider remediation program.

None of the accessible parcel or covenant records states that its external property boundary is identical to the AP-1 post-excavation limit. The removal certification instead refers to a distinct excavation-limit line inside the engineering map.

Therefore:

```text
county_parcel_boundary_can_be_used_as_AP1_boundary = no
covenant_tract_can_be_used_as_AP1_boundary_without_map_comparison = no
analyst_drawn_boundary_allowed = no
```

Using the parcel boundary would include land outside the former ash pond and would create a false confirmed-empty record.

## PDF access limitation

The official PDFs open in the web document index, but screenshots of the coordinate-bearing map pages repeatedly failed with a cache error. Direct file downloads also failed.

Only parsed document text was used. No visual coordinate extraction was claimed or performed.

This means the existence and type of the survey drawings are confirmed, but the polygon cannot yet be digitized honestly.

## Observation-timing review

The public record establishes:

- Plant Kraft retired in 2015;
- demolition, backfill, grading, and seeding work continued through approximately June 2017;
- Georgia Power states that Kraft ash-pond removal was complete by March 2018;
- the property was donated to the Georgia Ports Authority in 2021 for future port use.

A possible quieter period may have existed after final removal and before the 2021 transfer, but no source was found that confirms the AP-1 footprint remained materially unchanged throughout that period.

The exact dates for final structural-fill grading, vegetation establishment, maintenance, or port-related work inside AP-1 remain unresolved.

Therefore:

```text
possible_2018_to_2020_quiet_window = unverified
clean_sentinel1_window = no
post_removal_surface_stability = not_confirmed
```

## Survey uncertainty

The parsed map text identifies the coordinate system and survey/engineering firm, but no explicit numerical horizontal or vertical survey accuracy was found.

For a confirmed-negative row, the central geometry requirement remains the exact physical boundary tied to removal verification. A defensible boundary-position uncertainty would still need to be assigned from the final drawing, survey notes, or a governing project specification.

## Current classification

```text
reference_status = confirmed_removal_with_survey_grade_map_pending_geometry_extraction_and_timing
physical_confirmation = strong
coordinate_bearing_excavation_map_exists = yes
exact_private_geometry_extracted = no
survey_accuracy_assigned = no
clean_observation_timing_verified = no
eligible_negative_calibration_row = no
```

## Decision

Plant Kraft remains the strongest geometry-pending confirmed-empty lead.

It cannot become a calibration row until:

1. the AP-1 excavation-limit map is rendered or obtained in a readable form;
2. the exact boundary is extracted into a private geometry file;
3. the drawing is tied to the final confirmed-removal condition;
4. a boundary-position uncertainty is supported;
5. a clean, unchanged Sentinel-1 observation period is verified.

Do not use the county parcel, HSI point, environmental-covenant tract, or an aerial-image estimate as a substitute for the AP-1 excavation limit.

## Current readiness

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
calibration_records_created = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Continue only with completed removal sites whose final as-built or post-excavation survey drawings are directly readable and whose cleared surfaces remained dry and unused.

Retain Plant Kraft as the first recovery target if a readable copy of the Certification of CCR Removal maps becomes accessible. Do not repeat parcel or covenant searches unless a record explicitly states that a tract boundary is identical to the AP-1 excavation limit.