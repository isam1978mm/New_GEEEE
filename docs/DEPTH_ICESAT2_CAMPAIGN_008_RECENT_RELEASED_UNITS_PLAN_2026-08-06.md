# ICESat-2 Campaign 008 — Recent Released Reclamation Units

Date: 2026-08-06

## Approval

The user explicitly approved a new Campaign 008 with `go` after:

- Candidate 001 and Campaign 007 were closed;
- the Ona HI-3 route produced no event-window activity or thickness evidence;
- the complete Tyrone Route A EMNRD package remained blocked by missing global survey control; and
- no Campaign 008 work had previously been authorized.

## Controlling conclusion

Campaign 008 is approved as a new independent discovery campaign.

It does not modify the app, classifier, frontend, Option 5, Tyrone evidence,
production depth output, or `main`.

Numerical depth remains blocked.

## Why Campaign 008 changes the geometry target

Campaign 007 constrained ATL08 observations to broad active-mine polygons. It
found one finalized candidate inside Ona Mine, but the exact unit was HI-3 with
2021 status `Work Future`, and the 2022–2024 annual records reported zero mining,
disturbance, reclamation, or revegetation in HI-3.

Campaign 008 therefore targets completed units rather than another broad active
mine boundary.

The official FDEP layer used is:

```text
Mandatory Released Phosphate - Reclamation Units
https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/MMP_MANPHO/MapServer/14
```

The layer includes:

- mine operator;
- mine name;
- site ID;
- reclamation-unit name;
- reclamation and release status;
- release year;
- mined and reclaimed acreage; and
- official unit geometry.

FDEP defines a released unit as a unit whose reclamation has been completed and
deemed successful. The GIS is still a conceptual planning layer and is not
engineering-grade evidence. Approved plans, annual reports, surveys, and
certifications remain required for a depth anchor.

## Campaign identity

```text
campaign_id = southeast_us_earthwork_pilot_v8_fdep_recent_released_units
region_id   = fdep_recent_released_phosphate_units
```

Scanner:

```text
scripts/scan_icesat2_fdep_recent_released_units_campaign.py
```

Tests:

```text
tests/unit/test_scan_icesat2_fdep_recent_released_units_campaign.py
```

## Official release-year window

```text
minimum release year = 2019
maximum release year = 2024
```

This window is selected because ICESat-2 ATL08 repeat observations begin in the
late-2018 era. Release year is not treated as the construction date. It is only
a filter that raises the probability that final contouring or reclamation work
occurred within the measurable period.

## Campaign 008 method

Campaign 008:

1. queries the official released-reclamation-unit layer;
2. keeps only polygon features with release years from 2019 through 2024;
3. builds the normal resumable 25 km tile grid;
4. rejects tiles whose WGS84 envelopes do not intersect those official units;
5. queries ATL08 only for retained tiles;
6. deduplicates the returned observations;
7. rejects every ATL08 observation outside the official unit polygons;
8. applies the unchanged repeat-series, step, neighbour, and cluster gates;
9. rejects any cluster whose supporting segments do not all share exactly one
   named released unit; and
10. writes a campaign summary compatible with the existing mandatory finalizer.

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

```text
maximum net fraction             = 0.50
minimum recovery fraction        = 0.60
minimum retention fraction       = 0.50
minimum reversal fraction        = 0.60
minimum follow-up fraction       = 0.60
maximum context step             = 5.0 m
minimum context segment count    = 4
maximum context event window     = 730 days
```

No threshold is weakened.

## Additional Campaign 008 unit gate

A spatial cluster is retained only when every supporting segment shares exactly
one official unit identity:

```text
mine name
site ID
reclamation-unit name
release year
object ID
```

Clusters split across units, outside units, or inside overlapping ambiguous
units are rejected before finalization.

## What a survivor means

A Campaign 008 survivor supports only this statement:

> A persistent terrain-elevation rise was measured along neighbouring ATL08
> segments that all fall inside one official recently released reclamation
> unit.

It does not prove:

- the rise was caused by reclamation;
- the rise equals placed-material thickness;
- the release year equals the construction date;
- a buried-object depth;
- Sentinel-1 radar transferability; or
- a numerical depth calibration row.

## Protection boundary

Campaign 008 does not modify:

- classifier behaviour;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- Tyrone Route A or Route B evidence;
- `main`; or
- any public-record request.

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
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_recent_released_units_campaign.py `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_polygon_campaign.py `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_polygon_campaign_tile_fix.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

Expected focused Campaign 008 tests:

```text
5 passed
```

The combined test count depends on the current protected branch but all listed
tests must pass.

## Scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_fdep_recent_released_units_campaign.py `
  --tile-km 25 `
  --timeout-seconds 30
```

Output directory:

```text
data/research/icesat2_broad_track_scan/
southeast_us_earthwork_pilot_v8_fdep_recent_released_units/
```

The tile cache is resumable. Re-run the same command without `--force` to reuse
successful tile queries.

## Decision after scan

### No unit-constrained spatial candidates

Close Campaign 008. Do not run records research.

### Spatial candidates found

Run the existing mandatory finalizer on the Campaign 008 directory. Only a
finalized context-review survivor may proceed to:

1. Earth Engine land-cover context;
2. exact unit/activity-window confirmation;
3. official annual-report and as-built document review;
4. certified placed-material thickness confirmation; and
5. radar-surface comparability review.

Records research remains disabled until those prior gates identify one exact
unit and a compatible measured event.

## Parallel Tyrone status

Campaign 008 does not replace Route A.

Tyrone Test Plots 5 and 6 retain supported measured as-built depths and local
as-built footprints, but usable calibration rows remain zero until an external
coordinate transformation or equivalent survey control is obtained.
