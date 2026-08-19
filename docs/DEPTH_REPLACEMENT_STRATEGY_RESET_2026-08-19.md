# Numerical Depth Replacement Strategy Reset — 2026-08-19

## Decision

The project must stop expanding the generic **surface-signature -> numerical depth** feature search.

That route has now failed across multiple independent feature families under preregistered or protected tests:

- current NB numerical-depth proxy: failed raw scale, holdout, independent ordering, and surface-consistency checks;
- Sentinel-1 C-band VV/VH/ratio: failed six-plot depth-response gate;
- terrain/northness: six-plot exploratory pattern failed the independent 43-test-pit holdout effect-size gate;
- Landsat daytime thermal: failed global and seasonal depth-ordering gates;
- Sentinel-2 NDVI/NDMI: failed overall and calendar-month consistency gates;
- NISAR L-band GCOV HH/HV/HH-HV: failed the frozen seven-acquisition gate despite strong pixel support.

Across these tests, matched-depth top-surface versus outslope offsets repeatedly show that surface condition, terrain, moisture, vegetation, and/or viewing geometry can dominate the attempted signal.

**Do not rescue these routes by changing thresholds, selecting favorable dates, adding another unmotivated surface feature, changing plot geometry, or fitting a model to the six known plot answers.**

## Preferred replacement route: direct elevation difference

The preferred free/low-cost route is now a **direct physical geometry measurement**, not a learned satellite proxy.

For a cover/fill where both surfaces are known:

`depth ~= final_surface_elevation - pre_cover_or_buried_interface_elevation`

For excavation, the sign/interpretation is reversed as appropriate.

This is not a regression calibration problem. If both elevation surfaces are independently trustworthy and co-registered, the depth comes from their measured geometric separation.

### Source priority for the buried/pre-construction surface

1. Original survey/engineering surface: CAES, GPS, CAD, GIS, TIN, surveyed subgrade, or pre-cover topography.
2. Pre-construction lidar / repeat lidar, if it exists with adequate metadata and accuracy.
3. Historical stereo aerial photogrammetry / structure-from-motion DEM, but only if an independently declared accuracy gate is passed.
4. Otherwise: no numerical depth from this route.

### Source priority for the final/current surface

1. Original post-construction/as-built CAES/GPS/CAD/survey surface.
2. High-quality post-construction lidar/3DEP surface tied to a compatible datum.
3. Other surveyed surface with documented accuracy and stable-ground control.

## Why Tyrone remains the pilot

Tyrone 3X is still an excellent validation site even though the surface-signature methods failed:

- six official broad AS-BUILT plots have measured cover depths;
- 43 additional exact, independently mapped AS-BUILT test pits are available for independent validation;
- the local mine-grid to global transform is independently solved;
- the official CQA report states that CAES and conventional GPS were used for grading and that final grade was confirmed with CAES/post-cover GPS surveys.

The missing item for the direct-elevation route is therefore the **pre-cover/buried-interface elevation surface**, or an independently defensible way to reconstruct it.

## Exact next scientific gate

Run a **Tyrone pre-cover/buried-surface feasibility review only**.

Search in this order:

1. existing project/recovered EMNRD records for electronic CAES/GPS/CAD/GIS/TIN/subgrade/pre-cover survey material;
2. public pre-construction lidar if available;
3. public historical overlapping aerial photography capable of stereo/SfM reconstruction before cover construction.

Do not compute a depth raster until an accuracy/registration protocol is preregistered from the actual source metadata.

The feasibility review must explicitly determine:

- acquisition/survey date relative to cover construction;
- horizontal and vertical datum;
- native resolution / point density / survey spacing;
- stated or independently testable vertical accuracy;
- availability of stable control outside the constructed cover;
- whether final and pre surfaces can be co-registered without using the known depth answers;
- whether resulting uncertainty is small enough to resolve the depth differences of interest.

If the source cannot meet a defensible uncertainty gate, close it. Do not tune against TP1/2/3/5/6/7.

## What additional calibration sites can and cannot do

More measured sites are useful **after** a physically defensible measurement mechanism exists, for external validation and generalization.

More sites alone do not fix the current problem: repeated surface-signature failures show that adding training rows to the same insensitive/confounded predictors could simply learn site or surface differences instead of depth.

Therefore a new broad calibration-site search is not the immediate next action.

## Field fallback if no buried surface can be recovered

If no trustworthy pre/buried elevation surface exists for an AOI, a physically direct field method such as **ground-penetrating radar (GPR)** or another suitable geophysical survey becomes the realistic path. Such methods require site access and site-specific interpretation/calibration and are not a universal free satellite solution.

## Production safeguards

This strategy reset does not authorize changes to:

- the classifier;
- classifier labels, thresholds, or scores;
- the existing NB formula;
- the UI;
- SAR constraints;
- production Earth Engine logic;
- numerical-depth enablement.

NB numerical depth remains CLOSED/FAILED. Numerical app depth remains blocked until a replacement method independently passes its validation gates.

## Current next action

**Search for a Tyrone pre-cover/buried-interface elevation surface. Do not train a model and do not test another generic surface feature.**
