# UI-MAP-1 — Real Map Point Picker

Date: 2026-06-08
Status: Implemented target — replace fake picker with real tile-based point picker

## Problem

The old Define Target point picker was a blank local grid. It could change latitude and longitude, but it did not show a real map, imagery, roads, terrain, or location context. That made the picker misleading and not useful for selecting a real target.

## Goal

Replace the fake grid with a real map-style point picker that lets the operator click a visible tile map to set the target pin.

## Expected User Flow

```text
Open Define Target
→ see manual Latitude / Longitude inputs
→ see a real map when external map tiles are enabled
→ click the map
→ red target pin recenters on the clicked location
→ Latitude / Longitude update
→ queue/preview uses that point
```

## Safety Boundary

This work is UI-only and target-picking only.

It does not:

- Add public overlay exposure.
- Display private coordinates from outputs.
- Display private artifact geometry.
- Add H3/H4 training or inference.
- Change SAR/GRID/screening math.
- Change backend auth behavior.
- Add provider auth, Supabase, or VPS deployment.
- Add frontend dependencies.

## Tile Privacy Model

The app remains local-first. External map tiles are disabled by default in Settings.

When external tiles are disabled, the picker shows a clear disabled message and keeps manual latitude/longitude input available.

When external tiles are enabled, the browser may request tiles from the configured tile URL template. This is an operator choice controlled by Settings.

## Implementation Summary

- Removes the fake local grid picker.
- Uses the existing `externalTilesEnabled` and `tileUrlTemplate` settings.
- Renders a 3x3 XYZ tile grid around the current target center.
- Computes click position using Web Mercator pixel math.
- Updates latitude and longitude from the clicked map point.
- Keeps the red target marker centered on the selected point.
- Keeps manual latitude/longitude input working.
- Keeps ROI/Grid preview and Earth Engine dry-run planning unchanged.

## Acceptance Checklist

- [x] Fake blank point grid removed.
- [x] Real map picker shown when external tiles are enabled and tile template is valid.
- [x] Click on map updates latitude and longitude.
- [x] Marker recenters after click.
- [x] Manual lat/lon input still works.
- [x] External tiles remain disabled by default.
- [x] Disabled state explains how to enable map tiles.
- [x] No new dependency added.
- [x] No backend code changed.
- [x] No public overlay exposure added.
- [x] No H3/H4 or math changes.

## Closeout

UI-MAP-1 makes the target picker useful for real location selection while preserving the local-first tile privacy boundary.
