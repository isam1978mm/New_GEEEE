# Plan B — App-Goal Output Policy

Status: active policy for Plan B follow-up work.

## Purpose

The app goal is not blind byte-for-byte notebook copying.

The app goal is to locally reproduce, preserve, and improve the useful detection behavior from the notebook while keeping sensitive outputs private/local during development.

Notebook parity remains important evidence, but it is not always the final app shape when the app needs a richer local/operator contract.

## Working rule

Use notebook cells as source evidence for algorithms, fields, scoring, and expected behavior.

Use the app contract when the local app needs stronger metadata, privacy markers, pipeline provenance, or downstream compatibility.

Do not patch an app output only to make it look like a notebook output if that would make the app worse for local detection/operation.

## Output status labels

Use these labels in Plan B docs:

```text
Full same-export parity
  The app output was compared against frozen notebook output from the same export/run and passed.

App-port / notebook-current-no-export
  The app emits a useful local/private output, but the current notebook/export does not produce the exact reference file.

App-enhanced local contract
  The app output intentionally combines notebook-derived detection logic with richer app metadata/provenance/privacy fields.
  This is not the same as Full parity unless a frozen notebook reference also exists and comparison passes.

Production-redaction required
  The local app output contains sensitive fields that are acceptable locally now but must be removed/redacted before production/public/API exposure.

Blocked for Full parity
  A real notebook reference output is missing, the exact notebook writer cell is missing, or the available notebook export does not contain the required file.
```

## Privacy rule

During local development, coordinate-bearing and target-bearing outputs may exist as FILESYSTEM_ONLY artifacts.

Before production/public/API exposure, every coordinate-bearing output must be reviewed for redaction/removal. Public artifacts must not expose exact coordinates, raw target geometry, private KMZ/KML/GeoJSON, raw arrays, or private run paths unless explicitly approved.

## #26 decision rule

For `AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson`:

```text
Current app output: exists.
Exact notebook export: not found in the downloaded notebook export.
Exact notebook writer cell for that filename: not found in inspected notebook candidates.
Notebook cell 123 writes AI_FOCUS_17M_TARGETS_V7_2.geojson, not the #26 filename.
App output does not match cell 123 GeoJSON contract exactly.
```

Therefore #26 should not be marked Full same-export parity now.

The next #26 work should be an app-goal design step:

```text
1. Inspect current app #26 GeoJSON schema.
2. Inspect useful notebook semantic fields from cell 123 and related candidate cells.
3. Decide which notebook-derived semantic fields improve the local app output.
4. Patch only after explicit approval.
5. Keep local/private metadata and production-redaction notes.
```

## Development order after closed B1 parity items

```text
Closed in B1:
  #23 Full same-export parity
  #24 Full same-export parity
  #25 Full same-export parity
  #33 app-port / notebook-current-no-export

Next concrete local-app pass:
  #26 app-enhanced local contract: closed
  #27 visualization KMZ/PNG app-enhanced local contract: closed
  #34 field-operation GeoJSON/KMZ app-goal review

Then:
  Phase 2 tensor/raster parity/app-goal review
  Phase 3 gated/replacement parity/app-goal review
```

## #26 app-enhanced local contract example

#26 is the reference example for the app-goal policy.

```text
Output:
AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson

Classification:
App-enhanced local contract
Blocked for Full exact-file parity
Production-redaction required
```

Reason:

```text
The app output is richer than the closest notebook GeoJSON contract and is better for local detection/operator workflow.
It keeps app metadata/classifier context and adds notebook semantic fields where available.
It must not be presented as Full same-export parity because no exact notebook export exists for the app filename.
```


## #27 visualization app-enhanced local contract

For `AI_HEATMAP_CLASSIFICATION.png`, `AI_HEATMAP_CLASSIFICATION.kmz`, and `AI_3D_TARGET_VISUALIZATION.kmz`:

```text
Current app outputs: exist.
Exact notebook exports: not found in the downloaded notebook export.
Notebook writer candidates: cell 139, cell 155, cell 156.
Selected app-goal contract: keep local/private visualization package, validate real PNG/KMZ structure, and keep source/provenance markers.
Full exact-file parity: blocked unless exact notebook refs appear and a private comparison passes.
Production-redaction required: yes, because KML/KMZ visualization outputs are coordinate-bearing.
```

Rule: a `.png` output must be real PNG bytes, not escaped text. KMZ-embedded PNG entries must also start with the PNG signature.
