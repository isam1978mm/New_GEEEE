# Campaign 003 temporal and context-priority correction

## Decision

The first Campaign 003 finalization is superseded for all context and records
decisions.

The temporal-recovery gate correctly removed nine spatial candidates, but it did
not test whether a surviving rise later returned toward the pre-event surface.
The extracted dossiers exposed four additional false survivors:

- source rank 1: the 2022 rise persisted through July 2025, then all 21
  supporting segments dropped sharply in January 2026;
- source rank 6: the 2024 rise persisted through July 2025, then all seven
  supporting segments returned toward or below the pre-event level in January
  2026;
- source rank 12: most of the May 2022 rise reversed at the immediately next
  independent cycle in August 2022;
- source rank 15: the same event family as rank 1, with a large January 2026
  reversal across all three supporting segments.

These candidates are not eligible for context or records research as lasting
placed-thickness candidates.

The remaining high-magnitude and weak-support temporal survivors also require a
separate context-priority gate before any land or parcel review:

- source ranks 3, 8, 11, and 13 are deferred because their reported rises are
  about 9 m to 62 m, above the conservative 5 m direct-context threshold;
- source rank 19 is deferred because it has only three supporting segments and
  an event window spanning nearly four years.

A deferral does not mean the apparent rise is impossible or invalid. It means it
is not an efficient or defensible direct placed-thickness context target without
independent evidence first.

## Remaining context-review candidate

Source rank 9 is the only Campaign 003 candidate that passes the three screening
stages and remains suitable for exact land, water, parcel, surface, and activity
context review.

Its dossier shows:

- five neighboring ATL08 segments;
- a median reported rise of about 0.808 m;
- segment rises from about 0.625 m to 0.871 m;
- pre-event observations in February and May 2021;
- the higher surface observed in May 2022;
- the higher surface retained in August 2024;
- no later reversal available in the dossier.

This is still not a depth anchor. Its cause, exact footprint, construction
history, placed thickness, surface comparability, and transfer beyond the laser
strip remain unconfirmed.

## Software correction

The finalizer now applies three independent stages:

1. **Temporal-recovery gate**
   - rejects a rise that is mainly recovery from an older high surface.

2. **Terminal-stability gate**
   - rejects candidates when at least 60% of supporting segments lose more than
     half of the rise at the first later independent epoch;
   - rejects candidates when at least 60% of supporting segments lose more than
     half of the rise by the latest available independent epoch;
   - withholds candidates when fewer than 60% of segments have any later
     independent follow-up.

3. **Context-priority gate**
   - defers reported rises above 5 m from direct context review;
   - requires at least four supporting segments;
   - defers event windows longer than 730 days.

These thresholds are conservative screening rules. Passing them does not
confirm earthwork, placed thickness, buried-object depth, or radar
transferability.

## Expected Campaign 003 rerun result

After rerunning the corrected finalizer:

- source spatial candidates: 19;
- temporal-recovery rejections: 9;
- terminal-stability rejections: 4;
- context-priority deferrals: 5;
- context-review candidates: 1;
- expected context-review source rank: 9;
- record lookup priority: empty;
- records research ready: no;
- usable depth anchors: 0;
- numerical depth unlocked: no.

## Required command

Run from the main worktree after pulling the safe branch:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v3_imperial_valley
```

Use only the regenerated `campaign_finalized_summary.json` for subsequent
context decisions. Its `record_lookup_priority` must remain empty until rank 9
passes exact land/parcel and activity-context review.

## Scope

This correction does not:

- change the classifier;
- change Option 5;
- change the frontend;
- change production app behavior;
- create a calibration row;
- create a depth anchor;
- start records research;
- merge or publish to `main`.
