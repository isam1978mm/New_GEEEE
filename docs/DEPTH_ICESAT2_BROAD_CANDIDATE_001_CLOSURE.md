# ICESat-2 broad Candidate 001 — closure

Status: closed as a direct placed-thickness anchor candidate.

## Candidate

```text
campaign: southwest_us_earthwork_pilot_v1
rank: 1
RGT / spot: 844 / 3
supporting segments: 5
spatial extent: 280.60 m
pre-cycle / post-cycle: 15 / 16
apparent median split: 0.538208 m
cluster step NMAD: 0.124606 m
```

The cluster passed the first-stage spatial screen. Five neighbouring ATL08
terrain segments showed a common cycle-15 to cycle-16 upward transition.

## Corrected event-key check

The first dossier incorrectly reported:

```text
all_segments_share_one_event_key = false
```

because it included exact nanosecond timestamps in the event identity. Adjacent
ATL08 segments are observed sequentially, so their timestamps naturally differ
by milliseconds. The correct event identity is:

```text
RGT = 844
spot = 3
pre-cycle = 15
post-cycle = 16
```

All five segments share that identity.

## Decisive temporal result

The apparent rise is mainly recovery from lower February/May 2022 observations,
not a clean new rise above the oldest available surface.

| Segment | Apparent step (m) | Earliest-to-later net change (m) | Net fraction |
|---|---:|---:|---:|
| 197915 | 1.010193 | +0.026062 | 0.025799 |
| 197925 | 0.538208 | -0.078552 | 0.145951 |
| 197930 | 1.043884 | +0.393127 | 0.376601 |
| 197935 | 0.533508 | +0.118835 | 0.222743 |
| 197940 | 0.454163 | +0.183899 | 0.404919 |

Summary:

```text
recovery-like segments: 5 / 5
recovery-like fraction: 1.0
median earliest-to-later net change: 0.11883544921875 m
median net fraction of apparent step: 0.22274339320443884
```

Each oldest observation is closer to the later plateau than to the immediately
pre-event low plateau. The pattern is therefore:

```text
older higher surface
-> lower observations in February/May 2022
-> return near the older level by August 2022 and later
```

It is not the required clean pattern:

```text
stable lower surface
-> newly placed permanent material
-> stable higher surface
```

## Decision

```text
direct thickness-anchor records lookup: NO
candidate is a depth anchor: NO
numerical depth unblocked: NO
```

Possible causes include temporary excavation followed by restoration,
temporary disturbance, or cycle-specific terrain-height bias. This review does
not establish which cause occurred, and no records search is warranted for a
direct placed-thickness anchor.

## Workflow correction

First-stage broad scan survivors are now provisional. Records research must use
the second-stage finalized output:

```text
scripts/finalize_icesat2_broad_track_candidates.py
```

The finalizer:

1. preserves the original campaign scan summary;
2. builds each candidate dossier;
3. runs the temporal-recovery audit;
4. removes recovery-like candidates from `record_lookup_priority`;
5. writes `campaign_finalized_summary.json`.

Only candidates in the finalized summary may proceed to parcel and as-built
records research.

## Protection boundary

No classifier, frontend, Option 5, production depth output or `main` behavior
was changed.
