# J.R. Whiting Measured Cover Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** strongest mapped positive-depth evidence found; uncertainty, confirmed negative, and clean timing still incomplete  
**Purpose:** record the bounded evidence recovered from the public J.R. Whiting Ponds 1 and 2 closure package

## Plain-English result

The J.R. Whiting Ponds 1 and 2 closure package is the strongest positive-depth calibration lead found so far.

Unlike design-only closure packages, its final construction record contains a mapped table of actual surveyed subgrade and final-topsoil elevations. The difference between those two surveyed elevations is reported as final cover thickness at each construction control point.

The record table covers control points `1000` through `1106`, for 107 mapped measured depth points. The recovered values range from `2.03 ft` to `2.50 ft`, or approximately `0.6187 m` to `0.7620 m`.

This is a major evidence improvement. It is still not enough to create a calibration row because the public package does not state the vertical measurement accuracy of the construction record survey, no independently confirmed no-target comparison footprint has been established, and a clean Sentinel-1 observation period has not been verified.

## Official source package

Consumers Energy's public CCR compliance archive lists:

- the six-part Ponds 1 and 2 Final Construction Documentation Report;
- the six-part closure notification attachments;
- the closure plan;
- the post-closure plan;
- annual groundwater and inspection records.

The official final construction report and record drawings were prepared for the J.R. Whiting Ponds 1 and 2 closure. Coordinate-bearing geometry must remain outside Git.

The public PDF server could not be opened through the normal document reader during this pass. The facts below were recovered from the indexed text of the official Consumers Energy PDF files. The underlying official record drawings should still be visually verified before private geometry extraction or calibration-row creation.

## Completed cover system

The construction record supports the completed final cover as:

- `18 inches` of protective cover soil;
- `6 inches` of topsoil;
- total required final soil cover of `24 inches` (`2.00 ft`, `0.6096 m`).

The report records:

- closure work beginning in 2019;
- protective-cover and topsoil work substantially complete in November 2019;
- the topsoil survey completed on November 21, 2019;
- final construction certification and record drawings issued in 2020;
- an approximately 18.3-acre certified cover area.

## Actual mapped measured depths

The record drawing's Table 1 is titled as the J.R. Whiting Ponds 1 and 2 record construction control-point table.

For each mapped point it reports:

- the subgrade control-point number;
- the record subgrade elevation from survey;
- the corresponding final-cover control-point number;
- the record topsoil elevation from survey;
- final cover thickness calculated from the two surveyed elevations.

The final-cover control-point sequence runs from `2000` through `2106`, corresponding to subgrade control points `1000` through `1106`.

Recovered table extent:

```text
mapped_measured_depth_point_count = 107
minimum_recovered_final_cover_thickness_ft = 2.03
maximum_recovered_final_cover_thickness_ft = 2.50
minimum_recovered_final_cover_thickness_m = 0.618744
maximum_recovered_final_cover_thickness_m = 0.762
required_minimum_final_cover_thickness_m = 0.6096
```

Examples from the official table include thicknesses of:

```text
2.03, 2.04, 2.05, 2.06, 2.07, 2.08, 2.09, 2.10,
2.12, 2.14, 2.16, 2.20, 2.25, 2.31, 2.35, 2.39, and 2.50 ft
```

The record drawing states that the construction record survey was completed by ROWE as needed between August 9 and November 21, 2019.

## Survey and construction control evidence

The public package establishes:

- a licensed land surveyor;
- a 100-foot construction-control grid;
- repeat surveys of the subgrade and final topsoil at corresponding control points;
- elevations tied to NGVD29;
- GPS-controlled earthwork placement;
- field probing and continuous construction-quality observation;
- a final-cover construction tolerance above design;
- record drawings issued for the completed closure.

The construction plan used a top-of-protective-cover tolerance of approximately `+0.2 ft to 0.0 ft`. This is a construction acceptance control. It is not automatically the vertical measurement uncertainty of the survey.

The package also contains equipment calibration records for other construction-quality tests, but no source-supported numerical vertical accuracy for the ROWE construction record survey was found.

## Evidence that cannot yet be claimed

Do not claim any of the following yet:

- that displayed hundredth-foot precision equals survey accuracy;
- that the `+0.2 ft to 0.0 ft` grade tolerance equals final depth uncertainty;
- that every eastern-edge location was surveyed, because the record drawing notes that some riprap-covered edge points were not surveyed;
- that a nearby uncapped area is confirmed free of CCR;
- that the cap was unchanged during a particular Sentinel-1 period;
- that the 107 points are independent site groups.

## Current classification

```text
reference_status = mapped_measured_positive_depth_pending_uncertainty_negative_and_timing
actual_as_built_depth_values = yes
mapped_measured_depth_point_count = 107
measured_depth_range_m = 0.618744_to_0.762
licensed_construction_record_survey = yes
survey_grid_spacing_ft = 100
survey_vertical_datum = NGVD29
final_depth_uncertainty_m = not_assigned
confirmed_no_target_geometry = no
clean_sentinel1_window_verified = no
eligible_calibration_row = no
```

## Decision

J.R. Whiting is now the strongest public positive-depth lead in the project.

It is substantially stronger than Elk Plain because the official final record drawing reports both surveyed surfaces and calculated final cover thicknesses at a regular mapped grid. It is stronger than Sudbury because the actual per-point thickness values have been recovered rather than only a checked minimum.

Do not create calibration rows yet.

## Next bounded action

Continue only with:

1. a survey-control note, ROWE certification, equipment statement, or other source-supported vertical-accuracy bound for the construction record survey;
2. official J.R. Whiting records for a physically confirmed CCR-free or cleared comparison footprint;
3. post-closure inspection records showing whether the Ponds 1 and 2 cap remained unchanged after August 2020;
4. visual verification of the official record-drawing table before extracting private geometry;
5. separate independent complete site groups for validation and holdout.

Current project readiness remains:

```text
usable_calibration_rows = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```
