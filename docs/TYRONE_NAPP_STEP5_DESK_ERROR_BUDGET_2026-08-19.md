# Tyrone NAPP Step 5 — Desk Photogrammetric Error Budget — 2026-08-19

## Decision

The September 28, 1996 NAPP stereo triplet is worth pursuing **only at 25 micron or better scan resolution**.

- **63 micron / 400 dpi:** reject for the numerical-depth route before reconstruction.
- **25 micron / 1000 dpi:** borderline but scientifically worth a first reconstruction if an existing free scan is available.
- **14 micron / 1800 dpi color on-demand scan:** substantially more plausible if 25 micron is unavailable or fails for image-resolution reasons, but do not purchase it without explicit user approval.

This is a **screening calculation only**. It is not a depth result and it does not pass Gate 4A or Gate 4B by itself.

## Frozen gates carried forward

From the controlling Tyrone document:

- held-out stable-terrain Gate 4A: `RMSEz <= 0.15 m` plus the other frozen bias / percentile / drift limits;
- independent depth Gate 4B: overall `MAE <= 0.10 m`, `RMSE <= 0.15 m`, and the frozen plot-mean/order requirements;
- known Tyrone depths are holdout truth only and cannot be used to align, shift, scale, or choose the reconstruction.

## Source geometry

EarthExplorer metadata confirms the preferred triplet:

| Entity | Date | Roll | Frame | Flight line | Station | Camera | Lens | Focal length | Film |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| `NP0NAPP009519108` | 1996-09-28 | 9519 | 108 | 1084E | 281 | 124257 | 124308 | 152.773 mm | Color Infrared |
| `NP0NAPP009519109` | 1996-09-28 | 9519 | 109 | 1084E | 280 | 124257 | 124308 | 152.773 mm | Color Infrared |
| `NP0NAPP009519110` | 1996-09-28 | 9519 | 110 | 1084E | 279 | 124257 | 124308 | 152.773 mm | Color Infrared |

Frame-center latitude spacing between frames 108 and 109 is `0.03125 deg`, corresponding to approximately `3.475 km` ground baseline at Tyrone.

USGS documents NAPP as nominally:

- vertical mapping photography;
- approximately `1:40,000` scale;
- 6-inch-class focal length;
- approximately 60% forward overlap for stereo.

Using the actual calibrated focal length `152.773 mm` and nominal 1:40,000 scale gives an approximate flying height above ground of:

`H ≈ 40,000 × 0.152773 m = 6,110.92 m`

Using the observed adjacent-frame center spacing:

- `B ≈ 3,474.84 m`
- `B/H ≈ 0.569`
- `H/B ≈ 1.759`

These values are consistent with a normal NAPP stereo geometry.

## Scan-resolution screening

At 1:40,000 nominal scale:

| Scan | Ground sample distance from scan pitch |
|---|---:|
| 63 micron | about `2.52 m/pixel` |
| 25 micron | about `1.00 m/pixel` |
| 14 micron | about `0.56 m/pixel` |

For a first-order stereo screen, use the standard proportional relationship:

`vertical image-measurement error ≈ (H/B) × GSD × parallax_measurement_error_in_pixels`

This does **not** include all real error sources. It is deliberately used only to decide whether a scan resolution is already hopeless before reconstruction.

### Image-measurement component only

| Scan | If parallax precision = 0.05 px | If parallax precision = 0.10 px |
|---|---:|---:|
| 63 micron | about `0.222 m` | about `0.443 m` |
| 25 micron | about `0.088 m` | about `0.176 m` |
| 14 micron | about `0.049 m` | about `0.098 m` |

### Precision required merely to reach the 0.15 m Gate 4A RMSE scale

Ignoring every other error source, the image-matching parallax precision would need to be approximately:

| Scan | Required parallax precision for 0.15 m image component |
|---|---:|
| 63 micron | `<= 0.034 px` |
| 25 micron | `<= 0.085 px` |
| 14 micron | `<= 0.152 px` |

The 63-micron product therefore fails the desk gate: it would require unrealistically tiny image-measurement error **before** adding film deformation, camera model, control, datum, terrain, vegetation, and reference-surface error.

The 25-micron product is borderline: sub-0.1-pixel stereo matching could put the image-measurement component near the Gate 4A scale, but there is little remaining error budget. It is worth trying only because the real reconstruction will be validated against held-out stable terrain before any depth comparison.

The 14-micron color scan provides materially more geometric headroom and is the preferred fallback if the free 25-micron product is unavailable or is demonstrably inadequate for resolution reasons.

## Important: this is a lower-bound screen, not predicted final RMSE

The numbers above omit important contributors, including:

- original film deformation/shrinkage;
- lens/camera calibration residuals;
- fiducial measurement/orientation error;
- camera tilt and scale variation;
- ground-control and check-point error;
- modern LiDAR/reference error;
- datum transformation error;
- surface matching error on weak texture or vegetation;
- terrain slope sensitivity;
- interpolation / DEM generation error;
- the separate 1996-to-2004 grading-contamination problem.

Therefore **25 micron does not automatically pass**. It only survives the desk screening step.

## USGS product availability / price rules

USGS currently documents NAPP products as:

- 63 micron medium-resolution downloads: free when available;
- existing 25 micron high-resolution downloads: free when available;
- color on-demand film scan: 14 micron;
- on-demand high-resolution scan: `$30 per frame` plus a `$5` handling fee for an order requiring payment.

For the three-frame CIR triplet, an on-demand 14-micron order would therefore be about `$95` if all three frames were ordered together (`3 × $30 + $5`). **Do not place or authorize this purchase without explicit user approval.**

USGS source:
https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-aerial-photography-program-napp

## Step 5 result

**PASS TO FREE-25-MICRON AVAILABILITY CHECK.**

The next action is not to reconstruct 63-micron imagery. The next action is:

1. sign in to EarthExplorer and inspect the Download options for the three exact entity IDs;
2. if an existing **25 micron / 1000 dpi TIFF** is available for all three, download those three free files;
3. preserve original TIFFs and metadata unchanged;
4. if only 63 micron is available, do not spend reconstruction effort on it for depth;
5. if no 25 micron scan exists, return to the user with the exact 14-micron paid fallback cost before any purchase;
6. after obtaining 25 micron or better imagery, run one reconstruction under the already frozen Gate 4A/4B rules.

No numerical depth is unblocked yet.