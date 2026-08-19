# Tyrone NISAR GCOV L-band screen result — 2026-08-19

## Decision

**CLOSED / FAILED VALIDATION for direct NISAR amplitude depth signal.**

The preregistered PR #97 screen was run exactly on the seven fixed public PROVISIONAL NISAR L2 GCOV acquisitions over Tyrone 3X. All seven acquisitions were usable and every plot exceeded the frozen minimum pixel-support requirement.

No tested direct L-band amplitude feature passed the frozen gate:

| Feature | Increasing support | Decreasing support | Frozen requirement | Decision |
|---|---:|---:|---:|---|
| HH dB | 0/7 | 1/7 | >=5/7 overall, >=3/4 ascending, >=2/3 descending | FAIL |
| HV dB | 0/7 | 0/7 | same | FAIL |
| HH-HV dB | 0/7 | 0/7 | same | FAIL |

The single HH decreasing event occurred on one ascending acquisition only. It does not approach the preregistered support gate.

## Pixel support

The screen used the PR #81 validated WGS84 six-plot geometry with the fixed 10 m inward erosion. The frozen minimum was 15 valid pixels per plot / feature / acquisition.

The minimum actually observed across the full screen was **48 valid pixels**, so this result is not a spatial-support failure.

## Surface-condition diagnostic

Matched-depth top-surface minus outslope offsets remain substantial.

For HH dB, the offsets across the matched-depth plot pairs and seven acquisitions ranged from approximately **-4.93 to -1.22 dB**, with mean approximately **-2.99 dB**. This is a strong surface/site effect compared with the absent stable depth ordering.

HV and HH-HV also show inconsistent surface offsets and no stable depth ordering.

## Technical history

The first authenticated run did not evaluate science. `EARTHDATA_TOKEN` was present, but `earthaccess.login()` attempted a separate NASA profile lookup and the GitHub runner could not reach that endpoint. No backscatter values were inspected in that attempt.

The rerun changed only the authentication implementation: the already-issued Earthdata bearer token was passed directly to authenticated HTTPS range requests. No granule, geometry, buffer, feature, threshold, or decision rule changed.

The corrected run completed successfully and produced the scientific result above.

## Safeguards

- no classifier use or modification;
- no NB_DEPTH use or formula change;
- no Earth Engine query;
- no model fitting;
- no calibration record;
- no result-driven threshold or geometry change;
- no UI change;
- no app-depth enablement.

## What this means

The direct free-sensor routes tested at Tyrone now include C-band Sentinel-1 amplitude, terrain/northness, Landsat daytime thermal, Sentinel-2 NDVI/NDMI, and NISAR L-band HH/HV amplitude. None has passed independent/preregistered validation as a direct numerical-depth signal.

Do not rescue the NISAR amplitude result by choosing favorable dates, changing thresholds, moving polygons, or creating a formula from the observed values.

## Exact next action

**Stop blind feature-family expansion and reassess the replacement-depth strategy using the accumulated negative evidence.**

Numerical app depth remains blocked. The next scientific decision should determine whether a physically different measurement route or additional independent measured-depth sites are required before any further model attempt.
