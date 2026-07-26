# River Road — Radar-Linkage Feasibility Runbook — 2026-07-26

**Branch:** `main`  
**Status:** implementation ready; real query awaiting reviewed private geometry and accepted acquisition dates  
**Scope:** first site in the bounded depth radar-linkage feasibility sequence

```text
site_id = river_road
site_role = known_cover_surface_response
strict_calibration_row = no
numerical_depth_ready = no
app_depth_enabled = false
```

## 1. Honest purpose

Run a multi-date Sentinel-1 comparison between the protected River Road capped surface and a carefully matched nearby comparison area.

This first River Road run can test only whether the known-cover surface has a repeatable radar response. It cannot test a pit-by-pit depth gradient because the 129 accepted pit values and their surveyed location sheet remain unreadable.

## 2. Evidence fixed before analysis

- the PADEP-approved closure was completed in 1987;
- the closure record states a minimum 3-foot final soil cover;
- 129 physical cover-certification pits were excavated;
- pit locations were surveyed and individual thickness records are known to exist;
- deficient areas were corrected and re-certified;
- the site remained inactive and protected by institutional controls;
- the current remedy continues to maintain the cap.

The minimum 3-foot statement is not a point-specific numerical label and must not be converted into a calibration row.

## 3. Private working directory

Use a directory outside the repository, for example:

```text
C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\
```

Required files:

```text
river_road_target.geojson
river_road_comparison.geojson
river_road_acquisition_screen.json
river_road_result.json
```

Do not place these files in Git.

## 4. Target polygon rules

The target polygon must represent only the simple, stable capped surface.

Exclude:

- the uninvestigated southeast knob;
- diversion berms and channels;
- riprap and sedimentation structures;
- leachate and gas infrastructure;
- monitoring wells and probes;
- perimeter and access roads;
- repaired, eroded or maintained patches;
- wooded edges and mixed land-cover pixels;
- any geometry that cannot be supported by a visible source or reviewed imagery.

Do not use the whole 102-acre property. The refuse-disposal/capped area is smaller, and the remaining property includes open areas, drainage and sedimentation features.

## 5. Comparison polygon rules

The comparison polygon is not a confirmed negative.

It must be:

- outside the capped target;
- similar in size, slope, vegetation state and drainage setting;
- free of roads, structures, channels, ponds, riprap and obvious maintenance;
- large enough to contain at least four valid native-resolution pixels;
- fixed for the full matched acquisition series.

If no defensible comparison area can be selected, River Road is inconclusive and the sequence moves to Auburn rather than weakening the rules.

## 6. Acquisition-screen manifest

Create at least two accepted anchor dates. Six or more same-orbit support acquisitions are required across the accepted anchors.

Every accepted anchor must set all four controls to `true`:

```json
{
  "weather_screened": true,
  "vegetation_screened": true,
  "construction_inactive": true,
  "geometry_reviewed": true
}
```

Reject dates affected by:

- recent heavy rainfall or flooding;
- snow or frozen-ground conditions;
- major vegetation mismatch;
- mowing, repairs, inspection work or earth disturbance;
- insufficient valid pixels;
- inconsistent orbit or incidence-angle conditions.

## 7. Dry run

From the repository root in PowerShell:

```powershell
python .\scripts\run_depth_radar_linkage_feasibility_screen.py `
  --site-id river_road `
  --site-role known_cover_surface_response `
  --target-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_target.geojson" `
  --comparison-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_comparison.geojson" `
  --manifest "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_acquisition_screen.json" `
  --analysis-scale-meters 20 `
  --output "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_result.json"
```

Expected dry-run status:

```text
status = site_screen_dry_run_ready
query_executed = false
accepted_anchor_count >= 2
```

## 8. Real Earth Engine run

After the dry run passes and Earth Engine authentication is available, repeat the command with `--execute`:

```powershell
python .\scripts\run_depth_radar_linkage_feasibility_screen.py `
  --site-id river_road `
  --site-role known_cover_surface_response `
  --target-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_target.geojson" `
  --comparison-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_comparison.geojson" `
  --manifest "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_acquisition_screen.json" `
  --analysis-scale-meters 20 `
  --execute `
  --output "C:\Dev\New_GEE_PRIVATE\DEPTH_RADAR_LINKAGE\RIVER_ROAD\river_road_result.json"
```

The terminal output remains redacted. Detailed feature values remain only in the external result file.

## 9. River Road decision rule

Allowed site-level result:

```text
site_surface_response_supported
site_surface_response_not_supported
site_screen_inconclusive
```

Even a supported River Road result means only:

```text
repeatable_known_cover_surface_response = yes
```

It does not mean:

```text
depth_measured = yes
numerical_depth_ready = yes
calibration_record_created = yes
app_depth_enabled = yes
```

## 10. Next site

After River Road is completed or declared inconclusive, continue to Auburn McMaster without changing the features or thresholds. Auburn is the preferred first credible shallow-versus-deeper ordering test if comparable as-built subareas can be recovered.