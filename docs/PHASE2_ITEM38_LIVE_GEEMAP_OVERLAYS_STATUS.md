# Phase 2 Item #38 ??? Live Geemap Overlays

## Classification

Status: App-native replacement / output proof clean.

This is not Full live notebook parity. The notebook behavior is a live geemap.Map overlay with exact-coordinate marker/buffer/path behavior. The app intentionally replaces that behavior with a private app-native manifest and coordinate-free operator preview boundaries.

## Canonical notebook cell

```text
cell_243 -> live geemap.Map overlay of CNN probability matrix, markers, buffers, and corridor lines
```

## App replacement validated

```text id="6dl9a3"
full_job/focus/APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json
```

Current B1 inspection confirmed:

```text id="uem0nu"
source_cell: cell_243
source_notebook_family: LIVE_GEEMAP_OVERLAY_REPLACEMENT
status: implemented_as_app_native_manifest
artifact exists: true
```

Required layer family was already covered by focused tests:

```text id="hziz9t"
hybrid_basemap
cnn_digital_matrix
detected_target_markers
detected_target_area_buffers
subterranean_corridor_candidates
heatmap_ground_overlay
```

## Guardrails

Do not port geemap.

Do not create public map tiles, public route outputs, public marker layers, public coordinate downloads, or public frontend exposure from this item.

CNN probability and corridor layers remain dependency-gated by later approved #32/#39/#40 outputs.

## Focused tests

```text id="mf9a1x"
tests/unit/test_forbidden_terms.py
tests/unit/test_focus_mask.py
tests/unit/test_full_job_artifact_inventory.py
```

B1 inspection result:

```text id="9w70pf"
4 passed, 3 warnings
```

## Decision

Item #38 is closed as an app-native replacement contract.

Full live notebook parity remains blocked unless a later explicit operator/private overlay approval allows the original live-map behavior under approved gates.
