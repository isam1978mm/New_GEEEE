# Plant Kraft AP-1 Map and Georeference Result — 2026-07-27

## Decision

```text
CONFIRMED REMOVAL EVIDENCE = STRONG
SURVEY AND EXCAVATION MAPS = RECOVERED
LOCAL 20 M SIZE SUPPORT = PASSED IN PRINCIPLE
EXACT REAL-WORLD EXECUTION GEOMETRY = NOT PASSED
STABLE SENTINEL-1 PERIOD = NOT CONFIRMED
CALIBRATION ROW = NOT CREATED
EARTH ENGINE QUERY = NOT RUN
```

The official Georgia Power `Certification of CCR Removal` PDF was downloaded and its engineering-map pages were recovered successfully.

Plant Kraft AP-1 remains strong evidence of a physically removed CCR area. It is not approved as a confirmed-negative calibration row because the verified excavation limit is stored as a raster overlay on an aerial photograph, the independent real-world georeference could not be validated, and a stable post-removal observation period was not established.

No analyst-drawn substitute boundary was created.

## Official map evidence recovered

### Figure 2 — Post-excavation topographic map

```text
PDF page = 9
map title = Plant Kraft AP-1 Post Excavation Topographic Map
drawing date = 2016-08-22
scale = 1 inch = 40 feet
coordinate system = Georgia East Zone
horizontal datum = NAD83
engineering/survey firm = KEM & Co., LLC
```

This is a professional post-excavation topographic drawing with surveyed elevations and identifiable permanent facility features.

### Figure 3 — Verified excavation limits

```text
PDF page = 11
map title = Plant Kraft AP-1 Excavation Limits
verified excavation boundary = visible red outline
clean-area annotations = visible
```

The official figure clearly identifies the AP-1 excavation footprint and repeatedly annotates portions of the excavated area as clean.

However, the red excavation outline is baked into the embedded aerial image. It is not a vector survey line with directly extractable State Plane coordinates.

### Figure 4 — Top of structural fill

```text
PDF page = 13
map title = Plant Kraft AP-1 Topographic Map — Top of Structural Fill
drawing date = 2017-06-02
```

This drawing confirms that a surveyed structural-fill surface was produced after excavation.

## Physical size screen

The Figure 2 survey scale and the mapped AP-1 footprint show that the removed area is physically large enough, in principle, to contain multiple 20 m Sentinel-1 footprints.

Therefore:

```text
local physical size gate = passed in principle
execution polygon size gate = not tested
```

The local size conclusion does not establish real-world placement, boundary uncertainty, surface stability, or pixel purity.

## Independent georeference attempt

Figure 3 was compared against USGS/USDA NAIP imagery through an automated feature-registration screen.

```text
NAIP records queried = 13
best automatic candidate year = 2023
descriptor matches = 15
RANSAC inliers = 4
inlier ratio = 0.267
```

The automatic transform was rejected during manual review because:

- only four matches supported the homography;
- the transformed source extent was visibly warped and partly outside the target image;
- the match visualization did not establish defensible permanent control features;
- the former Plant Kraft area has undergone major industrial/port redevelopment, reducing the number of unchanged controls shared with the older excavation aerial.

The nominal zero-pixel residual reported for the four fitted inliers is not independent validation. With only four inliers, the homography can exactly fit those points while still being globally wrong.

Therefore:

```text
automatic NAIP georeference = rejected
exact WGS84 excavation polygon = not created
boundary-position uncertainty = not assigned
```

The automatically transformed red-pixel output is QA failure evidence only and must not be used as geometry.

## Observation timing

The broader public record supports:

- ash-pond removal was complete by March 2018 or earlier;
- a possible post-removal, pre-transfer interval existed during approximately 2018–2020;
- the property was transferred to the Georgia Ports Authority in 2021;
- later imagery shows substantial redevelopment of the former plant property.

No record reviewed proves that the exact AP-1 excavation footprint remained materially unchanged throughout the possible 2018–2020 window.

Therefore:

```text
possible quiet period = identified
quiet period for exact AP-1 footprint = unverified
stable Sentinel-1 period = not confirmed
```

## What remains valid

```text
physical CCR removal confirmed = yes
post-excavation professional survey recovered = yes
verified excavation-limit figure recovered = yes
top-of-structural-fill survey recovered = yes
area large enough in principle = yes
```

## What is not approved

```text
survey-vector excavation boundary = no
exact WGS84 geometry = no
numerical boundary uncertainty = no
stable observation period = no
clean 20 m execution polygons = no
Earth Engine query = no
confirmed-negative calibration row = no
```

The county parcel, environmental-covenant tract, hazardous-site point, automatic failed transform, and an analyst-drawn aerial estimate must not be substituted for the verified AP-1 excavation limit.

## Machine-readable result

```text
data/plant_kraft_ap1_map_georeference_screen_result.json
```

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
plant_kraft_confirmed_removal = yes
plant_kraft_map_pages_recovered = yes
plant_kraft_local_20m_size_support = yes_in_principle
plant_kraft_exact_georeference = failed
plant_kraft_stable_timing = unverified
plant_kraft_calibration_row_ready = no
```

## Next step

Retain Plant Kraft as strong confirmed-removal evidence only. Continue to a completed removal or cover project whose final verified boundary is directly georeferenced or supplied as survey-vector geometry, whose numerical uncertainty is supported, and whose final surface remained stable long enough for a clean Sentinel-1 screen.
