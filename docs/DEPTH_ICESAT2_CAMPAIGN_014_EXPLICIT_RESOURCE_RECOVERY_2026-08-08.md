# Campaign 014 — Explicit ATL08 Resource Recovery

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: EXECUTION RECOVERY IMPLEMENTED / SCIENTIFIC RESULT STILL OPEN

## Why this recovery is required

Campaign 014 targets the EPA Hidden Lane Landfill OU3 recent-earthwork window.
The first broad SlideRule ATL08 run returned apparent data but emitted H5Coro
resource-read failures. A strict rerun correctly converted those partial reads
into failed tiles. Three independent broad-query attempts per tile still failed.

The affected resources included multiple pre-event granules, especially:

- `ATL08_20210504235905_06291102_007_01.h5`

The 2021 granule repeatedly failed across all six beams on one selected tile.
Because the earlier retained series were classified as `insufficient_epochs`, a
missing pre-event observation can affect whether the repeat-series gate passes.
The broad-query zero-candidate result therefore cannot be accepted.

## Recovery method

SlideRule supports two relevant operations:

1. NASA CMR lookup of resources intersecting a polygon/time range; and
2. explicit processing of named resources.

Campaign 014 now uses those operations only after all three normal broad-query
attempts remain partial.

For each selected tile:

1. query CMR for every `ATL08` release `007` resource intersecting the same tile
   polygon and the unchanged campaign time range;
2. de-duplicate the returned resource names without changing order;
3. process each named ATL08 granule individually through `atl08x` with the same
   tile polygon;
4. give each resource up to three isolated attempts;
5. reject any attempt that reports `H5Coro::Future read failure` or
   `Failure on resource`;
6. combine the clean per-resource frames only when every CMR-listed resource
   has been recovered cleanly;
7. fail the tile if even one CMR-listed resource remains unreadable.

This prevents a missing resource or epoch from being silently dropped.

## Scientific scope unchanged

This is an execution-integrity recovery only. It does not change:

- minimum distinct epochs;
- minimum observations per side;
- minimum upward step;
- plateau NMAD threshold;
- dominant-jump threshold;
- neighbour distance or neighbour-count requirements;
- cluster step NMAD;
- cross-spot support;
- mandatory finalizer;
- context / terminal-stability / temporal-recovery gates;
- official EPA Hidden Lane polygon;
- OU3 2023-09-11 through 2025-11-06 event-window gate;
- records evidence requirements;
- application behavior.

No resource may be excluded merely because it is difficult to read. A tile is
scientifically complete only when every CMR-listed ATL08 release-007 resource
for that tile/time range is recovered cleanly.

## Decision rule

### Explicit-resource recovery succeeds for all selected tiles

Use the rebuilt tile caches and evaluate Campaign 014 normally. Only then may a
zero-candidate result be considered scientifically complete.

### One or more named resources remain unreadable

Campaign 014 remains incomplete. Do not rerun the same broad request again and
do not weaken any scientific threshold. The next recovery route must use an
independent access method for the exact unresolved resource(s), or close the
route explicitly as an unrecoverable data-access limitation rather than as zero
scientific candidates.

## Protected areas

No classifier, frontend, Option 5, Tyrone Route A, or `main` changes are part of
this recovery.
