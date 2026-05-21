# Notebook Full-Job Inventory

## Purpose

This document records the notebook full-job work products described in [Notebook_Cells_E.md](Notebook_Cells_E.md) and classifies which outputs the app must eventually reproduce.

Corrected project interpretation:

The app must eventually reproduce the notebook's full job work products where applicable, not only reduced core production artifacts.

This is an inventory and classification record only. It does not authorize implementation, `plan.md` changes, public exposure, or notebook edits.

## Source

Source inventory:

- [Notebook_Cells_E.md](Notebook_Cells_E.md)

Classification codes used below:

- `A` — reproduce as app artifact
- `B` — reproduce as internal QA artifact
- `C` — console/map-only, no app artifact equivalent
- `D` — out-of-scope until separately approved

Artifact class guidance used below:

- `FILESYSTEM_ONLY` by default
- `LOCAL_SENSITIVE` only for operator QA files that contain no raw coordinates, geometry, WKT, bounds, CRS transforms, local or Drive paths, hashes/checksums, target locations, or secrets
- `REDACTED_PUBLIC` only for already-redacted summaries
- `PREVIEW_ONLY` only for safe previews

## Global Artifact-Class Rules

Default rule:

- notebook full-job outputs should be treated as `FILESYSTEM_ONLY` unless they are explicitly promoted under the stricter guidance above

Must remain `FILESYSTEM_ONLY`:

- KMZ
- GeoJSON
- WKT dumps
- exact lat/lon target tables
- per-object patches with location context
- Drive/path inventory reports
- raw notebook full-job mirrors
- classifier outputs with target locations
- raw QA files containing bounds/transforms/paths
- training/inference outputs
- exact-target/classifier/KMZ sections unless later redacted

`LOCAL_SENSITIVE` candidates if redacted correctly:

- SAR pair diagnostics JSON without coordinates
- SAR summary CSV without coordinates
- band stats CSV without coordinates
- nodata audit reports without paths/transforms
- alignment QA summaries after redaction
- parity QA reports after redaction

## Phase Inventory

### Setup / install / working dirs

Source notebook phases:

- Phase A — Setup, installs, working dirs

Outputs and classification:

- package installs, imports, working-dir creation, temp folder resets: `C`
- Colab folder constants and Drive mounts: `C`
- radar helper functions and duplicate kitchen cells: `C`
- Drive mount and Colab-local directory orchestration: `D`

Artifact-class guidance:

- no app artifact equivalent for setup/install cells
- any raw Colab/Drive mirror or path inventory remains `FILESYSTEM_ONLY`

### Map / point / ROI

Source notebook phases:

- Phase B — Map, point picker, ROI

Outputs and classification:

- interactive geemap map, basemap, click picker, JS auto-scroll: `C`
- printed selected point as EE geometry / GeoJSON / WKT / lat-lon: `D`
- WGS84 and UTM ROI WKT printouts and zone verification text: `D`
- internal ROI construction semantics relevant to the app grid contract: `A`

Artifact-class guidance:

- no public artifact should expose raw coordinates, geometry, WKT, or exact ROI bounds
- any notebook-style ROI dump or exact-point report is `FILESYSTEM_ONLY`

### RUN folder + GRID + DEM

Source notebook phases:

- Phase C — RUN folder + grid manifest + DEM

Outputs and classification:

- RUN folder tree and internal path manifests: `B`
- authoritative GRID dict / grid manifest: `A`
- DEM GeoTIFF and DEM NPY: `A`
- RUN/GRID guard outputs and path guards: `B`
- zero-shift gate results and drift audit outputs: `B`

Artifact-class guidance:

- `grid_manifest.json`, DEM outputs, and stage manifests may be `LOCAL_SENSITIVE` only if they do not expose forbidden public content outside local/internal use
- any raw path-bearing RUN tree mirror remains `FILESYSTEM_ONLY`

### SAR RTC pipeline

Source notebook phases:

- Phase D — Sentinel-1 GRD → RTC pipeline

Outputs and classification:

- notebook S1 collection selection and grid-lock logic: `A`
- `VV_dB`, `VH_dB`, `logRatio_dB`, `incidence` rasters: `A`
- local DEM-assisted RTC processing outputs: `A`
- raw Earth Engine auth-flow behavior and Colab-specific EE bootstrap: `D`

Artifact-class guidance:

- primary SAR rasters are app artifacts
- any raw notebook-specific auth/runtime mirror remains `FILESYSTEM_ONLY`

### Drive-export waits and SAR QA/export

Source notebook phases:

- Phase E — Drive-export waits, pixel-alignment QA

Outputs and classification:

- Drive wait/copy-back mechanics: `D`
- per-band SAR stats and nodata audits: `B`
- pixel-center alignment checks and edge-consistency checks: `B`
- auto-rebuilt `logRatio_dB` if absent: `B`
- cube-to-per-band GeoTIFF export helpers: `B`
- shell listings of Drive folders and raw folder scans: `D`

Artifact-class guidance:

- SAR pair diagnostics JSON without coordinates: `LOCAL_SENSITIVE` candidate
- SAR summary CSV without coordinates: `LOCAL_SENSITIVE` candidate
- nodata audit reports without paths/transforms: `LOCAL_SENSITIVE` candidate
- raw Drive scans, local/Drive path inventories, or export-watcher logs: `FILESYSTEM_ONLY`

### Nano / geophysics / feature stacks

Source notebook phases:

- Phase F — "Nano / Treasure / Geophysics" feature stacks
- Phase G — More feature stacks, rename layer

Outputs and classification:

- derived nano/geophysics/treasure/refined RTC/sigma0/master-stack rasters and NPY stacks: `B`
- final export presence checks and per-layer stats: `B`
- texture/tensor essentials QA and geometry-consistency checks: `B`
- naming-only compatibility notes and duplicate stack variants: `C`
- domain-specific "treasure / archaeology target" naming variants: `D`

Artifact-class guidance:

- these stack outputs are not automatically public app artifacts
- band stats CSV without coordinates: `LOCAL_SENSITIVE` candidate
- raw stack mirrors and duplicate notebook stack exports default to `FILESYSTEM_ONLY`

### Hypercube / PCA / object extraction / alignment QA

Source notebook phases:

- Phase H — Hypercube + auditor + PCA anomaly + object extraction
- Phase I — Bonus/simulator features, tensor exports, alignment QA

Outputs and classification:

- official hypercube assembly outputs (`hypercube.tif`, `hypercube.npy`, support CSVs): `A`
- hypercube audits and official-grid audit CSVs: `B`
- PCA anomaly rasters and PCA reports: `A`
- object proposals, labels, object index, cluster summary: `A`
- per-object context exports and per-object NPY patches with location context: `D`
- auxiliary simulators, bonus features, extra tensors, twin Drive/Colab comparisons: `B`
- full TIF alignment QA and sub-pixel checks: `B`

Artifact-class guidance:

- alignment QA summaries after redaction: `LOCAL_SENSITIVE` candidate
- parity QA reports after redaction: `LOCAL_SENSITIVE` candidate
- per-object patches with location context remain `FILESYSTEM_ONLY`
- raw auditor CSVs with paths/transforms remain `FILESYSTEM_ONLY` unless redacted first

### DEM / S2 / thermal / focus-mask outputs

Source notebook phases:

- Phase J — Stragglers + DEM-matched S2 masks
- Phase K — "Tesla v7.2" inference engines
- Phase L — DEM_GEO8 + thermal + Zero-Point report + focus mask

Outputs and classification:

- DEM-derived layer sets such as slope/aspect/curvature/TPI/TRI/roughness/TWI families: `A`
- Landsat thermal / daytime LST aligned outputs: `A`
- DEM-matched S2 masks and grid-anchored optical tensors: `B`
- master-grid audits, reference-tif comparisons, metadata recovery, anchor-layer inspections: `B`
- focus-mask outputs and focus-region restricted analysis products: `D`
- zero-point reports and path-locator scans: `D`
- "treasure / precious-material / fusion center" named inference tensors: `D`

Artifact-class guidance:

- redacted alignment/focus QA summaries without forbidden content may be `LOCAL_SENSITIVE`
- raw focus-mask products tied to exact target context remain `FILESYSTEM_ONLY`
- Drive file locators and report scans remain `FILESYSTEM_ONLY`

### Classifier / KMZ / GeoJSON / target-output sections

Source notebook phases:

- Phase M — Tesla v7.2 hard classifiers
- Phase N — Outputs sanity + KMZ generation
- portions of Phase O / P / S that emit classifier target outputs

Outputs and classification:

- hard-classifier CSV/TXT/JSON target outputs with exact target semantics: `D`
- FeatureCollection exports and target GeoJSON outputs: `D`
- KMZ outputs including heatmaps, 3D targets, field-operation KMZs, navigation KMZs: `D`
- exact-target tables, target labels, subpixel-centered target exports: `D`
- QA CSV structure inspectors and target QA structure checks: `B`

Artifact-class guidance:

- classifier outputs with target locations are `FILESYSTEM_ONLY`
- exact-target/classifier/KMZ sections stay `FILESYSTEM_ONLY` unless later redacted and separately approved
- raw QA files containing bounds/transforms/paths remain `FILESYSTEM_ONLY`

### Training / inference / scanner sections

Source notebook phases:

- Phase O — Training scaffolding + AI inference pipeline
- Phase P — More iterations + CNN exec + metal-fingerprint scanner
- Phase S — CNN model build attempts

Outputs and classification:

- training cells, learned weights, VRAM-specific training variants, model prep flows: `D`
- inference loops and object-detector CSV/GeoJSON outputs: `D`
- CNN execution CSV exporters, final target inference, structural scanners, decision scanners: `D`
- metal-fingerprint diagnostics and target-by-target direct signature reports: `D`
- setup/install driver markdowns and JS autorun helpers: `C`

Artifact-class guidance:

- all training/inference outputs are `FILESYSTEM_ONLY`
- detector CSV or GeoJSON outputs with target context are `FILESYSTEM_ONLY`

### Drive scans / reference / comparison utilities

Source notebook phases:

- Phase Q — Drive scans + S2 era pulls + radar pulls
- Phase R — Reference-tif comparison utilities

Outputs and classification:

- Drive walks, folder scans, manual upload directories, local secrets-folder tif scans: `D`
- old-vs-current S2 comparison utilities and last-image inspectors: `B`
- radar VV pull checks and reference-tif diagnostics: `B`
- CSV/TXT comparison reports linking matrices to analysis pipelines: `B`
- explicit region naming, GPS-point comparison, and target-region references: `D`

Artifact-class guidance:

- Drive/path inventory reports are `FILESYSTEM_ONLY`
- raw notebook full-job mirrors are `FILESYSTEM_ONLY`
- comparison CSV/TXT reports can be `LOCAL_SENSITIVE` only after redaction removes coordinates, paths, transforms, and exact region references

## Summary View

High-confidence app reproduction targets eventually applicable to the app:

- internal GRID and DEM work products
- SAR RTC outputs and supporting non-coordinate QA
- DEM derivatives
- thermal LST
- selected S2-derived non-target products
- hypercube
- PCA anomaly outputs
- object extraction outputs without location-bearing side products
- redacted alignment/parity QA summaries

Outputs that are not app artifacts and should not be treated as eventual public equivalents:

- map-only interaction cells
- Colab/Drive orchestration
- raw ROI/point dumps
- KMZ/GeoJSON exact-target exports
- WKT/lat-lon tables
- training/inference/classifier target outputs
- raw notebook mirrors and path inventories

## Not Implemented Yet

This document is an inventory and classification record only.

It does not:

- authorize implementation
- authorize `plan.md` changes
- authorize public exposure
- authorize notebook edits
- authorize classifier-output surfacing
- authorize promotion of any notebook full-job output into the app without separate approval
