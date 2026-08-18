# Tyrone 3X Six-Plot Raw Sentinel-1 RTC Screen — Preregistration

Date: 2026-08-18

## Question

After accounting for the two known surface groups, does any raw Sentinel-1 feature change consistently with measured cover-depth ordering across the six Tyrone 3X plots?

This is a **signal screen**, not model training and not a numerical depth formula.

## Frozen inputs

- Geometry: `data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`
- Conservative geometry rule: fixed 10 m inward buffer after projection to EPSG:32612.
- Public source: Microsoft Planetary Computer `sentinel-1-rtc`.
- Period: 2018-01-01 through 2023-12-31.
- Orbit: descending, relative orbit 56. This is reused from the earlier Tyrone public-RTC work; it is not selected from the new six-plot result.
- Pixel size: 10 m.
- Features: VV dB, VH dB, and VV−VH/log-ratio dB.
- Monthly composite: pixelwise median of all successful selected acquisitions in a month.

For every plot/month/feature retain mean, median, standard deviation, Q25, Q75 and valid-pixel count.

## Independent measured-depth order

Only the already measured depth ordering is used:

- outslope: TP1 < TP2 < TP3;
- top surface: TP5 < TP6 < TP7.

No depth values are used to calculate radar features.

## Frozen screen

For each month and feature, each surface group is labelled:

- strictly increasing with depth order;
- strictly decreasing with depth order; or
- nonmonotonic.

A surface group passes only if:

1. at least 24 usable months exist;
2. one monotonic direction occurs in at least 70% of all usable months;
3. for DJF, MAM, JJA and SON, at least 4 usable months exist and at least 60% match the group dominant direction.

A feature becomes a **candidate depth-responsive signal** only if **both** surface groups pass independently and their dominant directions agree.

This designation still does not validate numerical depth.

## Same-depth surface check

Report TP1↔TP5, TP2↔TP6 and TP3↔TP7 feature differences descriptively. No threshold will be chosen from those differences after the run.

## Safeguards

- exclude `NB_DEPTH`;
- do not use classifier/PCA output as depth evidence;
- do not change thresholds after results are visible;
- do not train or fit a replacement depth model;
- do not query Earth Engine;
- do not enable app depth.

If the screen fails, document the failure without tuning this protocol. The next route is a separately preregistered physical feature family such as terrain or thermal.
