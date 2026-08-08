# Campaign 014 — Direct NASA/NSIDC ATL08 Recovery

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: IMPLEMENTED / LOCAL VALIDATION AND EARTHDATA DOWNLOAD NEXT

## Why this recovery exists

Campaign 014 targets the EPA Hidden Lane Landfill OU3 recent-earthwork window.
The scientific scan remains incomplete because SlideRule repeatedly returns
partial H5Coro reads for two ATL08 release-007 granules even after:

1. three broad tile retries; and
2. three explicit one-resource-at-a-time retries per granule.

The unresolved unique resources are:

- `ATL08_20210504235905_06291102_007_01.h5` — pre-earthwork baseline;
- `ATL08_20251226145703_01873002_007_01.h5` — post-OU3 follow-up.

All other CMR-listed resources recovered through the strict SlideRule route.

## Independent source path

The fallback uses NASA `earthaccess` to search for and download the two exact
ATL08 Version 7 HDF5 files from NASA/NSIDC. NASA Earthdata Login is required for
the protected data download. Credentials are entered only in the user's local
terminal if `earthaccess` prompts; credentials are not stored in the repository
or requested in chat.

The files are cached under:

`data/research/icesat2_broad_track_scan/mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork/nsidc_direct_atl08/`

The cache is campaign output and is not committed to the protected branch.

## Local HDF5 reader

`scripts/recover_campaign_014_nsidc_atl08.py` reads the official 100 m
`gt[x]/land_segments` data needed by the existing repeat-series parser:

- `delta_time`;
- `latitude` / `longitude`;
- `segment_id_beg`;
- `segment_snowcover` when available;
- `terrain/h_te_median`;
- `terrain/h_te_uncertainty` when available;
- `terrain/n_te_photons` when available;
- `terrain/terrain_slope` when available.

RGT, cycle, and region are decoded from the standard ATL08 filename. The ATLAS
spot number is read from the official ground-track-group `atlas_spot_number`
attribute; the recovery code does not guess spacecraft-orientation mapping.

The local reader filters rows to the same 25 km tile bounding polygon before
returning the DataFrame. The normal exact EPA Hidden Lane polygon filter remains
downstream and unchanged.

## Strict completeness rule

`scripts/run_icesat2_epa_hidden_lane_campaign_014_with_nsidc_fallback.py` keeps
the existing execution order:

1. three broad SlideRule attempts;
2. explicit CMR resource enumeration;
3. up to three SlideRule attempts for every named resource;
4. only for the two already-proven unresolved resources, substitute a cached
   direct NASA/NSIDC HDF5 frame if SlideRule still fails.

Every CMR-listed resource must still be represented. An unknown failed resource
is never silently ignored or replaced. If either direct HDF5 file is missing,
unreadable, or structurally invalid, Campaign 014 remains incomplete.

## Scientific rules unchanged

This recovery does not change:

- minimum distinct epochs;
- observations per side;
- 0.30 m minimum upward step;
- plateau NMAD;
- dominant-jump fraction;
- 250 m neighbour rule;
- minimum neighbouring segments;
- cluster NMAD;
- context/finalizer/terminal-stability/recovery gates;
- EPA Hidden Lane polygon gate;
- OU3 2023-09-11 through 2025-11-06 event-window gate.

It also does not modify classifier, frontend, Option 5, Tyrone Route A, or
`main`.

## Decision after direct recovery

- If both direct files validate and both selected tiles complete with zero
  failed tiles, use the rebuilt Campaign 014 scientific result.
- If any CMR-listed resource remains unresolved after direct recovery, keep
  Campaign 014 incomplete and document the exact unresolved official file.
- A zero-candidate result is valid only after both selected tiles are complete.
