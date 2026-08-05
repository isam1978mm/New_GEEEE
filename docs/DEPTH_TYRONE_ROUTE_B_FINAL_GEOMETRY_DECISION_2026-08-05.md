# Tyrone Route B Final Geometry Decision — 2026-08-05

## Conclusion

Route B did **not** recover coordinate-tied TP5 and TP6 polygons.

The corrected 2009 and 2011 NAIP exports are valid 1 m GeoTIFFs in NAD83 / UTM zone 13N (`EPSG:26913`). They confirm the broad No. 3X facility and support a close visual comparison with Figure 2 of the 2006 as-built report. They do not provide enough unambiguous homologous features to pass the approved strict georeferencing gate.

No numerical-depth unlock is allowed from this route.

## Evidence recovered

### Measured depth anchors remain valid

- TP5 confirmation-pit measurements: 28, 26, 26, 28, and 26 inches.
- TP5 mean: 26.8 inches = 0.68072 m.
- TP6 confirmation-pit measurements: 40, 35, 42, 36, and 34 inches.
- TP6 mean: 37.4 inches = 0.94996 m.

These are measured post-placement cover-thickness values. They are not design-only depths.

### Coordinate-controlled imagery recovered

The final historical exports have the following verified properties:

- years: 2009 and 2011;
- CRS: `EPSG:26913`;
- pixel size: 1.0 m by 1.0 m;
- dimensions: 2207 by 2118 pixels;
- bounds: E 179023–181230 m, N 3621371–3623489 m;
- affine transform: `[1, 0, 179023, 0, -1, 3623489]`.

The rasters are suitable as coordinate-controlled imagery references.

## Why the geometry gate fails

The approved gate requires:

- at least six well-distributed fitting controls;
- at least two independent withheld check controls;
- check RMSE no greater than 5.0 m;
- maximum check residual no greater than 7.5 m.

Figure 2 clearly draws the TP5 and TP6 survey polygons. The 2009 and 2011 images clearly show the broad dam, terrace pattern, access roads, and drainage/bench features. The problem is that the green TP5 and TP6 polygon boundaries do not consistently coincide with distinct image features.

Specific findings:

1. Some apparent plot lines pass through uniform reclaimed surface rather than along a road, berm, drain, or structure.
2. Some nearby imagery roads intersect the visually overlaid plot polygons, but the correspondence changes from one plot edge to another.
3. The outside dam/terrace pattern supports broad alignment, not exact plot-boundary placement.
4. Reusing the same approximate visual overlay to define both fitting and check points would be circular.
5. Selecting eight points anyway would require choosing among ambiguous road centers, terrace edges, or interpolated plot corners. Those would be invented controls rather than recovered evidence.

For that reason, the affine auditor was deliberately **not** run with fabricated input. A numerical residual report produced from guessed controls would not be a valid accuracy test.

## Route B subroute decisions

| Subroute | Decision | Reason |
|---|---|---|
| OSE exact-name matching | Failed | No exact or normalized matches for the map well labels. |
| OSE spatial-pattern matching | Failed | All 25 hypotheses failed the combined fit/check accuracy thresholds. |
| Current USGS imagery | Insufficient | Located the broad mine area but did not expose exact TP5/TP6 geometry. |
| Historical NAIP thumbnails | Discovery only | Corrected facility location, but JPEG thumbnails were not sufficient for a metre-based audit. |
| Historical NAIP GeoTIFFs | Valid imagery; geometry rejected | Coordinate transform is valid, but Figure 2 lacks eight defensible homologous controls. |

## Exact final decision

```text
Route B geometry recovery succeeded: no
TP5 coordinate polygon recovered: no
TP6 coordinate polygon recovered: no
Coordinate geometry unblocked: no
Plot-specific Sentinel-1 stability proven: no
Calibration row allowed: no
Numerical depth unlocked: no
```

## What would change the decision

The geometry blocker can be removed by one of the following existing-record deliverables:

- the August 2006 M3 as-built topographic survey in native coordinates;
- DWG or DXF survey drawings containing the TP5 and TP6 boundaries;
- survey-point exports with northing/easting and coordinate-system metadata;
- GPS or CAES exports;
- GIS polygons or georeferenced survey rasters;
- an official coordinate table tying the Figure 2 plot corners to a stated CRS and datum.

The current authorized next route is to wait for the existing EMNRD response and inspect any attachments it supplies. No additional email or records request is authorized.

## Current status

- Route A: waiting for the existing EMNRD response.
- Route B: completed and rejected for insufficient exact controls.
- Campaign 004: paused.
- Numerical depth: still blocked.
