# Tyrone 3X Six-Plot Global Transform Gate — 2026-08-18

## CURRENT STATUS — RESOLVED 2026-08-18

The geometry/control-data blocker recorded earlier in this document is now **RESOLVED for 10 m raster screening**.

An official 2024 Freeport-McMoRan Tyrone Emma Part 4 Exploration Permit Application contains 34 drill-hole rows with both:

- WGS84 longitude/latitude; and
- local Easting/Northing values.

A separate official 2021 Tyrone Emma hydrogeologic report explicitly describes local Northing/Easting values as being in the **Tyrone Mine coordinate system**.

These records provide the independent control that was missing when this gate was first written.

## Validation

A two-dimensional similarity transform was fitted using only four spatially distributed official control rows:

- `EM24-07`
- `EM24-14`
- `EM24-26`
- `EM24-33`

The remaining **30 official coordinate pairs were held out**.

Holdout result:

- mean residual: `0.001303 m`
- median residual: `0.001249 m`
- maximum residual: `0.002533 m`

This is negligible relative to a 10 m satellite pixel. No cover-depth values or NB values were used to fit, choose, or validate the transform.

After the holdout test passed, the transform was refit to all 34 official coordinate pairs:

```text
UTM_E_m = a * mine_E_ft - b * mine_N_ft + tx
UTM_N_m = b * mine_E_ft + a * mine_N_ft + ty

a  = 0.30480454058024326
b  = 0.0028379210270941257
tx = 743190.6873438816 m
ty = 3611236.9485833473 m
```

Intermediate CRS: `EPSG:32612` — WGS84 / UTM Zone 12N.

Final 34-point fit maximum residual: `0.001657 m`.

Control data and coefficients are source-controlled in:

- `data/depth_reference/tyrone_mine_grid_wgs84_controls_v1.csv`
- `data/depth_reference/tyrone_mine_grid_to_global_transform_v1.json`

## Six-plot WGS84 geometry

The existing official-drawing local polygons for TP1, TP2, TP3, TP5, TP6 and TP7 were transformed without changing their shapes or measured-depth metadata.

Raster-ready WGS84 reference:

- `data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`

This resolves the grid-to-global placement problem for the intended **10 m replacement-signal screening**.

### Important remaining geometry limitation

The transform is well constrained, but the plot boundaries are still **digitized from official AS-BUILT drawing centerlines**, not original CAD/survey vertices.

Therefore:

- do not call the WGS84 plot vertices original survey vertices;
- do not claim millimetre plot-boundary accuracy;
- the limiting uncertainty is now the source drawing digitization, not the mine-grid/global transform.

## Independent sanity check

The published Freeport-McMoRan location for Tyrone Tailing Dam 3X (`32°43'13.94"N, 108°24'51.07"W`) inversely maps to approximately:

- mine Easting `-2393.64 ft` (about W2394)
- mine Northing `39480.04 ft`

This falls inside the Dam 3X local drawing-grid extent and in the expected relative location. It was used only as a sanity check, not as fitting data.

## Historical blocker — preserved

Before this official coordinate-pair evidence was found, the project correctly rejected the July 2026 provisional visual/manual UTM placements.

The surviving `provisional_historical_40m_cores` sensitivity test used 81 translated placements and only 25 preserved TP5 < TP6 ordering. Its decision was `GEOMETRY_SENSITIVE_INCONCLUSIVE`.

That result remains valid and the historical visual georeference must **not** be revived. The new transform is independent of it.

## NB numerical-depth status

**UNCHANGED: CLOSED / FAILED VALIDATION.**

Resolving the geometry transform does not validate NB numerical depth and must not be used to retune or rescue the NB formula.

No classifier, UI, NB formula, SAR constraint, Earth Engine production logic, or application runtime is changed by this resolution.

## Exact next scientific action

The transform gate has passed. Next:

1. use the six WGS84 polygons with the completed Tyrone run or existing sensor assets;
2. verify usable pixel counts and placement;
3. extract raw/less-derived physical features excluding `NB_DEPTH`;
4. summarize mean, median, standard deviation, Q25, Q75 and pixel count per plot;
5. screen TP1↔TP5, TP2↔TP6 and TP3↔TP7 to separate depth signal from surface/slope effects;
6. do **not** train a replacement depth model until that screening is complete.

Candidate features include VV, VH, VV/VH or dB difference/ratio, ascending/descending differences where available, temporal SAR variation, incidence angle, DEM elevation/slope/aspect/roughness/TPI/curvature, thermal/LST/change, and carefully selected optical surface variables.
