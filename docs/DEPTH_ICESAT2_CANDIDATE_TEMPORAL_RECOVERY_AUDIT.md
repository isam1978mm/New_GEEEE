# ICESat-2 candidate temporal-recovery audit

Status: second-stage scientific gate before records research.

## Why this gate exists

The broad scanner uses robust medians and NMAD so that one noisy observation
does not destroy a real step. With only three observations on each side,
however, the same robustness can hide a different pattern:

```text
old high level -> temporary low level -> return to old high level
```

That pattern is not the intended:

```text
flat low level -> lasting higher level
```

A candidate showing recovery to an older level is not a defensible direct
placed-thickness anchor. It may represent temporary excavation, restoration,
seasonal or cycle-specific bias, or another temporary disturbance.

## Candidate 001 observation

The five supporting segments all share:

```text
RGT 844
spot 3
pre-cycle 15
post-cycle 16
```

Their per-segment event timestamps differ by milliseconds because neighbouring
ATL08 segments are observed sequentially along the track. Timestamp equality is
therefore not part of event identity.

The dossier shows that the August 2021 observation is closer to the later
2022-2024 plateau than to the immediately pre-event February/May 2022 level.
The five August-2021-to-late-plateau net changes are approximately:

```text
+0.026 m
-0.079 m
+0.393 m
+0.119 m
+0.184 m
```

The median is approximately:

```text
+0.119 m
```

This is much smaller than the scanner's reported cluster median split of:

```text
0.538 m
```

The apparent step is therefore likely dominated by recovery from a temporary
low period rather than a new 0.538 m lasting surface rise.

## Audit rule

For each supporting segment, the audit:

1. reads the oldest usable observation;
2. calculates the median of observations at or after the post cycle;
3. compares the oldest height with the pre and post plateaus;
4. calculates the absolute oldest-to-post net change as a fraction of the
   reported step;
5. marks the segment `recovery_like` when:
   - the oldest observation is closer to the post plateau than the pre plateau;
   - the net change is no more than 50% of the reported step.

The candidate is classified as a recovery pattern when at least 60% of its
supporting segments are recovery-like.

These are diagnostic second-stage rules. They do not change the broad scanner
or manufacture a candidate.

## Files

```text
scripts/audit_icesat2_candidate_temporal_recovery.py
tests/unit/test_icesat2_candidate_temporal_recovery.py
```

## Command

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_candidate_dossier.py -q

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\extract_icesat2_broad_candidate_dossier.py `
  --candidate-rank 1

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\audit_icesat2_candidate_temporal_recovery.py
```

The extractor is rerun so the corrected event-key check is written into the
local dossier.

## Decisive output

Default output:

```text
data/research/icesat2_broad_track_scan/
southwest_us_earthwork_pilot_v1/
candidate_001_temporal_recovery_audit.json
```

Read:

```text
status
recovery_like_segment_count
median_earliest_to_post_net_change_m
median_absolute_net_change_fraction_of_reported_step
decision.direct_thickness_anchor_lookup_recommended
```

## Decision

- `temporary_depression_recovery_pattern`: remove the candidate from direct
  thickness-anchor records research. It may remain only as a possible temporary
  earthwork lead.
- `lasting_rise_not_disproved_by_recovery_audit`: continue parcel and records
  research, while still requiring cause and certified thickness evidence.

## Scientific boundary

The audit does not prove that no earthwork occurred. It does not distinguish
temporary excavation from instrument or seasonal bias. It only determines
whether the ATL08 history supports a new lasting surface rise suitable for the
next thickness-anchor gate.
