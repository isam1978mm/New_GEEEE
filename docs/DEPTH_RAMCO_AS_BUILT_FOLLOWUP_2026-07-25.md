# RAMCO As-Built Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** final cover and as-built package confirmed; numerical depth evidence not recovered  
**Calibration rows created:** 0

## Plain-English result

RAMCO cannot currently supply a numerical-depth calibration row.

The official record confirms that more than 135,000 tons of waste were removed, the excavation was filled, and a final erosion-control cover was installed in September 2015. It also lists a named as-built drawing package.

However, the accessible public records do not state:

- actual measured cover thickness;
- before-and-after surface elevations;
- a mapped thickness table;
- numerical survey accuracy;
- a construction tolerance that can be assigned as final depth uncertainty.

The as-built PDF endpoint did not return a usable document during the bounded retrieval attempt, and no alternate official indexed copy supplied the missing values.

## Official records checked

Washington Department of Ecology Cleanup Site ID `3658` lists:

- RAMCO Site Cap Project As-Built Drawings, document `54685`, dated December 14, 2015;
- RAMCO Sampling Assessment and Removal Action Report;
- RAMCO Phase 1 and 2 Interim Remedial Action Report;
- RAMCO Interim Remedial Action Plan;
- environmental covenant `1117361`, recorded March 9, 2016;
- No Further Action determination issued in May 2016.

The official site description establishes:

- waste removal occurred from 2007 through 2010;
- the excavation was filled;
- the Port of Klickitat installed a final cover designed to control erosion;
- cover installation occurred in September 2015;
- the site later received a No Further Action determination.

## Drawing retrieval result

The as-built package is clearly identified as an official remedial-action/as-built report, but the document endpoint returned a cache/fetch error.

Searches of the official indexed records found no extracted text giving a cover-depth value or numerical survey-control statement.

Therefore, the named package remains a document lead, not usable calibration evidence.

## Current evidence state

```text
completed_final_cover = yes
cover_installation_date = 2015_09
named_as_built_package = yes
actual_measured_cover_thickness = no
mapped_thickness_surface = no
numerical_vertical_accuracy = no
confirmed_no_target_comparison = no
eligible_calibration_row = no
```

## Decision

Retain RAMCO only as an unresolved alternate.

Do not:

- invent a cover thickness from the phrase `final cover`;
- treat erosion-control purpose as a numerical depth specification;
- infer survey accuracy from the existence of as-built drawings;
- create a calibration row;
- start depth training.

Reopen RAMCO only if document `54685` becomes readable or another official source reproduces its measured elevations, thickness values, and survey-control notes.

## Current status

RAMCO proves that a cover was completed, but it does not provide a usable depth number with uncertainty.

```text
usable_ramco_calibration_rows = 0
total_usable_calibration_rows = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next step

Inspect the Triune Mine completion/as-built report, the last named fallback in the current bounded screen, for actual cover-thickness values, numerical uncertainty, confirmed comparison evidence, and stable Sentinel-1 timing.