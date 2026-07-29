# Tyrone Attachment I Electronic-Files Recovery Result

Date: 2026-07-29

## Decision

**The public Attachment I route is closed.**

The recovered public files do not provide CAD, GIS, surveyed Test Plot 5/6 coordinates, or a Tyrone mine-grid conversion.

This result does not invalidate the measured Tyrone depth anchors. It only means the missing electronic-media route cannot supply execution geometry from the files currently published online.

## What was recovered

The official EMNRD record includes:

- `GR010RE_20081223_FAReduction-AttachmentI.pdf`
- `GR010RE_20081223_FAReduction-Application.pdf`

Both were recovered through a temporary GitHub Actions workflow and inspected structurally and visually.

## Attachment I result

Attachment I is a one-page scanned cover sheet containing only:

```text
Attachment I
Electronic Files for This Application
```

The PDF contains:

- no embedded attachments;
- no PDF links or annotation URIs;
- no filenames;
- no CAD or GIS payload;
- no coordinate-system information;
- no mine-grid conversion.

## Associated application result

The associated application is a five-page scanned financial-assurance request.

Page 2 lists Attachments A through I. Its description of Attachment I is:

```text
Electronic Copy of Application Materials (provided on CD)
```

This confirms that Attachment I referred to a physical CD containing an electronic copy of the submitted application materials. The application does not provide a manifest of the CD contents.

The remaining pages contain:

- financial-assurance calculations and requested permit changes;
- the closing letter and signature;
- a general Mangas Valley tailing-impoundment location figure.

They do not contain:

- Test Plot 5 or Test Plot 6 coordinates;
- CAD, DWG, DXF, GIS, KML, KMZ, or shapefile names;
- survey corner tables;
- a local-grid-to-State-Plane or local-grid-to-UTM conversion;
- an electronic-media file inventory.

## Consequence for the feasible local-depth MVP

The local numerical-depth MVP remains usable for reviewed known zones and remains merged on `main`.

The two provisional measured anchors remain:

| zone | minimum | best | maximum |
|---|---:|---:|---:|
| `tyrone_tp5` | 0.65532 m | 0.68072 m | 0.70612 m |
| `tyrone_tp6` | 0.85090 m | 0.94996 m | 1.04902 m |

However, this public electronic-files route does not reduce the uncertainty of the provisional Test Plot polygons.

## Current execution boundary

```text
local_depth_mvp_merged = true
known_zone_ranges_available = true
unknown_aoi_radar_depth_ready = false
official_plot_geometry_recovered = false
earth_engine_query_executed = false
training_started = false
global_validated_depth_ready = false
```

## Exact next step

Continue with provisional manual georeferencing of the 2006 Test Plot drawing onto the 2020 coordinate-grid facility map.

The next screen must:

1. quantify the georeferencing uncertainty;
2. shrink Test Plot 5 and Test Plot 6 by that uncertainty plus the radar boundary exclusion;
3. confirm whether usable interiors remain;
4. label all geometry as derived and provisional;
5. run only a local raw-Sentinel-1 ordering screen if both interiors remain large enough.

No classifier score or PCA anomaly score may be used as depth evidence.
