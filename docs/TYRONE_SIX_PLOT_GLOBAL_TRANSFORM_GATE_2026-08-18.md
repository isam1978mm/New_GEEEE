# Tyrone 3X Six-Plot Global Transform Gate — 2026-08-18

## Decision

The Tyrone six-plot reference dataset is valid as an official-drawing/local-mine-grid reference, but the project does **not** yet have an independently verified Tyrone local-mine-grid → global/raster transform suitable for authoritative 10 m satellite-pixel extraction.

Therefore:

- numerical app depth remains blocked;
- the current NB numerical-depth route remains closed/failed validation;
- the six-plot reference remains usable for measured depths, local geometry, surface grouping, and provenance;
- raw six-plot sensor extraction must remain gated until the global transform is independently verified;
- the old July visual/image-fit UTM placements must not be promoted to authoritative geometry.

No classifier, UI, NB formula, SAR constraint, or production runtime code is changed by this decision.

## What is now independently established

### Official six-plot geometry and measurements

The recovered June 2008 Tyrone 3X Construction Quality Assurance / as-built package independently confirms the six test plots and their configuration. The recovered figures/plates show TP1, TP2, TP3, TP5, TP6, and TP7 on the Dam 3X surface.

The recovered original plate reports approximately:

| Plot | Nominal cover | Plate area |
|---|---:|---:|
| TP1 | 2 ft | 4.93 ac |
| TP2 | 3 ft | 5.40 ac |
| TP3 | 4 ft | 4.70 ac |
| TP5 | 2 ft | 4.06 ac |
| TP6 | 3 ft | 4.50 ac |
| TP7 | 4 ft | 2.25 ac |

These are consistent with the simplified acreages printed on `3X_CQAR_010_R0.pdf` and with the existing measured-depth reference table.

### Surveying really occurred

The recovered CQA report states that CAES personnel performed layout/staking and cover-thickness verification work, and that final grade was verified by post-cover GPS surveys. This establishes that survey-grade source data existed during construction.

### Local mine grid is real

`3X_CQAR_010_R0.pdf` uses a Tyrone local W/E–N drawing grid in feet. Other official Tyrone records also use local Northing/Easting values in feet. The project may therefore preserve the six plot polygons in this local grid without pretending those coordinates are WGS84/UTM.

## What was searched and not found

The transform search checked:

1. current project Sources;
2. current `main` repository files;
3. historical Tyrone PRs and branches;
4. the July provisional georeferencing implementation;
5. later August depth/validation branches;
6. the recovered official 3X CQA/as-built evidence package;
7. exact standalone drawing names `3X_CQAR_004_R0` and `3X_CQAR_006_007_R0` in currently accessible project/repository resources.

The recovered public CQA/as-built PDF does **not** expose a usable:

- datum;
- EPSG/UTM definition;
- State Plane definition;
- horizontal survey-control table;
- benchmark/grid-origin definition;
- mine-grid → global coordinate conversion;
- CAES/GPS electronic coordinate export;
- surveyed plot-vertex table.

The standalone `3X_CQAR_004_R0.pdf` and `3X_CQAR_006_007_R0.pdf` named in earlier project handoffs are not presently available in the current project Sources/repository and were not separately present in the recovered public package.

## Why the historical UTM placements cannot solve this gate

The July 2026 Tyrone work deliberately used provisional visual/manual georeferencing. Historical code tested multiple image-pixel → UTM Zone 12N similarity transforms and translated placements rather than one independently surveyed transform.

The surviving sensitivity output for run `0c6d05ab-798b-40d4-b608-e01deabd6cb8` is explicitly labelled `provisional_historical_40m_cores`. Across 81 ±40 m translation placements, only 25 preserved the TP5 < TP6 ordering (`25/81 ≈ 0.309`), and the predicted TP6−TP5 separation ranged from negative to positive. Decision: `GEOMETRY_SENSITIVE_INCONCLUSIVE`.

That experiment proves that plausible placement uncertainty materially changes the depth result. Reusing one of those visual UTM hypotheses as if it were authoritative would invalidate the replacement-method screening.

## Recovered evidence package

The historical official-record recovery workflow was rerun on 2026-08-18 solely to recreate its expired evidence artifact. This was an evidence-recovery operation only: no Earth Engine run, classifier change, UI change, depth-formula change, or application change.

Recovered package includes the Tyrone 3X as-built/CQA report, annual report material, rendered pages, and provenance. The as-built report confirms survey/GPS activity and original test-plot plans, but not the missing grid-to-global transform.

## Current scientific gate

**Question:** Can the six official local-grid polygons be placed on the completed satellite/raster run using an independently verified transform?

**Answer as of 2026-08-18:** **NO — not yet.**

This is a geometry/control-data blocker, not a depth-measurement blocker. The six measured reference depths are available.

## Exact next action

Use the first available route below that supplies independent control:

1. Inspect original standalone `3X_CQAR_004_R0.pdf` and `3X_CQAR_006_007_R0.pdf` if recovered from the EMNRD package, specifically for datum, benchmark, coordinate-system, survey-control, or grid-conversion notes.
2. If those sheets do not contain the conversion, obtain the CAES/PDTI/M3 electronic survey deliverable or coordinate/control table associated with the June 2008 3X CQA work: surveyed vertices/control points, CAD/GIS, GPS/CAES export, datum, or mine-grid conversion.
3. Only if an explicitly provisional fallback is approved, perform a new multi-GCP visual georegistration using the broad as-built Figure 2/roads/topography and predeclare an acceptance threshold. It must remain labelled provisional and must not be called authoritative merely because it fits the imagery.

## Action after the transform passes

Once the transform is independently verified:

1. transform TP1/TP2/TP3/TP5/TP6/TP7 into the completed run CRS;
2. verify plot placement, area, and usable-pixel counts;
3. extract raw/less-derived physical features independently of `NB_DEPTH`;
4. summarize per plot (median, mean, standard deviation, Q25, Q75, pixel count);
5. screen same-depth replicate pairs TP1↔TP5, TP2↔TP6, TP3↔TP7 for depth signal versus surface/slope effects;
6. do **not** fit a replacement depth formula/model until that screening is complete.

Candidate raw features include VV, VH, VV/VH or dB ratio, ascending/descending differences where available, temporal SAR variation, incidence angle, DEM elevation/slope/aspect/roughness/TPI/curvature, thermal/LST/change, and carefully selected optical surface variables.
