# Plan B1 #27 — App-Enhanced Visualization Status

Status: App-enhanced local visualization contract.

This item is not Full exact-file parity.

## Outputs

```text
AI_HEATMAP_CLASSIFICATION.png
AI_HEATMAP_CLASSIFICATION.kmz
AI_3D_TARGET_VISUALIZATION.kmz
```

## Notebook evidence

The downloaded notebook export did not contain the exact #27 files.

Candidate writer cells were found:

```text
cell 139: exact hits for all three #27 output names; uses files/AI_HEATMAP_CLASSIFICATION.png inside KMZ.
cell 155: exact hits for all three #27 output names; uses heat.png inside KMZ.
cell 156: exact hits for all three #27 output names; simplekml/temp-file implementation.
```

The app-goal contract keeps the local/private visualization package and follows the cell-155-style KMZ shape where the heatmap KMZ contains `doc.kml` and `heat.png`.

## App-goal decision

```text
Use app-enhanced local contract.
Do not patch blindly for byte parity.
Do not mark Full exact-file parity until exact notebook refs appear and private comparison passes.
Require production-redaction review before public/API exposure.
```

## Validation

Before the #27 fix, old and fresh app outputs proved the heatmap PNG bytes were escaped text instead of real PNG bytes.

After the fix:

```text
PASS_PNG_SIGNATURE=True
PASS_KMZ_SIGNATURE=True
PASS_KMZ_INNER_PNG_SIGNATURE=True
PASS_3D_KMZ_SIGNATURE=True
```

Fresh validated package details:

```text
AI_HEATMAP_CLASSIFICATION.png:
  real PNG signature
  640x640 RGBA

AI_HEATMAP_CLASSIFICATION.kmz:
  ZIP/KMZ signature valid
  contains doc.kml
  contains heat.png
  embedded heat.png has real PNG signature
  KML contains GroundOverlay and LatLonBox

AI_3D_TARGET_VISUALIZATION.kmz:
  ZIP/KMZ signature valid
  contains doc.kml
  KML contains 5 Placemark entries
  KML uses relativeToGround altitude mode
```

## Privacy

```text
Artifact class: FILESYSTEM_ONLY
HTTP servable: false
Production-redaction required: true
Reason: KML/KMZ visualization outputs are coordinate-bearing.
```
