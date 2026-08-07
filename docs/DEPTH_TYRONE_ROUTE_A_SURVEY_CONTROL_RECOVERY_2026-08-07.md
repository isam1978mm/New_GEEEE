# Tyrone Route A — Survey-Control Recovery

Date: 2026-08-07

## Controlling conclusion

Tyrone Route A remains the shortest credible route to numerical-depth calibration.

The measured as-built depth evidence for Test Plots 5 and 6 and the local plot footprints remain supported. The unresolved blocker is still the transformation of the local station/offset construction geometry into a global coordinate system suitable for Sentinel-1 acquisition and calibration.

This search found a materially stronger official lead: the missing global survey control was not merely hypothetical. Official Tyrone records state that conventional GPS and CAES grade-control surveys were used during 3X construction, and the later closure plan identifies the specific Construction Quality Assurance Report for the 3X reclamation.

Numerical depth remains blocked until numeric survey control is recovered and independently validated.

## Official evidence recovered

### 1. GPS / CAES control existed during 3X construction

The official 3X Tailing As-Built report states that CAES (Computer Aided Earth Moving System) and conventional GPS surveys were used for grade control. It also states that lysimeter locations were surveyed with GPS equipment before construction.

This is important because it establishes that survey-grade or machine-control spatial data existed for the same construction program that contains Test Plots 5 and 6.

### 2. Exact missing CQA report identified

Later official Tyrone Closure/Closeout Plan references identify:

```text
M3, 2008a.
Construction Quality Assurance Report: Tailing Impoundment 3X Reclamation [Draft].
Prepared for Freeport McMoRan Copper and Gold, Tyrone Operations.
June 2008.
```

The closure plan states that the 3X facility CQAR was submitted to the agencies in August 2008.

This is the highest-priority missing record because the earlier 3X as-built report explicitly deferred final construction details to the 3X Construction Quality Assurance documentation.

## Official sources

- EMNRD Tyrone Revision 09-1 public-record page:
  https://www.emnrd.nm.gov/mmd/mining-act-reclamation-program/pending-and-approved-mine-applications/mining-applications-regular-existing/gr010retyrone-mine-revision-09-1/
- Official 2013 Tyrone Closure/Closeout Plan Update, which gives the full M3 2008a citation:
  https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/2013-07-15_TyroneCCPUpdate_GR010RE.pdf
- Official 2019 Tyrone Closure/Closeout Plan Update, which states the 3X CQAR was submitted in August 2008:
  https://www.emnrd.nm.gov/mmd/wp-content/uploads/sites/5/2019-07-30_Tyrone_CCP_Update.pdf
- Official public 3X Tailing As-Built report is linked from the EMNRD Tyrone Revision 09-1 page as `3X Tailing As-Built`.

## What was not recovered

The current public/indexed search did **not** recover a numeric global control table for Test Plots 5 and 6, a benchmark/control-point schedule, or the native CAES/GPS survey deliverables.

Do not infer coordinates from an approximate map, broad mine polygon, satellite image, or visual alignment.

## Exact records now required

The next records-recovery action is narrowly limited to the 3X Tailing Impoundment reclamation survey/control package. Request the following, preferably in native electronic form when retained:

1. `M3, 2008a — Construction Quality Assurance Report: Tailing Impoundment 3X Reclamation [Draft], June 2008`, including every appendix, plate, drawing, table, exhibit, survey sheet, photograph index, and electronic attachment.
2. Any final or revised version of that report submitted in or around August 2008.
3. Survey control used for 3X reclamation construction and as-built verification, including benchmarks, monuments, control points, northing/easting or latitude/longitude, coordinate-system name, datum, units, and survey date.
4. Conventional GPS survey files used for 3X grade control or lysimeter/test-plot location control.
5. CAES / machine-control files, surfaces, point files, linework, or exports used for 3X grade control.
6. Native CAD/Civil/AutoCAD files or survey exports underlying Plate 1 and any 3X as-built drawings, including DWG, DXF, LandXML/XML, CSV/TXT point files, SHP/GeoJSON, or equivalent formats if retained.
7. Any surveyor certification, control report, coordinate transformation, basis-of-bearing statement, or project coordinate-system definition associated with the 3X reclamation.
8. Any table or electronic file giving the surveyed location of the six lysimeters or the boundaries/corners of Test Plots 5 and 6.

## Acceptance gate

Route A can move to coordinate transformation only if the recovered material provides at least one defensible tie between the local plot geometry and a global/survey coordinate system.

Preferred evidence is two or more non-collinear common points or surveyed plot corners. A single surveyed point can be useful only if the local grid orientation/scale and coordinate-system definition are independently fixed by the same official survey package.

Required metadata:

```text
coordinate values
coordinate system / CRS
datum
units
survey/control-point identity
survey date or report context
relationship to the local 3X plot geometry
```

## What happens after control is recovered

1. Transform the local TP5/TP6 footprints into the stated global CRS.
2. Validate the transform against all available independent survey points/control.
3. Reject the route if residuals are too large for the intended Sentinel-1 comparison.
4. Create globally located calibration rows only after the transform passes QA.
5. Run the existing local acquisition / radar comparability gates without weakening thresholds.

## Current status

```text
TP5 measured depth evidence:          supported
TP6 measured depth evidence:          supported
Local TP5/TP6 footprint geometry:     supported
GPS/CAES survey existence:            supported by official records
Exact 3X CQAR identity:               recovered
Numeric global survey control:        not yet recovered
Usable calibration rows:              0
Numerical depth unlocked:             false
```

## Decision

Do not start Campaign 010 yet.

Route A now has a specific, evidence-backed recovery target: the June 2008 M3 3X CQAR and its native GPS/CAES/CAD survey-control attachments. Exhaust this targeted record before opening another broad discovery campaign.
