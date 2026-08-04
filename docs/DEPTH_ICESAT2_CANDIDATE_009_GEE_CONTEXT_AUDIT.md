# ICESat-2 Candidate 009 — Earth Engine Context Audit

Status: implemented on the protected depth branch; local execution is required.

## Purpose

Candidate 009 is the only Campaign 003 candidate that survived:

- temporal-recovery screening;
- immediate and terminal stability screening; and
- context-priority screening.

It remains a context-review candidate only. It is not a depth anchor and records research remains paused.

Candidate summary:

```text
campaign rank = 9
latitude      = 32.76918983459473
longitude     = -115.41337509155274
median rise   = 0.8083953857421875 m
segments      = 5
spatial span  = approximately 200.6 m
event window  = 2021-05-23 through 2022-05-21
```

## Audit added

```text
scripts/audit_icesat2_candidate_gee_context.py
tests/unit/test_icesat2_candidate_gee_context.py
```

The audit is read-only. It uses:

```text
USDA/NASS/CDL
GOOGLE/DYNAMICWORLD/V1
```

The USDA Cropland Data Layer provides annual crop-specific and cultivated/non-cultivated context. Dynamic World provides 10 m class probabilities for crops, built surfaces, bare ground, water, vegetation, and other land-cover classes.

## What the audit checks

The script builds a 60 m buffer around the complete ATL08 supporting line, not only the centroid. It then checks:

1. USDA CDL point class for each event year;
2. cultivated/non-cultivated fraction across the buffered footprint;
3. the dominant crop classes across the buffered footprint;
4. Dynamic World mean class probabilities during:
   - the year before the event window;
   - the event window;
   - the year after the event window.

## Decision statuses

```text
agricultural_context_detected
mixed_agricultural_built_context
engineered_or_built_context_possible
bare_ground_context_detected
context_inconclusive
```

None of these statuses creates a depth anchor or automatically starts records research.

### Agricultural context

If USDA cultivated mapping or Dynamic World crop probability overlaps the supporting line, the site remains unsuitable for direct thickness interpretation unless later evidence identifies a specific engineered project covering the same footprint.

### Built or bare context

Built or bare context only justifies manual imagery and parcel review. It does not prove construction or placed thickness.

## Tests

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_gee_context.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_context_priority.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

## Execution

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\audit_icesat2_candidate_gee_context.py `
  --dossier `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v3_imperial_valley\candidate_009_dossier.json
```

If Earth Engine requires an explicit Cloud project:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\audit_icesat2_candidate_gee_context.py `
  --dossier `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v3_imperial_valley\candidate_009_dossier.json `
  --ee-project YOUR_EARTH_ENGINE_PROJECT
```

Outputs:

```text
candidate_009_gee_context_audit.json
candidate_009_gee_context_audit.geojson
```

## Required interpretation

Even if the result is `engineered_or_built_context_possible`:

```text
records_research_recommended = false
candidate_is_depth_anchor = false
candidate_is_placed_thickness_measurement = false
```

The next gate is exact parcel/project and historical-imagery attribution. Records research can begin only after a named project footprint and activity window match all five supporting segments.

## Protection boundary

This work does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`.
