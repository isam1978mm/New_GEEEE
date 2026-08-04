# ICESat-2 Broad Track Campaign 002 — Phoenix Closure

Status: closed with no spatially supported terrain-step candidates.

## Decisive result

Campaign:

```text
southwest_us_earthwork_pilot_v2_phoenix
```

Region:

```text
west_phoenix_lower_gila_pilot
```

Observed result:

```text
tile_count                         = 25
completed_tile_count               = 25
failed_tile_count                  = 0
quality_segment_count              = 1,156,206
exact_segment_series_count         = 293,862
raw_step_up_segment_count          = 25
surviving_step_cluster_count       = 0
record_lookup_priority             = []
status                             = no_surviving_candidates_in_broad_track_campaign
```

The SlideRule/H5Coro alerts did not create failed tiles. All 25 tiles completed.

## Scientific interpretation

Twenty-five exact segment histories passed the single-series step-up screen, but none had the required neighbouring support under the unchanged rules:

```text
minimum upward step              = 0.30 m
neighbour connection distance    = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
```

Therefore the raw segments remain isolated observations. They do not justify candidate dossiers, temporal-recovery audits, parcel research, permit research, or as-built record requests.

## Decision

Campaign 002 is closed.

```text
spatial candidate found          = no
final candidate found            = no
records research warranted       = no
usable thickness anchor          = no
numerical depth unblocked        = no
```

Do not lower the neighbour threshold to manufacture a candidate.

## Next route

Proceed to a new independent broad campaign. Campaign 003 uses a separate configuration and output directory so Campaigns 001 and 002 remain preserved as audit trails.

The controlling order remains:

```text
broad scan
-> spatial cluster gate
-> temporal-recovery finalizer
-> records research only for finalized survivors
```

## Protection boundary

No classifier, frontend, Option 5, production depth output, or `main` change is authorized by this closure.
