# Campaign 003 terminal-stability correction

## Decision

The first Campaign 003 finalization is superseded for records decisions.

The temporal-recovery gate correctly removed nine spatial candidates, but it did
not test whether a surviving rise later returned toward the pre-event surface.
The extracted dossiers exposed four false survivors:

- source rank 1: the 2022 rise persisted through July 2025, then all 21
  supporting segments dropped sharply in January 2026;
- source rank 6: the 2024 rise persisted through July 2025, then all seven
  supporting segments returned toward or below the pre-event level in January
  2026;
- source rank 12: most of the May 2022 rise reversed at the immediately next
  independent cycle in August 2022;
- source rank 15: the same event family as rank 1, with a large January 2026
  reversal across all three supporting segments.

These candidates are not eligible for records research as lasting placed-
thickness candidates.

## Remaining context-review candidate

Source rank 9 remains the only Campaign 003 candidate that is not disproved by
the available temporal evidence.

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

The finalizer now applies two independent temporal gates:

1. **Temporal-recovery gate**
   - rejects a rise that is mainly recovery from an older high surface.

2. **Terminal-stability gate**
   - rejects candidates when at least 60% of supporting segments lose more than
     half of the reported rise at the first later independent epoch;
   - rejects candidates when at least 60% of supporting segments lose more than
     half of the rise by the latest available independent epoch;
   - withholds candidates when fewer than 60% of segments have any later
     independent follow-up.

The thresholds are conservative screening rules. Passing them does not confirm
earthwork or thickness.

## Expected Campaign 003 rerun result

After rerunning the corrected finalizer:

- source spatial candidates: 19;
- temporal-recovery rejections: 9;
- terminal-stability rejections among the previous temporal survivors: 4;
- expected records-context shortlist: source rank 9 only;
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
records decisions.

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
