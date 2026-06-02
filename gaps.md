# Notebook-to-App Gaps and Intentional Omissions

**Project:** GEE Screening  
**Source review:** `Notebook cells.md`, repository docs, and current app code  
**Purpose:** Separate true product gaps from notebook behavior that the app intentionally removed or quarantined.

---

## 1. Scope decision

This document records what the notebook can do that the current app cannot do, with one important distinction:

- Some missing notebook behavior is a real product gap.
- Some missing notebook behavior is intentionally excluded because it is speculative, unsafe, duplicate, Colab-only, or not PRD-aligned.

Excluded from this gap register by project-owner decision:

- Interactive Colab point picker / map workflow.

That feature is not tracked as a required app gap.

---

## 2. One-line summary

The notebook does the defensible science the app does, plus a large amount of duplicate feature-stack work, Colab/Drive plumbing, exact-coordinate export behavior, and speculative treasure/archaeology classifier language. The app keeps the controlled science path, fixes known formula/code issues, drops duplicate and Colab-only behavior, blocks coordinate-bearing public responses, and quarantines any classifier-style logic behind a CLI-only experimental boundary with neutral labels and filesystem-only outputs.

---

## 3. True remaining product gaps

These are the gaps that still matter for the lawful paid-archive triage product.

### 3.1 v6 paid-archive package import

#### Notebook capability

The validated v6 notebook can produce a paid-archive triage package containing files such as:

- `lawful_gee_candidate_scout_top_25_<timestamp>.csv`
- `lawful_gee_candidate_scout_top_25_<timestamp>.geojson`
- `top25_enhanced_v6.csv`
- `top25_enhanced_v6.geojson`
- `quality_diagnostics_all_cells_v6.csv`
- `stable_candidate_priority_list_v6.csv`
- `request_zones_v6.csv`
- `request_zones_v6.geojson`
- `paid_imagery_quote_template_v6.csv`
- `paid_imagery_quote_comparison_v6.csv`
- `paid_archive_request_summary.txt`
- `visual_inspection_map.html`
- `paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip`

#### Current app gap

The app does not yet provide a v6 package importer that validates this package and persists its contents as governed app data.

The current app run/artifact model is not enough by itself. The product still needs structured import records and parsed entities for candidates, request zones, and quote comparisons.

#### Required capability

Add a v6 import path that:

1. validates package presence;
2. validates required files;
3. validates CSV/GeoJSON schemas;
4. stores provenance hashes;
5. links import results to a run;
6. persists candidate rows;
7. persists request-zone rows;
8. persists quote-template/comparison rows;
9. blocks import/escalation when legal gates fail.

Suggested PRD-style command:

```bash
lawful-anomaly gee-import-v6 \
  --run-id <run_id> \
  --package-path <paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip> \
  --attestation present \
  --geofence clear
```

#### Priority

High.

---

### 3.2 Candidate persistence and v6 review-priority ranking

#### Notebook capability

The notebook can produce ranked candidate tables with fields such as:

- `candidate_score`
- `quality_adjusted_score`
- `review_priority_score`
- `confidence_score_all`
- `stability_score`
- `top10_count`
- `top25_count`
- `avg_rank`
- `season_top10_count`
- `season_top25_count`
- `season_avg_rank`
- `season_score_mean`
- `season_score_std`
- `score_gap_from_median`
- `score_gap_to_next_rank`
- `balanced_rank`
- `visibility_heavy_rank`
- `contrast_heavy_rank`
- `terrain_heavy_rank`
- `false_positive_warning_count`

#### Current app gap

The app can generate PCA anomaly and object extraction outputs, but those outputs are not the full v6 candidate review model. Current object outputs are closer to anomaly-object summaries than paid-archive candidate review records.

#### Required capability

Persist imported v6 candidate rows and review them using the PRD ordering:

1. `review_priority_score`
2. `false_positive_warning_count` ascending
3. `confidence_score_all`
4. `stability_score`
5. `candidate_score`

The app must keep the interpretation rule visible:

> A high-scoring candidate means worth review with paid imagery. It does not mean treasure found, archaeology proven, or field action authorized.

#### Priority

High.

---

### 3.3 Request-zone lifecycle

#### Notebook capability

The notebook can generate paid-imagery request zones:

- `request_zones_v6.csv`
- `request_zones_v6.geojson`

#### Current app gap

The app does not yet expose structured request-zone records equivalent to the v6 package lifecycle.

Missing structured fields include:

- `zone_id`
- geometry;
- centroid;
- area estimate;
- included candidate IDs;
- candidate count;
- max candidate score;
- mean review priority score;
- max confidence score;
- minimum false-positive warning count;
- reason summary;
- recommended imagery specs;
- request-zone review state.

#### Required capability

Add request-zone import and review support.

Request zones should be ranked using:

1. clean candidate presence;
2. highest review-priority score;
3. confidence score;
4. stability score;
5. low false-positive warning count;
6. practical coverage efficiency.

Public/shared exports must remain coordinate-restricted or redacted. Internal/reviewer exports may include exact geometry only behind explicit gated review/export actions.

#### Priority

High.

---

### 3.4 Paid imagery quote template and quote-comparison lifecycle

#### Notebook capability

The notebook can prepare paid imagery quote files:

- `paid_imagery_quote_template_v6.csv`
- `paid_imagery_quote_comparison_v6.csv`

Expected quote fields include:

- `quote_id`
- `provider`
- `zone_id`
- `candidate_ids_covered`
- `acquisition_date`
- `sensor`
- `resolution_m`
- `cloud_cover_pct`
- `off_nadir_deg`
- `sun_elevation_deg`
- `processing_level`
- `license_terms`
- `price`
- `currency`
- `delivery_time_days`
- `coverage_score`
- `metadata_complete`
- `notes`

#### Current app gap

The app does not yet persist provider quote comparison rows as structured app data.

#### Required capability

Add quote-comparison persistence and review support.

Quote scoring should consider:

- resolution quality;
- cloud cover;
- off-nadir angle;
- coverage of priority zones;
- metadata completeness;
- license acceptability;
- price;
- delivery time.

No quote request, provider order, or imagery purchase may be created automatically. Any escalation must require:

- legal gate passed;
- reviewer approval;
- export audit manifest exists;
- explicit human trigger.

#### Priority

Medium-high.

---

### 3.5 False-positive review upgrades

#### Notebook / PRD capability

The v6 workflow includes false-positive warning concepts such as:

- built-up warning;
- cropland-heavy warning;
- water-edge warning;
- modern-linear-edge warning;
- false-positive warning count.

Future desired warnings include:

- road proximity;
- settlement proximity;
- quarry or construction pattern;
- building density;
- field-boundary pattern.

#### Current app gap

The app has the staged raster/object workflow, but the full v6 false-positive warning review model is not yet persisted as structured candidate review data.

#### Required capability

Add or import warning fields and use them to lower review priority or require manual review. Warnings must not automatically delete candidates.

#### Priority

Medium-high.

---

## 4. Intentional omissions — not app gaps

These are notebook capabilities the app should not reproduce as normal product behavior.

---

### 4.1 Treasure / archaeology classifier labels are removed from the user surface

#### Notebook behavior

Notebook cells such as 95, 97, 128, 132, 134, 135, and 236-243 emit named labels such as:

- `Gold_Metal_Jar`
- `Sarcophagus_Naos`
- `Red_Mercury_Trace`
- `Black_Mercury_Trace`
- `Buried_Entrance`
- `Weapons_Shield_Cache`
- `Ancient_Well`

These labels are not defensible from 10 m public satellite pixels and must not appear in the user-facing app.

#### App behavior

The classifier-style logic is quarantined under:

```text
app/pipeline/stages_experimental/
```

Boundary rules:

- import requires `ENABLE_EXPERIMENTAL=1`;
- invocation is CLI-only;
- API must not import or expose it;
- frontend must not invoke or display it;
- background tasks must not invoke it;
- core orchestrator must not invoke it;
- outputs write only under `data/runs/<run_id>/experimental/`;
- outputs are `FILESYSTEM_ONLY` and `http_servable=False`;
- neutral IDs are used, such as `Class_A` through `Class_N`;
- mapping to source-notebook identifiers exists only in `docs/CLASS_MAPPING.md`.

#### Decision

This is an intentional safety boundary, not a missing feature.

Do not expose source notebook classifier labels through API, UI, logs, filenames, normal artifacts, or public exports.

---

### 4.2 No coordinate-bearing outputs over HTTP

#### Notebook behavior

Several notebook cells emit exact latitude/longitude to KMZ, GeoJSON, CSV, Google Earth overlays, or live map markers.

Examples from the notebook review include cells:

```text
119, 122, 123, 128, 132, 134, 135, 139, 149,
155, 156, 158, 159, 160, 162, 177, 178, 181,
190, 191, 200, 237, 241, 243
```

#### App behavior

The app redaction contract forbids public JSON keys and values that expose sensitive spatial or system details, including:

- latitude;
- longitude;
- coordinates;
- geometry;
- bounds;
- bbox;
- CRS;
- EPSG;
- CRS transform;
- filesystem paths;
- hashes;
- tracebacks;
- raw inputs.

The app also verifies outgoing JSON responses and returns a public error response if redaction verification fails.

KMZ, local location, heatmap, field-operation, and exact geometry artifacts must remain filesystem-only or otherwise internal/gated.

#### Decision

This is an intentional safety boundary, not a missing feature.

Do not make exact coordinate-bearing artifacts public, previewed, tiled, or directly downloadable over HTTP.

---

### 4.3 No `ee.Authenticate()` or interactive Earth Engine auth

#### Notebook behavior

The notebook uses Colab-style interactive Earth Engine authentication.

#### App behavior

The app uses backend/server service-account initialization only.

Required settings are:

- service-account email;
- service-account key path.

If either is missing, initialization fails instead of falling back to interactive auth.

#### Decision

This is intentional.

Do not add `ee.Authenticate()` to the backend app.

---

### 4.4 No Colab/Drive/UI-specific plumbing

#### Notebook behavior

The notebook contains Colab-only or Drive-only behavior, including:

- Drive mount;
- Drive export waits;
- Drive refresh hacks;
- shell listing cells;
- Colab JavaScript auto-scroll / auto-run cells;
- notebook-local pip install cells.

#### App behavior

The app uses controlled server-side run storage, Python dependencies, artifact records, and API/backend execution.

#### Decision

This is intentional.

Do not port Drive mount/wait/refresh hacks, Colab JavaScript cells, or notebook pip install cells into the app.

The interactive map/point-picker workflow is also excluded from this document by project-owner decision.

---

### 4.5 No notebook-only duplicate feature stacks

#### Notebook behavior

The notebook contains many duplicate or near-duplicate feature-stack families, including examples such as:

- NANO stacks;
- TREASURE stacks;
- SIGMA0 MASTER variants;
- GPHYS MASTER variants;
- ARCH TARGETS variants;
- RAD MASTER CUBE variants;
- ULTIMATE GPHYS SCAN;
- AUX METAL FEATURES;
- multiple PCA passes;
- multiple Tesla/inference protocol variants.

#### App behavior

The app collapses this into a controlled pipeline with one canonical path for:

- GRID;
- DEM;
- zero-shift/alignment checks;
- SAR RTC;
- Sentinel-2 indices;
- DEM derivatives;
- thermal;
- hypercube;
- PCA anomaly;
- object extraction;
- alignment QA.

#### Decision

This is intentional.

Do not port duplicate notebook stacks unless a future PRD identifies a specific defensible layer with tests, neutral naming, and governance.

---

### 4.6 Notebook-only artifacts the app intentionally does not produce

The app does not need to produce every notebook artifact.

Notebook-only or intentionally excluded families include:

- panchromatic outputs such as `PAN_LS` and `PAN_S2`;
- separate ascending/descending S1 support stacks;
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M` resampled variant;
- deep-learning model build/inference cells using Swin, UnetPlusPlus, ResNet50, SegFormer, or an archaeology dictionary;
- live geemap overlay of probability matrix on a satellite basemap;
- notebook-only AI/hard-decision QA files;
- pre-RTC SAR intermediates unless specifically needed for parity diagnostics.

Some notebook-compatible internal/parity artifacts may exist in app code, such as `REPORT_640_*` or notebook-compatible hypercube outputs. Those must be treated as internal/parity artifacts and must not be promoted as user-facing proof semantics.

#### Decision

Do not treat every notebook-only artifact as a product gap.

Only implement notebook artifacts when they support the lawful paid-archive triage PRD.

---

### 4.7 Known notebook bugs are not carried forward

#### Notebook bug 1 — Python constructor typo

Notebook cell 233 uses a broken class constructor pattern:

```python
def init(self)
```

instead of:

```python
def __init__(self)
```

This is not carried into the app.

#### Notebook bug 2 — `IRON_SWIR` denominator

The notebook note identified this incorrect formula:

```text
IRON_SWIR = (B11 - B12) / (B11 - B12)
```

That expression collapses to 1 wherever the denominator is nonzero.

The app uses the corrected normalized-difference form:

```text
(B11 - B12) / (B11 + B12)
```

#### Decision

These are fixes, not gaps.

Do not reintroduce notebook bugs for parity.

---

## 5. App strengths to preserve

Preserve these app advantages while adding true missing PRD capabilities:

- backend service-account Earth Engine flow;
- no interactive `ee.Authenticate()`;
- run status lifecycle;
- stage manifests;
- artifact records;
- artifact classes;
- filesystem-only sensitive outputs;
- fixed GRID discipline;
- alignment QA;
- public/internal export separation;
- redaction verification on public JSON responses;
- controlled API access instead of free-form notebook execution;
- quarantined experimental classifier boundary;
- neutral labels only outside approved private mapping docs.

Do not weaken these controls while closing true product gaps.

---

## 6. Recommended implementation order

### Step 1 — v6 import scaffold

Add `gee-import-v6` package validation with required-file checks, schema checks, package hashes, and final-rule text verification.

### Step 2 — candidate persistence

Persist imported v6 candidate rows with score, stability, warning, and provenance fields.

### Step 3 — request-zone persistence

Persist imported v6 request zones and add review states.

### Step 4 — quote-comparison persistence

Persist quote template/comparison rows and require explicit human selection.

### Step 5 — safe review UI/API views

Expose candidate and request-zone review data with public/internal coordinate rules.

### Step 6 — false-positive warning upgrades

Add stronger road/building/settlement/quarry/construction/field-boundary warnings.

### Step 7 — terminology guard audit

Keep user-facing product language neutral. Ensure no notebook treasure/archaeology labels leak into app code, frontend, logs, artifacts, or public API responses.

---

## 7. Final rule

This project supports lawful desk-based remote-sensing triage only.

It does not prove treasure, authorize entry, authorize metal detecting, authorize excavation, authorize collection, or replace landowner, heritage, environmental, or protected-area permits.
