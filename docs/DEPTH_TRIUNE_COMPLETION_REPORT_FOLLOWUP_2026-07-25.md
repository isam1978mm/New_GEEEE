# Triune Completion Report Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** completed cover confirmed; numerical depth evidence unavailable  
**Calibration rows created:** 0

## Plain-English result

Triune Mine cannot currently supply a numerical-depth calibration row.

The official Washington Department of Ecology record confirms that the Bureau of Land Management completed cleanup in 2018. About 5,500 cubic yards of tailings and waste rock were moved into an onsite consolidated waste area. That area was covered with a liner, clean soil, and vegetation. Excavated areas were also covered with clean soil as needed.

The official site index lists a December 2018 completion report classified as a remedial-action/as-built report. However, the live official document page did not expose the report during this bounded retrieval attempt, and no alternate official indexed source supplied the missing construction measurements.

The accessible public evidence does not state:

- the installed clean-soil thickness;
- mapped as-built cover elevations or thickness values;
- numerical survey accuracy or construction tolerance;
- a bounded final depth uncertainty;
- an independently confirmed no-target comparison area.

Therefore, no depth label or calibration row may be created.

## Official evidence checked

Washington Department of Ecology Cleanup Site ID `2154` identifies:

- site status: Construction Complete-Performance Monitoring;
- federal cleanup conducted by the Bureau of Land Management;
- cleanup completion in 2018;
- removal and consolidation of approximately 5,500 cubic yards of mine tailings and waste rock;
- a liner, clean-soil cover, and vegetation over the consolidated waste area;
- clean-soil restoration of excavated areas as needed;
- a 2023 Ecology and BLM inspection reporting that the consolidated waste area appeared to be functioning as intended;
- `Completion Report Triune Mine`, dated December 1, 2018, classified as a Remedial Action/As-Built Report.

## Completion-report retrieval result

The search-indexed official page lists four technical reports, including the completion report.

The live official site page returned a document count of zero during retrieval and did not provide a working completion-report link. Direct access to the underlying service also failed.

No official BLM or Ecology mirror was found that reproduced a thickness table, certified drawing, survey-control statement, or as-built elevation surface.

This is an availability failure, not proof that the original report contains no measurements. It means the required measurements are not currently supported by accessible evidence.

## Observation timing

The cleanup was completed in 2018, and a 2023 inspection found the consolidated waste area functioning as intended. This is useful stability evidence.

However, stability alone cannot create a calibration row because the numerical depth and uncertainty fields remain absent.

## Current evidence state

```text
cleanup_completed = yes
cleanup_completion_year = 2018
consolidated_waste_area = yes
liner_installed = yes
clean_soil_cover_installed = yes
vegetation_established = yes
post_construction_inspection_year = 2023
actual_measured_cover_thickness = no
mapped_as_built_thickness_surface = no
numerical_vertical_accuracy = no
final_depth_uncertainty_m = not_assigned
confirmed_no_target_comparison = no
eligible_calibration_row = no
```

## Decision

Close Triune as an unavailable evidence-only fallback.

Do not:

- assign a generic soil-cover thickness;
- infer depth from the removed waste volume;
- treat the existence of an as-built report as proof of a numerical thickness;
- assume professional construction provides an unstated accuracy value;
- create a calibration row;
- start depth training.

Reopen Triune only if the official completion report becomes accessible and contains actual mapped thickness values plus a defensible accuracy or tolerance statement.

## Current status

The six named public packages in the active screen have now been checked. None is calibration-ready.

```text
usable_triune_calibration_rows = 0
total_usable_calibration_rows = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next step

Do not restart broad generic searching.

The next evidence action should focus only on recovering one of the two strongest blocked official records:

1. Sudbury Construction Quality Assurance Certification Report `64264` with its certified as-built surface; or
2. an Elk Plain survey-control record that explicitly states vertical accuracy for the cap-surface measurements.

If neither record can be recovered through an official public route, update the main handoff to state that the current named public-document screen is exhausted and that numerical depth remains blocked pending newly released or directly obtained engineering evidence.