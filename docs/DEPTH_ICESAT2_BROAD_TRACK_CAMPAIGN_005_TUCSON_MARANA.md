# ICESat-2 Broad Track Campaign 005 — Tucson–Marana

Status: CLOSED. Campaign 005 completed successfully on 2026-08-05 with zero spatially supported candidates.

## Final result

```text
campaign_id                    = southwest_us_earthwork_pilot_v5_tucson_marana
completed_tile_count           = 8
failed_tile_count              = 0
quality_segment_count          = 469750
exact_segment_series_count     = 127162
raw_step_up_segment_count      = 3
surviving_step_cluster_count   = 0
surviving_candidate_count      = 0
record_lookup_priority         = []
```

The three raw step-up segments were isolated and were correctly rejected by the unchanged neighbour filter. Because no spatial cluster survived, no temporal-recovery audit, terminal-stability audit, context review, parcel review, or records research is warranted.

Authoritative scan status:

```text
no_surviving_candidates_in_broad_track_campaign
```

## Scientific interpretation

Campaign 005 is a valid negative result. It does not indicate a software failure, and it does not justify weakening any scientific threshold. It produced no depth anchor and did not change app behavior.

## Protection boundary

Campaign 005 did not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`;
- Tyrone Route A or Route B records.

No new emails or public-records requests were created.

## Continuation

The active continuation is Campaign 006:

```text
config/icesat2_broad_track_campaign_v6_central_florida_phosphate.json
docs/DEPTH_ICESAT2_BROAD_TRACK_CAMPAIGN_006_CENTRAL_FLORIDA_PHOSPHATE.md
```
