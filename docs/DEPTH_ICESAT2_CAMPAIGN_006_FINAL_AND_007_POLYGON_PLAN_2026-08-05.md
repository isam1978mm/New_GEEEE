# ICESat-2 Campaign 006 Final Decision and Campaign 007 Polygon-Constrained Plan

Date: 2026-08-05

## Campaign 006 final decision

Campaign 006 completed every approved stage:

```text
scan tiles completed              = 15 / 15
failed tile count                 = 0
spatial candidates                = 5
final context-review candidates   = 4
Earth Engine context audits       = 4
FDEP footprint survivors          = 0
records research ready            = false
numerical depth unlocked          = false
```

The official FDEP point-by-point audit checked every supporting ATL08 segment for Candidates 001 through 004 against:

1. Mandatory Phosphate 2021 active mine boundaries;
2. Mandatory Released Phosphate mine boundaries; and
3. Mandatory Released Phosphate reclamation units.

Every candidate had:

```text
matched_point_count = 0
manual_footprint_review_survives = false
```

Therefore Campaign 006 is closed. Its candidates are valid persistent terrain-step observations, but they are not inside the official phosphate footprints that motivated the campaign. They must not proceed to records research or depth calibration.

## Why another broad rectangle is not approved

Campaign 006 demonstrated that a broad geographic box can find strong persistent terrain steps outside the intended regulated facilities. Repeating another blind rectangular scan would risk spending most of the query and review effort on unrelated land.

The next campaign changes the selection method rather than weakening any scientific gate.

## Campaign 007 identity

```text
campaign_id = southeast_us_earthwork_pilot_v7_fdep_active_mines
region_id   = fdep_active_mandatory_phosphate_mines
```

Scanner:

```text
scripts/scan_icesat2_fdep_polygon_campaign.py
```

Tests:

```text
tests/unit/test_scan_icesat2_fdep_polygon_campaign.py
```

## Campaign 007 method

Campaign 007:

1. downloads official FDEP 2021 active mandatory phosphate mine polygons inside the Campaign 006 Central Florida envelope;
2. creates the same 25 km resumable tile grid;
3. rejects tiles whose WGS84 envelopes do not intersect any official mine polygon;
4. queries ATL08 only for retained tiles;
5. deduplicates the returned observations;
6. rejects every ATL08 segment outside the official mine polygons;
7. applies the unchanged repeat-series, step, neighbour, and cluster gates; and
8. writes a campaign summary compatible with the existing mandatory finalizer.

Every retained ATL08 observation is therefore inside an official active-mine polygon before candidate classification.

## Unchanged scientific gates

```text
minimum distinct epochs          = 4
minimum observations per side    = 2
minimum upward step              = 0.30 m
maximum plateau NMAD             = 0.25 m
minimum dominant-jump fraction   = 0.60
neighbour connection distance    = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
cross-spot diagnostic distance   = 500 m
```

The mandatory finalizer remains unchanged:

1. temporal-recovery audit;
2. immediate and terminal stability audit;
3. context-priority audit with the 5 m ceiling;
4. land-cover/manual context review;
5. exact reclamation-unit or project-footprint review;
6. certified placed-material thickness evidence.

A polygon-constrained spatial candidate is not a depth anchor.

## Protection boundary

Campaign 007 does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`;
- Tyrone Route A or Route B records.

No new email or public-records request is authorized.

Always keep:

```text
records_research_ready = false
numerical_depth_unlocked = false
candidate_is_depth_anchor = false
```

until all later evidence gates are independently satisfied.

## Validation command

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_polygon_campaign.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

## Scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_fdep_polygon_campaign.py `
  --tile-km 25 `
  --timeout-seconds 30
```

The output directory is:

```text
data/research/icesat2_broad_track_scan/
southeast_us_earthwork_pilot_v7_fdep_active_mines/
```

The tile cache is resumable. Re-run the same command without `--force` to reuse successful tile queries.

## Decision after scan

### No polygon-constrained spatial candidates

Close Campaign 007. Do not run records research.

### Spatial candidates found

Run the existing mandatory finalizer on the Campaign 007 directory. Only finalized context-review survivors may proceed to Earth Engine and exact reclamation-unit review. Keep records research disabled until a named unit, activity window, exact ATL08 overlap, and certified placed thickness are documented.
