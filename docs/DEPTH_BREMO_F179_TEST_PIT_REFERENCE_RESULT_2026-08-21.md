# F179 — Bremo Appendix A test-pit reference check

Date: 2026-08-21

## Purpose

Build a small auditable numerical reference from the Appendix A survey drawing and check whether the drawing metadata can be georeferenced from the published State Plane grid.

This is supplementary to the decisive `CBR-02` Thickness Survey. The test pits are not a substitute for the VC-to-over-excavation thickness surface.

## Source

Official Virginia DEQ package:

`SWP618 PartialClosureApproval by Removal West Ash Pond and CQA Rpt Part 1 of 2 Narrative App A B.pdf`

Appendix A PDF page 20:

- Flora Surveying Associates
- `CLOSURE BY REMOVAL SURVEY`
- drawing `CBR-01`
- Virginia State Plane Coordinate System South Zone, NAD83
- elevations referenced to NAVD88

## Important source discrepancy

The CQA narrative/table states that **21 test pits/test holes** were excavated.

However, direct visual inspection of Appendix A drawing `CBR-01` shows labels **Test Pit 1 through Test Pit 22**.

This discrepancy is not silently reconciled here.

Until the source CAD/survey file or an explanatory note is recovered:

- narrative count = 21;
- drawing-visible numbered pits = 22;
- do not claim which source is the clerical error.

## Directly readable test-pit elevations

The drawing gives top and bottom elevations in feet. The difference is the surveyed test-pit depth, not the VC-to-final over-excavation thickness.

| Test pit | Top elev (ft) | Bottom elev (ft) | Difference (ft) | Difference (m) |
|---:|---:|---:|---:|---:|
| 1 | 207.42 | 206.81 | 0.61 | 0.1859 |
| 2 | 202.90 | 202.03 | 0.87 | 0.2652 |
| 3 | 204.00 | 203.16 | 0.84 | 0.2560 |
| 4 | 203.89 | 203.03 | 0.86 | 0.2621 |
| 5 | 202.99 | 202.27 | 0.72 | 0.2195 |
| 6 | 203.03 | 202.29 | 0.74 | 0.2256 |
| 7 | 212.37 | 211.66 | 0.71 | 0.2164 |
| 8 | 202.25 | 201.48 | 0.77 | 0.2347 |
| 9 | 203.37 | 202.65 | 0.72 | 0.2195 |
| 10 | 203.08 | 202.29 | 0.79 | 0.2408 |
| 11 | 203.46 | 202.41 | 1.05 | 0.3200 |
| 12 | 212.12 | 211.33 | 0.79 | 0.2408 |
| 13 | 213.33 | 212.81 | 0.52 | 0.1585 |
| 14 | 207.10 | 206.12 | 0.98 | 0.2987 |
| 15 | 209.05 | 208.22 | 0.83 | 0.2530 |
| 16 | 204.24 | 203.53 | 0.71 | 0.2164 |
| 17 | 203.20 | 202.47 | 0.73 | 0.2225 |
| 18 | 202.92 | 202.20 | 0.72 | 0.2195 |
| 19 | 197.73 | 196.71 | 1.02 | 0.3109 |
| 20 | 210.83 | 210.08 | 0.75 | 0.2286 |
| 21 | 219.04 | 218.30 | 0.74 | 0.2256 |
| 22 | 204.15 | 203.44 | 0.71 | 0.2164 |

For the 22 drawing-visible pits, the read values span approximately:

- minimum: 0.52 ft = 0.1585 m;
- maximum: 1.05 ft = 0.3200 m;
- median: 0.745 ft = 0.2271 m;
- mean: 0.7809 ft = 0.2380 m.

These numbers are a secondary physical-depth check only.

## Georeferencing check

The published sheet contains State Plane grid labels. Direct inspection gives, for example:

- Easting grid line: `E11542250`;
- Easting grid line: `E11543000`;
- Northing grid line: `N3783000`;
- Northing grid line: `N3782750`;
- Northing grid line: `N3782500`;
- Northing grid line: `N3782250`.

The grid spacing and drawing scale are sufficient to georeference the published sheet to the stated NAD83 Virginia State Plane South system without inventing a location.

## F179 decision

### Published-drawing georeference gate: PASS

The Appendix A drawing has enough coordinate framework to recover approximate State Plane locations for survey features from the published sheet.

### Test-pit depth reference: PASS as supplementary evidence

The top/bottom elevations provide direct surveyed vertical distances in the same magnitude range as the frozen 0.15 m gate.

### VC-to-final thickness truth: NOT YET EXTRACTED

Do not use the test-pit depths as a substitute for the actual `CBR-02` survey-point thickness values. The next step must work from the Thickness Survey itself.

## Next action — F180

Digitize a fixed, clearly readable subset of `CBR-02` survey points:

1. choose points away from steep side slopes and map-edge distortion;
2. record each published thickness value;
3. derive State Plane location from the sheet grid;
4. convert thickness to metres;
5. freeze that reference set before testing any candidate elevation source;
6. then compute the existing residual gates without tuning to those values.

Do not return to broad candidate search while this direct measured thickness sheet remains usable.
