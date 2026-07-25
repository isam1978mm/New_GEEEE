# Elk Plain Survey Accuracy Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** mapped as-built thickness values confirmed; public numerical survey accuracy still missing  
**Calibration rows created:** 0

## Plain-English result

Elk Plain remains the strongest mapped positive-depth lead.

The official cap survey drawing contains many measured clean-fill thickness values, approximately `6.00` to `11.08 ft`, and distinguishes the surveyed contaminated-soil surface from the surveyed post-cap clean-soil surface.

However, the accessible public records still do not state a numerical vertical survey accuracy, uncertainty, closure tolerance, RMSE, equipment accuracy, or comparable bound that can be assigned to those values.

The recorded environmental covenant and legal-description map strengthen the final protected-area boundary. They do not solve the missing vertical uncertainty for the cap-thickness measurements.

Therefore, no Elk Plain calibration row may be created.

## Official records checked

### Survey of Cap Thickness Map

Washington Department of Ecology document `143487`.

The drawing identifies:

- AHBL;
- project `2180025.10`;
- drawing date May 17, 2024;
- sheet `C1.0`;
- an as-built survey of the contaminated-soil surface before capping;
- an as-built survey of the clean-soil surface after capping;
- clean-fill thickness values in feet;
- drawing status `REVIEW SET`.

The readable title block and notes do not provide:

- a vertical datum statement tied to depth uncertainty;
- survey equipment accuracy;
- a control-network accuracy;
- a closure statement;
- RMSE or confidence interval;
- a numerical vertical tolerance for the displayed thickness values.

Displayed values to hundredths of a foot are not, by themselves, proof of hundredth-foot accuracy.

### Ecology feedback on the cap map

Washington Department of Ecology document `143490`.

Ecology stated that the submitted cap survey figure appropriately addressed its request for a map documenting placed-cap thickness.

This supports regulator acceptance of the drawing's purpose and content. It does not provide or adopt a numerical measurement uncertainty.

### Pierce County Record of Survey

Record of Survey `202502055001` is documented for the capped parcel.

The Pierce County recorded-document portal and the county's official map-record index were checked. The image requires an interactive county-record session and was not recoverable through the available bounded retrieval route.

Even if recovered, the record must contain an explicit vertical-control or accuracy statement applicable to the cap-surface measurements before it can solve the uncertainty blocker. A parcel or boundary survey alone would only strengthen geometry.

### Final environmental covenant and legal-description map

The current Ecology site index lists:

- recorded environmental covenant number `202603110335`, recorded March 11, 2026;
- Property Legal Description and Map for Environmental Covenant, dated January 20, 2026;
- Site No Further Action opinion, dated March 16, 2026.

These records establish the final protected cap area and continuing restrictions, including cap maintenance and prohibition of soil disturbance.

They improve boundary confidence and long-term stability evidence. They do not state a numerical vertical uncertainty for the 2024 cap survey.

## Current evidence state

```text
actual_as_built_thickness_values = yes
mapped_cap_area = yes
regulator_acceptance_of_map_purpose = yes
recorded_protected_boundary = yes
site_no_further_action = yes
numerical_vertical_accuracy = no
final_depth_uncertainty_m = not_assigned
confirmed_no_target_comparison = no
eligible_calibration_row = no
```

## Decision

The bounded public Elk Plain survey-accuracy route is exhausted for now.

Do not:

- infer accuracy from decimal places;
- treat Ecology's map acceptance as an uncertainty certification;
- assign a generic professional-survey accuracy;
- create an approximate calibration row;
- start depth training.

Reopen this path only if a source appears that explicitly gives vertical accuracy, survey-control residuals, a certified uncertainty statement, or the underlying survey-point metadata for the cap surfaces.

## Current status

Elk Plain has real mapped depth values, but no defensible accuracy number and no confirmed comparison area.

```text
usable_elk_plain_calibration_rows = 0
total_usable_calibration_rows = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next step

Continue to the next named official package rather than repeating Elk Plain searches.

The next bounded target is Recomp drawing set `G3/G4`, followed by RAMCO cap as-built drawings, to check whether either package contains actual mapped thickness values plus a stated tolerance or survey-control bound.