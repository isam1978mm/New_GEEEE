# UI-MAP-1 — Large Navigable Real Map Point Picker

Date: 2026-06-08
Status: Implemented target — replace fake picker with large navigable tile map

## Problem

The old Define Target point picker was a blank local grid. It could change latitude and longitude, but it did not show a real map, imagery, roads, terrain, or location context. That made the picker misleading and not useful for selecting a real target.

A small tile preview is also not enough. The operator needs a real map workspace large enough to inspect the area, navigate around, and place a pin by clicking.

## Goal

Replace the fake grid with a large map picker that supports:

- Real XYZ map tiles when external map tiles are enabled.
- Large visible map area.
- Pan controls.
- Zoom controls.
- Click-to-place target pin.
- Latitude/longitude fields updated from the clicked pin.
- Manual latitude/longitude entry still supported.

## Expected User Flow

```text
Open Define Target
→ enable external map tiles in Settings if needed
→ see a large real map
→ pan and zoom to the target area
→ click the map
→ red target pin appears at the selected point
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
- Renders a larger XYZ tile grid around the current map center.
- Adds pan buttons and zoom buttons.
- Computes click position using Web Mercator pixel math.
- Updates latitude and longitude from the clicked map point.
- Shows the red target pin at the selected point.
- Keeps manual latitude/longitude input working and recenters the map when the manual target changes.
- Keeps ROI/Grid preview and Earth Engine dry-run planning unchanged.

## Acceptance Checklist

- [x] Fake blank point grid removed.
- [x] Large real map picker shown when external tiles are enabled and tile template is valid.
- [x] Map can be panned.
- [x] Map can be zoomed.
- [x] Click on map updates latitude and longitude.
- [x] Red pin appears at selected target.
- [x] Manual lat/lon input still works.
- [x] External tiles remain disabled by default.
- [x] Disabled state explains how to enable map tiles.
- [x] No new dependency added.
- [x] No backend code changed.
- [x] No public overlay exposure added.
- [x] No H3/H4 or math changes.

## Closeout

UI-MAP-1 makes the target picker useful for real location selection while preserving the local-first tile privacy boundary.
