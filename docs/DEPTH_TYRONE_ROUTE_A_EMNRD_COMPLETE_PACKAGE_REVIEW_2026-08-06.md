# Tyrone Route A — Complete EMNRD Package Review

Date: 2026-08-06

## Decision

Route A is **partially supported but numerical depth remains blocked**.

The complete EMNRD delivery materially improves the Tyrone Test Plot 5 and Test Plot 6 evidence. It provides:

- independent M3 as-built average cover depths derived from surveyed area and placed-cover volume;
- as-built plot areas and footprint drawings;
- a local mine-site coordinate grid;
- preliminary plot dimensions large enough to contain clean 30–40 m radar review areas after exclusions; and
- construction, instrumentation, vegetation, drainage, and repair information needed to define exclusion zones.

The package does **not** provide an external coordinate reference system, local-to-global survey control, CAD/GIS/GPS point files, or the referenced September 29, 2006 Golder as-built test-plot report. Therefore exact defensible latitude/longitude polygons for Test Plots 5 and 6 cannot yet be produced under the existing georeference quality gates.

```text
route_a_status                 = partially_supported_still_blocked
measured_depth_supported       = true
as_built_plot_geometry_found   = true
external_crs_resolved          = false
exact_global_polygons_ready    = false
records_research_ready         = false
numerical_depth_unlocked       = false
```

## Package inspected

The supplied `all.7z` package contained 73 archive entries, approximately 192 MB after extraction. The review included:

- `20031215_Test_Plot_Work_Plan.pdf`;
- `Dam_3X_CQAR__Const_Sept_2004_to_Dec_2005__July_2008.pdf`;
- `3X_CQAR_000_R0.pdf` through `3X_CQAR_016_R0.pdf`, including combined sheets 006/007 and 008/009;
- preliminary drawings `40-2-101_P2.pdf`, `40-2-102_P2.pdf`, and `40-2-103_P2.pdf`;
- annual summaries for 2010 through 2013;
- 22 construction photograph sheets;
- meteorological and vadose-zone spreadsheets; and
- supporting QA, gradation, index, and instrumentation files.

Duplicate filenames were preserved during inspection. The duplicate photo log and one duplicate meteorological workbook were byte-identical; the other numbered meteorological workbooks were distinct time-series files.

## Test Plot 5 depth

### Previously established official pit measurements

The previously recovered official five-pit values are:

```text
28, 26, 26, 28, 26 inches
mean = 26.8 inches = 0.68072 m
95% interval carried by the project = 0.65532–0.70612 m
```

These are post-placement physical pit-face measurements, not design depth.

### M3 as-built volume/area average

Drawing `3X_CQAR_012_R0.pdf`, titled `Tailing Dam #3X — Volumes & Cover Depths`, reports:

```text
as-built area             = 4.1 acres
placed cover volume       = 15,038 cubic yards
reported average depth    = 2.3 feet
calculated volume/area    = 2.2734 feet
                          = 27.281 inches
                          = 0.69294 m
```

The volume/area average agrees closely with the five-pit mean of 26.8 inches.

## Test Plot 6 depth

### Previously established official pit measurements

The previously recovered official five-pit values are:

```text
40, 35, 42, 36, 34 inches
mean = 37.4 inches = 0.94996 m
95% interval carried by the project = 0.85090–1.04902 m
```

These are post-placement physical pit-face measurements, not design depth.

### M3 as-built volume/area average

Drawing `3X_CQAR_012_R0.pdf` reports:

```text
as-built area             = 4.5 acres
placed cover volume       = 20,315 cubic yards
reported average depth    = 2.8 feet
calculated volume/area    = 2.7982 feet
                          = 33.579 inches
                          = 0.85289 m
```

The M3 volume-average depth is lower than the five-pit mean, but approximately coincides with the lower end of the project’s pit-based interval. This must be treated as real spatial and/or method variability. The project must not silently select one TP6 target without documenting the measurement method.

## Measurement methods and timing

The 2003 work plan requires five random-grid excavations in each test plot after cover placement and before seeding. It states that the construction report must include actual cover-thickness data from those five excavations, along with as-built diagrams, plot location, plot number, size, and maps or tabulated thickness results.

The 2008 Dam 3X CQA report states that:

- final grading used GPS and the Computer Aided Earthmoving System (CAES);
- cover thickness was evaluated by comparing GPS readings with CAES design files;
- physical test pits were used to confirm GPS-indicated cover depth;
- insufficient-cover areas were corrected and reverified;
- post-cover GPS surveys are shown on Drawings 3X CQAR-006/007; and
- average cover depths are shown on Drawing 3X CQAR-012.

The archive does not provide exact excavation dates or the full five-pit location table for Test Plots 5 and 6.

## Plot locations and coordinate system

### What was found

As-built drawings `3X_CQAR_006_007_R0.pdf` and `3X_CQAR_010_R0.pdf` show the Test Plot 5 and Test Plot 6 polygons on a labeled local coordinate grid.

Drawing `3X_CQAR_001_R0.pdf` identifies the grid as:

```text
MINE SITE COORDINATES
```

The work plan states that as-built surveying could use GPS calibrated to the local mine-site GPS network using mine-site coordinates.

### What was not found

The package contains no defensible external reference for that grid:

- no EPSG code;
- no NAD27/NAD83/WGS84 statement;
- no UTM or State Plane zone;
- no benchmark/control-point table;
- no local-to-global transformation;
- no survey-point coordinate export;
- no CAD, GIS, GPS, or CAES design/survey file; and
- no independent control points suitable for verification.

Therefore the as-built footprint drawings cannot yet be converted into accepted global polygons under the project’s required gate:

```text
minimum fit controls       = 6
independent check controls = 2
maximum RMSE               = 5 m
maximum residual           = 7.5 m
```

## Plot dimensions and usable radar area

Preliminary drawing `40-2-103_P2.pdf` shows:

```text
Test Plot 5 longitudinal limit = 550 ft
Test Plot 5 cross-section      = 470 ft plus a 50 ft fertilizer-treatment area

Test Plot 6 longitudinal limit = 559 ft
Test Plot 6 cross-section      = 567 ft plus a 50 ft fertilizer-treatment area
```

These are design dimensions rather than final surveyed boundary dimensions, but the as-built areas of 4.1 and 4.5 acres confirm that both plots are large enough in principle to contain clean regions at least 30–40 m wide.

Usable radar polygons must exclude:

- the 50 ft fertilizer-treatment strips;
- instrumentation nests and neutron access tubes;
- lysimeters and their disturbed surroundings;
- erosion transects;
- the meteorological station and associated cables where applicable;
- berms, drains, plot edges, and road-adjacent areas; and
- repaired lysimeter depressions and subsidence/crack zones.

## Surface comparability

The plots were built as related top-surface cover treatments, but they are not perfectly interchangeable radar surfaces.

The 2010–2013 annual reports document differences and changes in:

- rock cover;
- bare-ground fraction;
- canopy and litter cover;
- vegetation establishment;
- ponding and localized subsidence; and
- rehabilitation around lysimeter areas.

The 2013 report describes depressions and subsidence cracks over top-surface lysimeters, with ponding especially associated with the Test Plot 6 three-foot lysimeter and evidence also at Test Plot 5. Those areas were rehabilitated in April 2008 by removing cover, adding tailings, replacing cover, reseeding, mulching, and reinstalling instruments.

A fair radar comparison therefore requires clean interior polygons, a stable post-repair interval, and explicit surface-similarity screening.

## Missing authoritative record

The Dam 3X CQA report explicitly references:

```text
As-Built Report Cover, Erosion, and Revegetation Test Plot Study —
Tailing Test Plots
Golder Associates
September 29, 2006
```

That report is not present in the 73-entry EMNRD package.

It is the most likely missing source for:

- exact Test Plot 5 and Test Plot 6 five-pit values in their original table;
- pit locations or random-grid identifiers;
- measurement dates;
- test-plot-specific construction records;
- plot-specific as-built diagrams; and
- references to native survey/CAD/GPS files.

## Exact Route A decision

### Supported

- official measured/as-built depth evidence exists for both plots;
- two independent depth methods are available: physical pits and GPS/CAES-derived volume/area averages;
- as-built plot areas and local-grid footprints exist;
- the plots are large enough for potential Sentinel-1 analysis after exclusions; and
- infrastructure, repairs, and surface confounders are documented sufficiently to define a future exclusion plan.

### Still blocked

- no external coordinate reference system or local-to-global survey control;
- no accepted latitude/longitude polygons;
- missing September 29, 2006 Golder as-built test-plot report;
- no native CAD/GIS/GPS/CAES survey files;
- no exact pit-location table in the delivered package;
- Test Plot 6 contains material method/spatial depth variability; and
- no stable, cleaned, plot-specific Sentinel-1 calibration interval has yet been approved.

## Current project status

```text
Tyrone Route A evidence recovery = complete for supplied EMNRD package
Route A result                    = partially supported / still blocked
Test Plot 5 numerical depth       = officially supported, geometry unresolved
Test Plot 6 numerical depth       = officially supported with variability, geometry unresolved
usable global calibration rows    = 0
numerical depth ready             = no
app numerical depth unlocked      = no
Campaign 008                      = not approved
```

## Next permitted action

Do not start Campaign 008 and do not change the classifier, frontend, Option 5, or production depth behavior.

The remaining Tyrone action is limited to determining whether the existing EMNRD response includes or can supply, within the same request record:

1. the September 29, 2006 Golder as-built test-plot report;
2. native CAD/GIS/GPS/CAES survey data for Drawings 3X CQAR-006/007 and 010;
3. survey-control or benchmark data that converts mine-site coordinates to an external CRS; and
4. the exact five-pit location and measurement table for Test Plots 5 and 6.

No new records request or outreach is authorized by this review.