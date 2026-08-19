# Tyrone NISAR L-band coverage feasibility result — 2026-08-18

## Decision

**PASS — PUBLIC NISAR L-BAND COVERAGE EXISTS OVER TYRONE 3X AT USEFUL FREQUENCY-A RESOLUTION.**

This is a coverage/product-feasibility result only. No NISAR backscatter values were downloaded or inspected, no scientific signal threshold was evaluated, and no model or calibration row was created.

## Metadata query

A metadata-only ASF Search API query was run at `POINT(-108.415 32.72)` for NISAR PROVISIONAL products from 2026-06-17 through 2026-08-19.

Result:

- 7 L2 GCOV products;
- 7 L2 GSLC products;
- all seven acquisition times are represented in both product families;
- 4 ascending acquisitions on path 48 / frame 18;
- 3 descending acquisitions on path 27 / frame 72;
- all are mode `40+5`;
- Frequency A provides HH/HV dual-pol support.

GCOV acquisition starts:

- 2026-06-17 12:26:15Z — ascending;
- 2026-06-28 01:59:33Z — descending;
- 2026-06-29 12:26:15Z — ascending;
- 2026-07-10 01:59:32Z — descending;
- 2026-07-11 12:26:14Z — ascending;
- 2026-07-22 01:59:31Z — descending;
- 2026-07-23 12:26:13Z — ascending.

## Why GCOV Frequency A is the primary next product

NISAR PROVISIONAL L-band products were released publicly on July 20, 2026. They are fully calibrated and partially validated. The PROVISIONAL archive includes acquisitions from June 17, 2026 forward.

The L2 GCOV product provides calibrated gamma-0 polarimetric covariance/backscatter terms with radiometric terrain correction and geocoding. For land acquisitions collected at 40 MHz Frequency A, GCOV is posted on a 10 m square grid. Frequency B for this mode is much coarser and is excluded from the primary Tyrone test.

GSLC is also available and gives finer 5 m × 5 m Frequency-A posting for 40 MHz acquisitions, but it is phase-preserving complex data and the files are much larger. It is not needed for the first amplitude-only L-band signal screen and is therefore deferred rather than mixed into the initial test.

## Scientific meaning

This result does **not** prove that L-band measures cover depth. It only removes the previous feasibility blocker: a genuinely different public radar wavelength is now available over the verified Tyrone reference plots at sufficient nominal posting for a controlled test.

The direct C-band, northness, thermal, NDVI, and NDMI routes remain closed under their existing preregistered failures. They will not be retuned or mixed into this L-band screen.

## Safeguards

- imagery downloaded: NO;
- backscatter values inspected: NO;
- Earth Engine: NO;
- classifier changed: NO;
- NB formula changed: NO;
- UI changed: NO;
- model fitted: NO;
- calibration row created: NO;
- app numerical depth enabled: NO.

## Exact next action

Preregister the seven-acquisition NISAR L2 GCOV PROVISIONAL Frequency-A six-plot screen **before** any HH/HV backscatter values are inspected. A passing six-plot feature may only advance to a separately preregistered independent validation against the 43 exact mapped AS-BUILT test pits; it must not immediately become a numerical-depth model.
