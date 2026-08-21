# F180 — Bremo CBR-02 frozen measured-thickness reference subset

Date: 2026-08-21

## Purpose

Freeze a small independent set of measured Bremo West Ash Pond thickness points from the official Appendix A `CLOSURE BY REMOVAL THICKNESS SURVEY` before comparing any candidate elevation product against them.

This prevents later cherry-picking or moving the truth points after seeing a remote-sensing/elevation result.

## Source

Official Virginia DEQ package:

- `Closure by Removal Construction — Bremo Power Station — West Ash Pond (VDEQ Permit No. 618)`
- Golder Associates Inc., Project No. 19-133736, March 25, 2020
- Appendix A, Flora Surveying Associates drawing `CBR-02`, titled `CLOSURE BY REMOVAL THICKNESS SURVEY`

The drawing legend identifies the plotted crosses as `SURVEY POINT AND THICKNESS`.

The survey notes reference Virginia State Plane Coordinate System South Zone, NAD83, with elevations referenced to NAVD88.

## Coordinate calibration used

The rendered sheet was calibrated directly against its printed State Plane grid.

Visible grid intersections establish approximately:

- E 11,542,500 ft at rendered x = 1844 px
- successive 250-ft Easting grid lines at roughly 1000-px spacing
- N 3,783,000 ft at rendered y = 478 px
- successive 250-ft Northing grid lines at roughly 1000-px spacing

Therefore the plan scale in the render is approximately 4 px/ft in both axes.

Coordinates below are **digitized from the printed State Plane grid**, not copied from the original survey/CAD point file. They are adequate as a frozen pilot subset, but the original CAD/point export would remain preferable for final production-grade horizontal coordinates.

## Frozen pilot subset

| Point | Easting ft | Northing ft | Thickness ft | Thickness m |
|---|---:|---:|---:|---:|
| A1 | 11,542,698.3 | 3,782,722.0 | 0.66 | 0.2012 |
| A2 | 11,542,694.6 | 3,782,703.7 | 0.78 | 0.2377 |
| A3 | 11,542,690.0 | 3,782,684.9 | 0.84 | 0.2560 |
| A4 | 11,542,687.1 | 3,782,666.7 | 0.52 | 0.1585 |
| A5 | 11,542,681.4 | 3,782,648.7 | 0.77 | 0.2347 |
| A6 | 11,542,676.8 | 3,782,630.8 | 0.60 | 0.1829 |
| B1 | 11,542,717.5 | 3,782,718.3 | 0.59 | 0.1798 |
| B2 | 11,542,712.9 | 3,782,700.5 | 0.66 | 0.2012 |
| B3 | 11,542,709.6 | 3,782,682.1 | 0.54 | 0.1646 |
| B4 | 11,542,705.0 | 3,782,663.3 | 0.58 | 0.1768 |
| B5 | 11,542,700.4 | 3,782,645.4 | 0.55 | 0.1676 |
| B6 | 11,542,695.0 | 3,782,627.5 | 0.50 | 0.1524 |

Machine-readable copy:

`data/research/bremo_f180_cbr02_reference_subset.csv`

## Why these points

- They are interior CBR-02 survey points, not values inferred from excavation volume.
- The thickness labels are clearly readable on the official drawing.
- They span the six-inch threshold and nearby larger measured changes.
- They were frozen before testing any candidate external elevation surface.

## Classification

These values are labeled:

> **measured survey-to-survey thickness reference points**

They are not:

- the full CCR excavation depth;
- evidence that the 327,323 yd3 quantity was survey-derived;
- a replacement for the missing June 9, 2016 pre-excavation H&B surface.

## F180 decision

**PASS — a fixed independent Bremo pilot truth set now exists.**

The smallest measured value in the frozen set is 0.50 ft = 0.1524 m, which is directly relevant to the frozen 0.15 m vertical-resolution gate.

## Remaining caution

The thickness values are direct survey labels, but their Easting/Northing coordinates in this pilot CSV were digitized from the printed grid. Do not claim sub-foot horizontal survey accuracy from this digitization. If an original Flora CAD/point file becomes available, replace only the horizontal coordinates after provenance checking; do not change the frozen thickness values in response to model results.

## Next action — F181

Identify the exact independent elevation surface pair that can bracket the 2019–2020 VC-to-over-excavation interval at Bremo and test its timing/coverage/source accuracy **before** reading any residual against the frozen thickness values.

Do not use the frozen answers to choose among candidate surfaces.
