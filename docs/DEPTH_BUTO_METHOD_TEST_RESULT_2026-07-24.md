# Buto Sentinel-1 Method Test Result — 2026-07-24

**Branch:** `main`  
**Execution:** local user-run Earth Engine query  
**Status:** completed successfully  
**Broad source search:** stopped

## Plain-English result

The Buto method test completed successfully.

The approximate Buto anomaly area looked consistently different from the nearby comparison area on the published Sentinel-1 date, **2018-05-05**.

The same target-versus-background direction also remained stable on nearby same-orbit acquisitions.

This supports a real and repeatable **spatial radar difference** at the tested location.

It does **not** prove that Sentinel-1 measured burial depth.

## Redacted execution result

```text
query_executed = true
status = method_screen_complete_spatial_comparison_only
spatial_agreement_decision = spatial_agreement_supported
exact_date_acquisition_count = 1
usable_exact_date_acquisition_count = 1
support_acquisition_count = 36
same_orbit_support_count = 11
signal_feature_count = 4
stable_feature_count = 4
comparison_area_is_confirmed_negative = false
depth_measured = false
training_started = false
calibration_record_created = false
app_depth_enabled = false
```

## What the numbers mean

- One Sentinel-1 acquisition was found on the exact published date.
- That exact-date image had enough valid pixels for the comparison.
- Thirty-six acquisitions were available in the support window.
- Eleven nearby acquisitions from the same relative orbit were usable as a stability check.
- All four neutral signal features kept a stable target-versus-background direction.

## Important limits

The result must remain a method result only because:

- the target polygon was estimated from a published figure and is not survey-grade;
- the comparison polygon is nearby background, not a confirmed empty area;
- the current app preprocessing is not claimed to reproduce every SNAP setting in the paper exactly;
- the test checks spatial agreement, not a signal-to-depth relationship;
- this is one physical site only;
- numerical depth uncertainty is still missing.

## Allowed conclusion

```text
spatial_radar_anomaly_supported = yes
repeatable_same_orbit_direction = yes
burial_depth_measured = no
depth_calibration_record_ready = no
depth_model_training_ready = no
app_depth_output_ready = no
```

## Project effect

This result is a useful success for the research method:

- the project reproduced a stable Sentinel-1 spatial difference at the strongest published case found so far;
- Buto remains the strongest evidence source for future method work;
- the result does not unblock numerical depth estimation by itself.

The next depth-specific requirement remains independent calibration evidence with measured depth uncertainty, confirmed comparison areas, and separate physical site groups.
