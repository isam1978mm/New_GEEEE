# Campaign 014 — Off-site failed-resource completeness rule

Date: 2026-08-08

## Status before this rule

Campaign 014 remained execution-incomplete after strict broad SlideRule retries
and per-resource recovery because two ATL08 release-007 resources repeatedly
returned H5Coro read failures:

- `ATL08_20210504235905_06291102_007_01.h5`
- `ATL08_20251226145703_01873002_007_01.h5`

The public NASA OpenAltimetry probes then established:

- both target RGTs intersect the broad Campaign 014 search bounds;
- neither target RGT intersects the tight envelope of the official EPA Hidden
  Lane Landfill polygon;
- the tight EPA envelope is west `-77.42677485999997`, south
  `39.052508687000056`, east `-77.41625001099999`, north
  `39.06693744100005`.

Because the EPA polygon is wholly contained by that envelope, a track absent
from the envelope cannot contribute a segment inside the official EPA polygon.

## New execution-only completeness rule

A failed CMR-listed ATL08 resource may be excluded from Campaign 014 tile
completeness only when an independent OpenAltimetry `getTracks` check proves
both:

1. the exact RGT is present in the current 25 km acquisition tile on the
   resource date; and
2. the same RGT is absent from the exact EPA Hidden Lane envelope on that date.

If either proof is missing, ambiguous, unavailable, or shows the RGT in the EPA
envelope, the resource remains blocking and the tile remains incomplete.

This is not a scientific-threshold exception. It removes only a failed input
that is independently proven incapable of producing any observation inside the
Campaign 014 target polygon.

## Unchanged items

No change is made to:

- minimum distinct epochs;
- observations per side;
- minimum upward step;
- plateau NMAD;
- dominant-jump fraction;
- neighbour distance/count;
- cluster NMAD;
- finalizer thresholds;
- EPA event-window requirement;
- exact segment-in-polygon filtering;
- classifier;
- frontend;
- Option 5;
- Tyrone evidence;
- `main`.

## Required rerun

Run Campaign 014 through
`scripts/run_icesat2_epa_hidden_lane_campaign_014_with_site_relevance_recovery.py`
with `--force` so no earlier partial tile cache can be reused.

If both selected tiles complete, the resulting scientific counts are eligible
for final Campaign 014 interpretation. If any failed resource cannot be proven
off-site by the strict two-part rule, Campaign 014 remains incomplete.
