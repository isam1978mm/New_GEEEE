# Plan C — Full UI Implementation For Notebook-Capability App

Status: planning document.

Goal: after Plan A and Plan B define and implement the missing backend outputs, build the UI flow that lets an operator run the app like the notebook purpose: choose a point, run notebook-equivalent phases, monitor progress, inspect QA, review targets, and export allowed outputs.

Plan C is the UI/API wiring plan. It does not replace Plan A or Plan B. The UI can only show features after the backend app stages and output contracts exist.

## Scope

Plan C includes:

```text
app screens
operator flow
API contracts needed by the UI
stage checklist display
artifact/output browser
QA/report display
target table
map layers
private/local export controls
error/retry states
```

Plan C does not include:

```text
porting missing notebook formulas
building classifier logic
training models
validating raster parity
creating frozen notebook references
```

Those belong to Plan A and Plan B.

## UI principle

```text
The UI should expose notebook capability through app-native screens.
It should not copy Colab, geemap widgets, Drive folder browsing, or manual notebook execution behavior.
```

## Expected operator flow

```text
1. Open app.
2. Choose or enter location.
3. Confirm ROI/grid/run options.
4. Start run.
5. Watch stage progress.
6. Review QA gates.
7. Review core outputs and stacks.
8. Review focus-analysis and target outputs when available.
9. Review map layers and target table.
10. Export allowed outputs.
11. Keep private/internal outputs local unless explicitly allowed.
```

## Plan C screen list

| # | Screen / UI area | Purpose | Depends on |
|---:|---|---|---|
| C1 | Run start screen | Enter coordinates or pick point; choose run options. | Existing run-create API plus Plan A map/ROI completion. |
| C2 | ROI/grid confirmation | Show ROI size, grid size, CRS, resolution, and safe summary before run. | Grid contract from backend. |
| C3 | Run progress screen | Show current stage, completed stages, failed stages, and timestamps. | Run status API and stage manifests. |
| C4 | Stage checklist | Show notebook-equivalent phase checklist: core, Plan A, Plan B, exports. | Backend stage registry. |
| C5 | QA dashboard | Show zero-shift, alignment, nodata, geometry, reference comparison, and report status. | Plan A QA outputs. |
| C6 | Artifact browser | List allowed artifacts by category: public-safe, local/private, filesystem-only. | Artifact API and artifact classes. |
| C7 | Raster/tensor summary view | Show band names, shapes, basic stats, and validation status without exposing sensitive raw arrays. | Stack/report summaries. |
| C8 | Focus analysis screen | Show focus mask/window status, focus stats, and target-analysis inputs/outputs. | Plan A focus completion and Plan B focus analysis. |
| C9 | Target table | Show detected/classified targets, labels, confidence/score, status, and export availability. | Plan B target schema. |
| C10 | Map layers screen | Show safe map overlays: ROI, focus area, heatmap, target markers, probability layer when allowed. | Plan B map/KMZ/probability outputs. |
| C11 | Export center | Download allowed CSV/JSON/GeoJSON/KMZ/report files. | Output privacy policy and guarded artifact route. |
| C12 | Error/retry screen | Show safe failure reason, failed stage, retry/resume options. | Backend run status and error policy. |
| C13 | Admin/debug local-only view | Local operator-only file paths, private reports, and diagnostics if enabled. | Local-only mode flag; never public by default. |

## Plan C execution order

### C1 — Run input and map picker

```text
Build:
  coordinate input
  app-native map point picker
  ROI/grid preview
  start-run button

Outcome:
  operator can start the same kind of run the notebook starts from SelectedPoint, without Colab/geemap.
```

### C2 — Stage progress and checklist

```text
Build:
  stage timeline
  current stage panel
  completed/failed stage list
  notebook-phase coverage labels

Outcome:
  operator can see whether the run reached core, Plan A, Plan B, and export phases.
```

### C3 — QA dashboard

```text
Build:
  zero-shift status
  pixel alignment status
  geometry consistency status
  nodata/audit status
  reference comparison status

Outcome:
  operator can trust or reject outputs before looking at target results.
```

### C4 — Artifact browser and export center

```text
Build:
  grouped artifact list
  artifact class badges
  guarded download buttons
  hidden/disabled state for private or filesystem-only artifacts

Outcome:
  operator can download allowed outputs and understand why private outputs are not served.
```

### C5 — Stack and tensor summary views

```text
Build:
  band list
  shape/dtype/stat summaries
  validation badges
  no raw array serving by default

Outcome:
  operator can inspect AI-ready and tensor products without unsafe raw payload exposure.
```

### C6 — Focus-analysis screen

```text
Build:
  focus-mask status
  focus-window summary
  focus-band summary
  focus-analysis result placeholder/output panel

Outcome:
  operator can see the 17m focus workflow once Plan A/B backend outputs exist.
```

### C7 — Target results screen

```text
Build:
  target table
  target labels
  confidence/score fields
  source phase
  export buttons for allowed target artifacts

Outcome:
  operator can inspect classifier/AI target outputs after Plan B detection logic exists.
```

### C8 — Map layers and visual outputs

```text
Build:
  ROI layer
  focus-area layer
  heatmap/probability layer
  target marker layer
  layer toggles
  safe coordinate/geometry display policy

Outcome:
  app replaces live geemap overlays with app-native map layers.
```

### C9 — KMZ/GeoJSON handling

```text
Build:
  local/private export indicators
  guarded download policy
  redacted/public mode only if explicitly designed

Outcome:
  app can expose notebook-style GeoJSON/KMZ products safely.
```

### C10 — Training and model management UI, only if approved

```text
Build:
  separate training page or admin-only workflow
  model registry/status
  selected model/version display
  inference input contract display

Outcome:
  training remains separate from normal run execution.
```

## Required API/UI contracts

Before UI implementation, define these contracts:

```text
POST /runs
GET /runs/{run_id}
GET /runs/{run_id}/stages
GET /runs/{run_id}/artifacts
GET /runs/{run_id}/qa
GET /runs/{run_id}/stacks
GET /runs/{run_id}/focus
GET /runs/{run_id}/targets
GET /runs/{run_id}/map-layers
GET /runs/{run_id}/artifacts/{artifact_name}
```

The exact routes can differ, but the UI needs these data groups.

## UI output visibility policy

```text
Public-safe:
  run status
  stage status
  redacted summaries
  safe CSV/JSON reports

Local/private by default:
  exact target geometry
  raw target GeoJSON
  KMZ files
  probability rasters
  raw NPY tensors
  internal QA manifests
  coordinate-bearing diagnostics

Filesystem-only:
  raw rasters and arrays unless explicitly promoted
  private classifier outputs unless redacted
```

## Definition of done for Plan C

```text
[x] run can be started from coordinate input or map picker
[x] ROI/grid confirmation is shown before run
[x] run progress and stage checklist work
[x] QA dashboard shows Plan A/Plan B validation status
[x] artifact browser lists outputs by class
[x] allowed downloads work through guarded API only
[x] focus-analysis screen works when backend outputs exist
[x] target table works when target outputs exist
[x] map layers work with app-native map UI
[x] private/local outputs are not exposed accidentally
[x] UI tests or integration checks cover the main flow
```

## Dependencies on Plan A and Plan B

```text
Plan A must provide:
  completed partial backend outputs, QA reports, focus scaffolding, and target-output containers.

Plan B must provide:
  classifier/AI outputs, target schema, GeoJSON/KMZ/probability outputs, and ML/tensor contracts.

Plan C then wires those outputs into the UI.
```

## Bottom line

```text
Plan C is required.
The final product is not complete just because backend outputs exist.
The UI must let the operator run, monitor, inspect, and export notebook-equivalent results through app-native screens.
```
