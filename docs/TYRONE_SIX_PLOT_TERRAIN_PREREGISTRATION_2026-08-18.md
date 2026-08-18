# Tyrone 3X Six-Plot Terrain Screen — Preregistration

Date: 2026-08-18

Purpose: test terrain variables separately using the verified six-plot geometry. This is a signal/confounder screen, not model training.

Frozen source: Microsoft Planetary Computer `3dep-seamless`, 10 m GSD, EPSG:32612, 10 m analysis pixels. If multiple 10 m DEM items overlap, use their pixelwise median.

Frozen plot interiors: 10 m and 20 m inward buffers. Each plot must retain at least 15 valid pixels.

Frozen features: elevation, slope, northness, eastness, 3x3 roughness, approximately 50 m-radius TPI using an 11x11 mean, and Laplacian curvature. Retain mean, median, standard deviation, Q25, Q75 and valid-pixel count. Use plot median for the screen.

Depth levels are replicated across surface types: shallow = TP1 and TP5; medium = TP2 and TP6; deep = TP3 and TP7.

Direct-depth screen: a feature passes only when the two shallow values are completely separated from the two medium values, and the two medium values are completely separated from the two deep values, in one common direction. The same direction must pass at both inward buffers. No tolerance is fitted.

Surface-confounder screen: compare TP5 minus TP1, TP6 minus TP2 and TP7 minus TP3. A feature is flagged only when all three matched-depth differences have the same nonzero sign at both buffers, with the same sign across buffers.

Safeguards: no NB_DEPTH, no classifier/PCA depth evidence, no changing the source/features/buffers/rules after results, no depth model fitting, no Earth Engine, and no app-depth enablement.

If no direct terrain candidate passes, close this family and preregister thermal separately.
