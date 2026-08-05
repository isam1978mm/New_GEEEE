# ICESat-2 Campaign 006 — Context Review Active

Date: 2026-08-05

Status: ACTIVE CONTEXT REVIEW. Campaign 006 completed its broad scan and mandatory finalization with four context-review survivors. No candidate is a depth anchor, records research remains disabled, and numerical depth remains blocked.

## Authoritative finalizer result

```text
campaign_id                     = southeast_us_earthwork_pilot_v6_central_florida_phosphate
source_spatial_candidate_count  = 5
temporal_recovery_rejected_count = 0
terminal_stability_rejected_count = 0
context_priority_deferred_count = 1
context_review_candidate_count  = 4
surviving_candidate_count       = 4
record_lookup_priority          = []
records_research_ready          = false
status                          = finalized_context_review_candidates_found
```

## Candidate decisions

### Context-review priority 1

```text
campaign_rank       = 1
latitude            = 28.172230911254882
longitude           = -81.81663436889649
median_step_m       = 0.6883673667907715
segment_count       = 5
event_start         = 2022-11-15
event_end           = 2023-08-14
recovery_audit      = pass
terminal_stability  = pass
context_priority    = pass
```

### Context-review priority 2

```text
campaign_rank       = 2
latitude            = 27.215709686279297
longitude           = -81.66138305664063
median_step_m       = 2.7743520736694336
segment_count       = 5
event_start         = 2020-03-20
event_end           = 2020-12-17
recovery_audit      = pass
terminal_stability  = pass
context_priority    = pass
```

### Context-review priority 3

```text
campaign_rank       = 3
latitude            = 27.36371636390686
longitude           = -81.61431884765625
median_step_m       = 1.6717584356665611
segment_count       = 4
event_start         = 2022-03-16
event_end           = 2023-06-13
recovery_audit      = pass
terminal_stability  = pass
context_priority    = pass
```

### Context-review priority 4

```text
campaign_rank       = 4
latitude            = 27.3285915851593
longitude           = -81.6181697845459
median_step_m       = 1.4007323421537876
segment_count       = 4
event_start         = 2022-03-16
event_end           = 2023-06-13
recovery_audit      = pass
terminal_stability  = pass
context_priority    = pass
```

### Deferred candidate

Campaign rank 5 passed recovery and terminal-stability checks but had only three supporting segments. It remains deferred for insufficient spatial support and must not proceed to context or records work.

## Mandatory next gate

For candidate ranks 1 through 4:

1. extract the exact ATL08 dossier and GeoJSON;
2. run the Earth Engine CDL and Dynamic World context audit over the supporting segment line;
3. review imagery and exact parcel/project footprint only after the Earth Engine context output exists;
4. keep records research disabled until a named engineered project, exact footprint, event-window match, and measured placed-material thickness are independently confirmed.

The Earth Engine context audit may classify agricultural, built, bare-ground, mixed, or inconclusive context. None of those classifications proves cause or thickness.

## Protection boundary

This stage does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`;
- Tyrone Route A or Route B records.

No new emails or public-records requests are authorized.
