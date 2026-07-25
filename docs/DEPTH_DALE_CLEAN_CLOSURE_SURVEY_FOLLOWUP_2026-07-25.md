# Dale Clean-Closure Survey Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** strong regulator-confirmed removal evidence; exact public survey and clean observation timing unavailable  
**Calibration rows created:** 0

## Plain-English result

Kentucky's William C. Dale Station is one of the strongest physical clean-closure examples found in the public record.

The United States Environmental Protection Agency's April 13, 2026 proposed CCR rule states that Kentucky's Division of Waste Management oversaw closure by removal of three legacy impoundments at Dale between 2014 and 2019. The state approved the closure plan, performed at least 16 onsite inspections, and conducted three inspections that verified clean closure down to native soils. EPA reports more than 350 hours of state oversight.

This is strong independent confirmation that the pond areas were cleared of ash. It is not enough for a calibration row because the exact final surveyed boundaries, final surface survey, and post-closure surface history were not recovered.

## Official records checked

- EPA proposed rule published April 13, 2026, discussing the Kentucky-supervised Dale closures.
- Kentucky Public Service Commission Case `2014-00252`, approving construction of the Smith landfill to receive Dale ash and reclamation of the Dale pond site.
- Kentucky Department for Environmental Protection eSearch Agency Interest `809`, East KY Power Coop — Dale Station.
- East Kentucky Power Cooperative CCR index and separate legacy-unit folders for Ash Ponds 2, 3, and 4.

## Evidence established

```text
physical_ash_removal = confirmed
removal_to_native_soil = confirmed
state_approved_closure_plan = yes
state_onsite_inspections = at_least_16
clean_closure_inspections = 3
state_oversight_hours = more_than_350
closure_period = 2014_to_2019
```

## Missing evidence

The public Kentucky agency page does not expose a downloadable solid-waste closure activity for Agency Interest `809`.

The three EKPC legacy pond document folders were identified, but their internal pages and files could not be recovered through the accessible public interfaces or normal indexing.

The following remain missing:

- exact final survey polygon for each removed pond;
- survey coordinate system and boundary accuracy;
- final grading or as-built surface drawing;
- confirmation that the pond footprints remained dry, unused, and materially unchanged during a suitable Sentinel-1 period;
- a defensible geometry file tied directly to the state-confirmed clean-closure inspections.

The station's broader demolition and remaining electrical infrastructure mean that site-wide stability cannot be assumed. A pond-specific post-closure review would still be required even if geometry were recovered.

## Current classification

```text
reference_status = confirmed_removal_to_native_soil_pending_exact_geometry_and_timing
physical_confirmation = strong
exact_private_geometry_extracted = no
post_closure_surface_stability_verified = no
eligible_negative_calibration_row = no
```

## Decision

Dale remains strong evidence that state-supervised closure by removal can provide a true empty-area reference. It cannot become a calibration row from the currently accessible public records.

Do not draw an analyst-estimated polygon from aerial imagery. Do not treat the former dam or general station boundary as the three final excavated pond boundaries.

## Next bounded action

Move to Georgia's Kraft plant removal case because EPA states that Georgia approved the final soil and groundwater condition as protective in 2021. Search specifically for the state Response and Remediation Program completion report, exact ash-pond survey, and post-removal land-use record.

Do not create a calibration row, start training, or enable numerical depth.