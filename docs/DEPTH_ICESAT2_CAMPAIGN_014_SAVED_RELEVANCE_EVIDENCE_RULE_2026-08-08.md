# Campaign 014 Saved Relevance Evidence Rule

Date: 2026-08-08

## Purpose

Campaign 014 remained execution-incomplete because two ATL08 release-007 granules repeatedly produced SlideRule/H5Coro partial-read failures:

- `ATL08_20210504235905_06291102_007_01.h5` — 2021-05-04, RGT 0629
- `ATL08_20251226145703_01873002_007_01.h5` — 2025-12-26, RGT 0187

Independent standalone OpenAltimetry probes were then run before this rule was added.

The broad Campaign-014 track probe saved:

`data/research/icesat2_broad_track_scan/mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork/openaltimetry_track_probe/track_probe_summary.json`

It reported the target RGT present for both dates inside the broad Campaign-014 control bounds.

The exact EPA-envelope probe saved:

`data/research/icesat2_broad_track_scan/mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork/openaltimetry_epa_envelope_probe/epa_envelope_probe_summary.json`

It reported both target RGTs absent from the tight official EPA Hidden Lane envelope.

## Why live proof inside the scanner was rejected

Later long-running recovery attempts queried OpenAltimetry again during resource recovery and received empty track lists for the same broad control bounds. That contradicted the earlier successful standalone probe and made the live service unsuitable as a deterministic completeness gate inside the scanner.

The scanner must not alternate between complete/incomplete solely because an external track lookup is transient during a long run.

## Saved-evidence rule

A failed ATL08 resource may be excluded from Campaign-014 tile completeness only when the two previously saved probe summaries contain exactly one matching row for the same:

- resource filename;
- observation date;
- RGT.

The saved broad-control row must prove all of the following:

- `target_track_present = true`;
- decision = `target_track_intersects_campaign_bounds`;
- the returned track IDs include the target RGT.

The saved exact-EPA-envelope row must prove all of the following:

- `target_track_present = false`;
- decision = `target_track_absent_from_exact_epa_envelope`;
- the returned track IDs do not include the target RGT.

If either saved file is missing, malformed, contradictory, duplicated, or does not contain the exact resource/date/RGT match, the proof fails closed and the resource continues to block the tile.

## Scientific meaning

This is an execution-completeness rule only.

It does not change:

- minimum epochs;
- minimum observations per side;
- step magnitude threshold;
- plateau NMAD threshold;
- dominant-jump requirement;
- neighbour distance;
- minimum neighbouring segments;
- cluster NMAD;
- net/recovery/retention/reversal/follow-up finalizers;
- context step or context event-window gates;
- EPA event-window requirement;
- exact polygon filtering;
- application behavior.

A track absent from the envelope containing the EPA polygon cannot provide a segment inside that EPA polygon. Excluding only such independently proven off-site failed resources therefore does not remove site observations.

## Next action

Run Campaign 014 with the saved-evidence launcher and `--force` so old incomplete caches are not reused.

If both selected tiles complete with zero survivors, Campaign 014 can be closed as a valid zero-candidate campaign. If a resource without exact saved off-site proof fails, Campaign 014 remains incomplete.
