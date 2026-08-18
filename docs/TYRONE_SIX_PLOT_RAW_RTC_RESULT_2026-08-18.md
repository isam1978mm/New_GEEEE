# Tyrone 3X Six-Plot Raw Sentinel-1 RTC Screen — Final Result

Date: 2026-08-18

## Decision

**NO CANDIDATE DEPTH-RESPONSIVE SIGNAL FOUND** among the preregistered raw Sentinel-1 features:

- VV dB
- VH dB
- VV−VH / log-ratio dB

This closes this raw Sentinel-1 feature family under the frozen six-plot protocol. Do **not** tune the geometry, thresholds, time period, orbit or feature formula to rescue it.

This result does not reopen the previously failed NB numerical-depth route.

## Frozen protocol

The protocol was committed before the result was inspected.

- WGS84 geometry: `data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`
- fixed inward erosion: 10 m
- source: Microsoft Planetary Computer `sentinel-1-rtc`
- period: 2018-01-01 to 2024-01-01 exclusive
- fixed orbit: descending relative orbit 56
- pixel size: 10 m
- monthly composite: pixelwise median
- plot statistic used for monotonic screen: median
- measured ordering:
  - outslope TP1 < TP2 < TP3
  - top surface TP5 < TP6 < TP7

A surface group required one strict monotonic direction in at least 70% of all usable months plus the frozen seasonal-support gates. A feature could pass only if both groups passed independently with the same direction.

No NB, classifier/PCA score or depth formula was used as a predictor.

## Execution quality

GitHub Actions run: `32167325271`

- candidate RTC items: 264
- selected fixed-orbit items: 177
- successful reads: **177 / 177**
- failures: **0**
- usable months: **72**

Fixed 10 m interior-mask pixels:

| Plot | Pixels |
|---|---:|
| TP1 | 142 |
| TP2 | 160 |
| TP3 | 136 |
| TP5 | 113 |
| TP6 | 124 |
| TP7 | 48 |

The result is therefore not a data-availability failure.

## Result by feature

| Feature | Outslope dominant result | Top-surface dominant result | Same direction? | Candidate signal? |
|---|---|---|---|---|
| VV dB | decreasing 13/72 = 18.1%; 50 nonmonotonic | increasing 25/72 = 34.7%; 36 nonmonotonic | No | **NO** |
| VH dB | increasing 20/72 = 27.8%; 41 nonmonotonic | increasing 20/72 = 27.8%; 47 nonmonotonic | Yes | **NO** |
| VV−VH dB | decreasing 24/72 = 33.3%; 39 nonmonotonic | increasing 15/72 = 20.8%; 47 nonmonotonic | No | **NO** |

All group screens failed their preregistered 70% requirement and the seasonal-support requirements.

### VH deserves no rescue

VH is the closest-looking result only because both surface groups nominally favor increasing values with depth. But each group is strictly increasing in only **20 of 72 months (27.8%)**. Most months are nonmonotonic, and the seasonal gates fail.

The earlier TP5/TP6-only VH ordering result therefore does not generalize to the complete independent six-plot depth sequence.

## Same-depth surface comparison

Median top-surface minus outslope differences across 72 months:

| Matched depth pair | VV dB | VH dB | VV−VH dB |
|---|---:|---:|---:|
| TP5 − TP1 (~2 ft) | -1.4125 | -2.4302 | +0.9677 |
| TP6 − TP2 (~3 ft) | -1.7368 | -2.5719 | +0.9399 |
| TP7 − TP3 (~4 ft) | -1.2470 | -2.3397 | +0.9677 |

The matched-depth surface offsets are large and remarkably consistent. This reinforces the earlier conclusion that surface/slope condition has a strong radar effect and cannot be ignored in numerical-depth inference.

## Scientific meaning

The verified geometry removed the old placement uncertainty, but the full six-plot test still fails.

Therefore the current evidence does **not** support converting raw Sentinel-1 VV, VH or VV/VH information into numerical cover depth for this site.

No calibration record is created. No replacement model is trained. App numerical depth remains blocked.

## Safeguards confirmed

```text
classifier_output_used = false
pca_anomaly_used = false
nb_depth_used = false
earth_engine_query_executed = false
calibration_record_created = false
training_started = false
app_depth_enabled = false
```

## Exact next action

Do not modify this radar screen.

Proceed to a **separately preregistered terrain-feature screen** using the same verified six-plot geometry. Terrain variables such as elevation, slope, aspect, roughness, TPI and curvature must be treated primarily as possible surface/slope confounders; only an independently frozen test may determine whether any contains depth-related information.

If terrain also fails, close it and move to thermal as a separate predeclared family rather than combining failed variables into an overfit six-plot model.
