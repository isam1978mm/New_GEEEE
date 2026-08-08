# Campaign 014 — OpenAltimetry No-Account Probe

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: IMPLEMENTED / LOCAL LIVE PROBE REQUIRED

## Why this exists

Campaign 014 remains incomplete because SlideRule repeatedly returns partial reads for two ATL08 release-007 granules:

- `ATL08_20210504235905_06291102_007_01.h5`
- `ATL08_20251226145703_01873002_007_01.h5`

The direct NASA/NSIDC HDF5 fallback requires NASA Earthdata Login credentials. The operator had not previously been asked to create an Earthdata account, so that route must not be assumed.

## No-account recovery source

NASA/NSIDC OpenAltimetry currently exposes a public ICESat-2 API. The official OpenAPI definition identifies:

- endpoint: `/api/icesat2/{product}`
- ATL08 as a supported product;
- required parameters: date, spatial bounding box, and track ID;
- output formats including JSON and CSV;
- a maximum 5 degree x 5 degree request box.

NSIDC describes OpenAltimetry as freely accessible and usable without special software.

## Exact Campaign 014 probe

The probe uses the locked Campaign 014 discovery bounds:

- west: -77.70
- south: 38.80
- east: -77.10
- north: 39.20

It queries exactly:

1. `2021-05-04`, RGT `0629`, corresponding to `ATL08_20210504235905_06291102_007_01.h5`;
2. `2025-12-26`, RGT `0187`, corresponding to `ATL08_20251226145703_01873002_007_01.h5`.

The helper stores the raw OpenAltimetry response and a small response-shape summary. It deliberately does not guess the response schema before a live response is observed.

## Scientific integrity

This probe changes no scientific threshold and does not alter:

- the EPA Hidden Lane polygon gate;
- the documented 2023-09-11 through 2025-11-06 OU3 event window;
- repeat-series thresholds;
- neighbour/cluster thresholds;
- finalizer, terminal-stability, temporal-recovery, context, or evidence gates;
- classifier behavior;
- frontend behavior;
- Option 5;
- Tyrone Route A;
- `main`.

OpenAltimetry data cannot silently replace an unresolved granule. A later parser/fallback may be implemented only after the live response confirms that the public service returns the needed ATL08 observations for the exact date/RGT.

## Decision rule

- If both public API calls return usable ATL08 data, implement and test a Campaign-014-only OpenAltimetry frame adapter and rerun Campaign 014 without Earthdata credentials.
- If one of the two exact date/RGT responses is unavailable, record that source limitation and choose a different recovery path; do not fabricate or drop the missing epoch.
