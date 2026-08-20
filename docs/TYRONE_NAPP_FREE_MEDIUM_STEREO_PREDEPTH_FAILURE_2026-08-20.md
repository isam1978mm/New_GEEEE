# Tyrone 1996 NAPP free medium-resolution stereo — pre-depth accuracy result — 2026-08-20

## Decision

**The free EarthExplorer medium-resolution NAPP scans are CLOSED for numerical cover-depth estimation.**

This decision was reached **before reading or fitting any Tyrone cover-depth answers**. The test asked only whether two independent stereo pairs from the same 1996 flight can reconstruct the same terrain with repeatability remotely close to the already-frozen photogrammetric gate.

They cannot.

The previously frozen historical-surface gate requires `RMSEz <= 0.15 m` on held-out stable patches before any depth comparison is allowed. Independent 1996 stereo reconstructions from the free scans disagree by metres, not centimetres.

This result does **not** authorize purchase of higher-resolution scans. The 14-micron on-demand option remains untested and requires explicit user approval before any order/payment.

## Inputs

EarthExplorer NAPP triplet, acquisition 1996-09-28:

- `NP0NAPP009519108` — roll 9519 frame 108
- `NP0NAPP009519109` — roll 9519 frame 109
- `NP0NAPP009519110` — roll 9519 frame 110

Uploaded repository archive:

- `data/research/tyrone_napp_1996/Desktop.7z.001`
- `data/research/tyrone_napp_1996/Desktop.7z.002`
- `data/research/tyrone_napp_1996/Desktop.7z.003`

The split archive passed `7z` integrity testing and contains all three TIFFs.

Camera calibration:

- USGS report `R2104`
- Zeiss RMK A 15/23
- camera serial `124257`
- lens serial `124308`
- calibrated focal length `152.773 mm`
- report states fiducial-distance measurement accuracy within `0.003 mm`

The exact R2104 fiducial matrix was used for interior-orientation work. The four calibrated corner fiducials were used to place each scan into a common camera-coordinate geometry before stereo matching.

## Pre-depth firewall

The following were **not used** in this experiment:

- TP5 measured depth;
- TP6 measured depth;
- TP7 measured depth;
- TP1/TP2/TP3 measured depth;
- any of the 43 mapped test-pit cover depths;
- any fitted depth offset or scale;
- classifier output;
- NB depth proxy.

No classifier, UI, NB formula, Earth Engine production path, or numerical-depth production code was modified.

## Stereo usability passed

The free scans are real, overlapping stereo photographs; the failure is accuracy, not absence of overlap.

Initial adjacent-frame feature matching produced thousands of geometrically consistent matches:

- frame 108 -> 109: about 3,100+ fundamental-matrix inliers;
- frame 109 -> 110: about 3,300+ fundamental-matrix inliers.

After R2104-based scan normalization, calibrated essential-matrix solutions produced camera motion consistent with a NAPP flight strip: adjacent translation was almost entirely along one camera axis and rotations were small.

A deterministic train/validation geometry check selected the essential-matrix RANSAC threshold without using any depth values. On held-out 108/109 tie points, rectified vertical epipolar error was approximately:

- median: `0.246 px`
- 95th percentile: `0.977 px`

So the photographs are stereo-usable.

## Dense stereo repeatability

Dense sub-pixel stereo was tuned only against image-to-image tie-point geometry, never against depth.

For the first pair, the selected dense matcher had held-out disparity agreement of roughly:

- median absolute disparity difference: about `0.21-0.23 px`
- 95th percentile absolute disparity difference: about `0.77-0.80 px`

The independent second pair reproduced essentially the same image-space behavior:

- median absolute disparity difference: `0.221 px`
- 95th percentile absolute disparity difference: `0.795 px`

This shows the result is not caused by one broken stereo pair.

## Fatal independent-surface test

The two stereo pairs were reconstructed independently over the same 3X-area 1996 terrain:

1. frames 108 + 109;
2. frames 109 + 110.

The second pair was placed in the first pair's relative 3-D system using common three-view image tracks only. No modern depth or cover measurements were used.

The two surfaces were then compared using spatially separated control/check patch logic. A global similarity alignment was fitted on control patches and evaluated on held-out patches.

Approximate held-out vertical repeatability:

| Patch size | Median absolute disagreement | Held-out RMSE |
|---:|---:|---:|
| 40 m | `1.96 m` | `3.55 m` |
| 60 m | `1.66 m` | `4.04 m` |
| 80 m | `1.56 m` | `3.81 m` |
| 100 m | `1.79 m` | `3.17 m` |
| 120 m | `2.15 m` | `2.73 m` |
| 200 m | `1.44 m` | `3.44 m` |

Even selecting low-slope historical patches did not rescue the result; 40 m-class low-slope patch RMSE remained on the order of `~2 m`.

The exact metre scale uses the approximately equal NAPP station spacing inferred from the catalog frame centers. Reasonable uncertainty in that baseline cannot turn metre-scale disagreement into the required `0.15 m`.

## Frozen-gate comparison

Frozen Gate 4A requirement:

- `RMSEz <= 0.15 m`
- `abs(median vertical residual) <= 0.05 m`
- 95th percentile absolute vertical residual `<= 0.30 m`
- residual-plane drift across 3X `<= 0.10 m`

Observed free-scan independent repeatability is roughly **one to two orders of magnitude worse** than the required vertical accuracy.

Therefore the route stops **before** comparison with any measured cover depth.

## Exact interpretation

This failure means:

> The free medium-resolution 1996 NAPP TIFFs are useful historical imagery, but they are not metrically repeatable enough to support a defensible Tyrone cover-depth estimate under the frozen accuracy gate.

It does **not** mean historical stereo photogrammetry is impossible in principle. It means this free scan product is insufficient for the required sub-decimetre task.

## Route status after this result

| Route | Status |
|---|---|
| Free NAPP medium-resolution stereo | **CLOSED for numerical depth** |
| Paid/on-demand 14-micron NAPP scan | **HELD / NOT APPROVED** |
| Free public 2004 NAIP before Sept 2004 | **CLOSED — no Tyrone scenes found** |
| Public 2007 Appendix A design drawings | **CLOSED for 3X — 3X not in the drawing set** |
| Original 2004 native pre-cover/grading surface from EMNRD | **CLOSED from EMNRD** |
| Recorded measured-depth lookup for reviewed Tyrone zones | **Still scientifically safe as lookup, not estimation** |
| General numerical depth estimation | **Still blocked** |

## Discipline

Do not:

- reveal or fit the Tyrone measured depths to rescue this medium-scan result;
- relax the frozen `0.15 m` historical-surface gate;
- treat the free scans as depth because the stereo visually looks good;
- order 14-micron scans without explicit user approval;
- return to random satellite-feature depth hunting.
