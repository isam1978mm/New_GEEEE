# Cross Gypsum Pond Active-Site Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** confirmed closure by removal, but exact final survey geometry and stable unchanged observation period are not available  
**Calibration rows created:** 0

## Plain-English result

Cross Generating Station's former Gypsum Pond was genuinely closed by removal. Santee Cooper states that all CCR material and CCR-contact soil were removed under a South Carolina regulator-approved closure plan, and closure was formally certified in March 2017.

This does not create a usable confirmed-negative calibration row.

The decisive problem is surface stability. Santee Cooper's own groundwater report describes the closed Gypsum Pond as being in a highly congested and active part of the generating station with multiple simultaneous ongoing operations. A groundwater monitoring system was later developed around the closed pond, and corrective-action work remains active through at least May 2026.

The former pond footprint therefore cannot be assumed to have remained dry, unused, and materially unchanged during a clean Sentinel-1 observation period.

## Evidence established

```text
physical_CCR_removal = confirmed
all_CCR_removed_by = 2016-10-17
formal_state_closure_certification = 2017-03-22
public_site_summary_closure_date = 2017-03-11
closure_method = removal_of_CCR_and_CCR_contact_soil
post_closure_groundwater_program = active
active_station_operations_near_footprint = confirmed
clean_unchanged_radar_period = not_confirmed
```

The one-day difference between the public site summary and formal state certification reflects different milestones in the closure record. It does not affect the eligibility decision.

## Geometry and survey review

The public Cross CCR page lists:

- a written closure plan;
- a qualified-professional-engineer certification;
- completion of closure by removal; and
- regulator approval that closure is complete.

However, the publicly indexed material reviewed did not expose a directly readable final as-built or post-excavation survey plat with:

- an exact pond polygon;
- coordinate values or a usable georeferenced boundary;
- permanent survey control or benchmarks; and
- numerical horizontal boundary uncertainty.

Therefore:

```text
exact_final_empty_polygon = no
survey_grade_geometry_extracted = no
boundary_position_uncertainty = no
analyst_drawn_geometry_allowed = no
```

## Surface-stability blocker

The 2021 groundwater report states that the closed Gypsum Pond is in a highly congested and active generating-station area with multiple simultaneous ongoing operations.

Later public records list:

- annual groundwater monitoring reports through 2025;
- remedy-selection progress reports through May 2026; and
- no final notification that the remedy is complete.

Monitoring wells or related groundwater work do not automatically prove that every square metre of the former pond was disturbed. They do prove that the site is operationally active and that an unchanged surface cannot be assumed without a pond-specific construction and maintenance history.

## Current classification

```text
reference_status = confirmed_removal_but_active_site_and_geometry_incomplete
physical_confirmation = strong
exact_private_geometry_extracted = no
survey_accuracy_assigned = no
clean_observation_timing_verified = no
eligible_negative_calibration_row = no
```

## Decision

Cross Gypsum Pond is not a usable negative calibration site.

It fails two independent requirements:

1. no directly readable exact final removal polygon with numerical survey uncertainty was recovered; and
2. the footprint lies in an active, congested generating-station area with continuing groundwater monitoring and corrective-action work.

Do not create a calibration row from an aerial estimate, general facility boundary, groundwater well network, or an approximate pond outline.

## Current readiness

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
calibration_records_created = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Stop searching active generating stations for empty controls unless a record explicitly proves a protected, unused, unchanged pond footprint.

Continue with an older completed removal site whose final post-excavation survey is directly readable and whose former unit became a simple grassed or bare area without redevelopment, monitoring construction, landfill conversion, wetland conversion, or industrial reuse.
