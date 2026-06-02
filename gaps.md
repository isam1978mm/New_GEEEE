# Gaps Between Notebook Capabilities and Current App

**Project:** GEE Screening  
**Source review:** `Notebook cells.md` + current `max2026-lab/GEE_screening` repository review  
**Purpose:** Document what the notebook can do that the current app cannot yet do, while separating lawful/defensible gaps from unsafe or non-PRD-aligned notebook behavior.

---

## 1. Scope decision

This document records the notebook-vs-app capability gaps identified during review.

Excluded from this document by project-owner decision:

- Interactive Colab point picker / map workflow.

That notebook feature is not needed for the app gap list.

---

## 2. Executive verdict

The notebook can do more exploratory Colab work than the app, but much of the notebook's extra behavior is not safe, not production-ready, or not aligned with the lawful paid-archive triage PRD.

The current app is stronger for:

- controlled backend execution;
- fixed GRID discipline;
- service-account Earth Engine initialization;
- run history and artifact tracking;
- stage-by-stage pipeline status;
- safer artifact serving policy;
- local-only handling of sensitive artifacts.

The current app is weaker or incomplete for:

- full v6 paid-archive triage package import;
- structured candidate persistence;
- v6 review-priority ranking;
- request-zone lifecycle;
- paid imagery quote comparison lifecycle;
- structured false-positive warning review;
- neutralized product terminology.

---

## 3. Gap 1 — Full v6 paid-archive triage package

### Notebook capability

The v6 notebook can produce a full paid-archive candidate package, including files such as:

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

### Current app limitation

The app currently has a staged backend pipeline and artifact tracking, but it does not yet implement a v6 package importer that validates and persists these notebook outputs as structured app data.

The current app stores runs and artifacts, but the reviewed model does not yet include dedicated v6 import entities such as:

- `gee_import_artifacts`
- structured GEE candidate rows;
- structured request-zone rows;
- structured quote-comparison rows.

### Required app capability

Add a v6 import path that accepts a package directory or zip, validates schemas, stores provenance hashes, and persists candidate cells, request zones, and quote rows under the existing legal/review/export governance.

Suggested command from PRD direction:

```bash
lawful-anomaly gee-import-v6 \
  --run-id <run_id> \
  --package-path <paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip> \
  --attestation present \
  --geofence clear
```

### Priority

High.

This is the main gap between the validated v6 notebook workflow and the current app.

---

## 4. Gap 2 — Stable candidate ranking and review-priority logic

### Notebook capability

The notebook can produce ranked candidate files with fields such as:

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

### Current app limitation

The app can generate PCA anomaly and object extraction outputs, but its object outputs are mainly pixel/object summaries:

- object id;
- row/column bounding box;
- pixel center;
- area in pixels;
- mean anomaly;
- max anomaly;
- cluster id.

It does not yet implement the v6 ranking model using stability, seasonality, confidence, false-positive warnings, and review-priority ordering.

### Required app capability

The app should support v6 candidate ranking with primary review ordering:

1. `review_priority_score`
2. `false_positive_warning_count` ascending
3. `confidence_score_all`
4. `stability_score`
5. `candidate_score`

The app must keep this interpretation rule visible:

> A high-scoring candidate means worth review with paid imagery. It does not mean treasure found, archaeology proven, or field action authorized.

### Priority

High.

Without this, the app can detect raster/object anomalies but cannot reproduce the notebook's lawful v6 review shortlist.

---

## 5. Gap 3 — Request-zone creation for paid imagery

### Notebook capability

The notebook can generate request zones from high-priority candidate cells:

- `request_zones_v6.csv`
- `request_zones_v6.geojson`

These zones are practical geometries for paid high-resolution archive imagery requests.

### Current app limitation

The app has a fixed run grid and object extraction, but it does not yet expose a structured request-zone entity or lifecycle equivalent to the v6 package.

The current app does not yet provide governed request-zone records with:

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

### Required app capability

Add request-zone import and/or generation support.

The system should rank zones using:

1. clean candidate presence;
2. highest review-priority score;
3. confidence score;
4. stability score;
5. low false-positive warning count;
6. practical coverage efficiency.

Public/shared exports must remain coordinate-restricted or redacted. Internal/reviewer exports may include exact geometry only behind the existing gate.

### Priority

High.

Request zones are the bridge between anomaly/candidate review and paid imagery quote workflows.

---

## 6. Gap 4 — Paid imagery quote template and quote comparison workflow

### Notebook capability

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

### Current app limitation

The app does not yet persist provider quote comparison rows as structured app data.

The reviewed model does not yet include an `imagery_quote_comparisons` table or equivalent structured quote lifecycle.

### Required app capability

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

No paid quote, provider request, or imagery order may be created automatically. Any escalation must require:

- legal gate passed;
- reviewer approval;
- export audit manifest exists;
- explicit human trigger.

### Priority

Medium-high.

This becomes critical after request-zone persistence exists.

---

## 7. Gap 5 — Multiple ROI sizes and manual ROI outputs

### Notebook capability

The notebook can work with multiple ROI concepts, including:

- a rough larger square ROI;
- an exact UTM square ROI;
- printed WKT/GeoJSON representations;
- manual verification of UTM zone and geometry.

### Current app limitation

The app currently builds one authoritative grid around a supplied latitude/longitude:

- UTM CRS based on the coordinate;
- 10 m scale;
- 640 x 640 pixels;
- 6.4 km x 6.4 km extent.

This fixed grid is good for reproducibility, but it does not support multiple operator-defined ROI sizes or manual ROI output variants.

### Required app capability

Only add this if future product requirements need it.

Do not prioritize this over v6 import, candidate persistence, request zones, or quote comparison.

### Priority

Low.

The fixed grid is acceptable for controlled app execution.

---

## 8. Gap 6 — Google Drive export/wait/copyback workflow

### Notebook capability

The notebook can:

- mount Google Drive;
- export Earth Engine outputs to Drive;
- wait for Drive exports to land;
- copy outputs back into Colab;
- scan Drive folders;
- manually refresh Drive metadata.

### Current app limitation

The app uses server-side run storage and artifact records. It does not implement the notebook's Colab/Drive workflow.

### Required app capability

No immediate requirement.

For production, server-side storage is better than Drive copyback. The app should not adopt the Drive workflow unless there is a specific operator need for import/export compatibility.

### Priority

Low.

This is useful for Colab experimentation but not required for the production app.

---

## 9. Gap 7 — Experimental feature stacks and model-training attempts

### Notebook capability

The notebook contains many exploratory stacks and experiments, including:

- repeated radar/geophysics feature stacks;
- texture/tensor feature exports;
- PCA anomaly variants;
- watershed/object extraction variants;
- CNN/YOLO/Swin/SegFormer setup attempts;
- classifier/training scaffolds;
- repeated or duplicate cells.

Only part of this is defensible and useful for the app.

The defensible science core is approximately:

- GRID lock;
- Sentinel-1 SAR RTC pipeline;
- Sentinel-2 spectral indices;
- DEM derivatives;
- Landsat thermal;
- hypercube assembly;
- PCA anomaly;
- basic object extraction;
- alignment QA.

### Current app limitation

The app implements a controlled staged subset. It does not run every exploratory notebook experiment.

This is mostly correct. The app should not copy the notebook wholesale.

### Required app capability

Keep only PRD-aligned, explainable, defensible stages.

Potentially useful future additions:

- richer false-positive warning layers;
- stronger road/building/proximity filters;
- better quality diagnostics;
- neutral anomaly-class labeling;
- repeatability/stability scoring.

Do not add unsupported artifact-specific claims or dummy-label ML training.

### Priority

Medium.

The app should improve its defensible analysis, not absorb the notebook's speculative branches.

---

## 10. Gap 8 — Exact-coordinate KMZ / GeoJSON / field-navigation outputs

### Notebook capability

The notebook can emit exact-coordinate KMZ, GeoJSON, Google Earth, and field-navigation style outputs.

### Current app limitation

The app intentionally restricts these outputs. Some location and field-ops replacement artifacts exist, but they are local-only filesystem artifacts and should not be HTTP-served or public-facing.

### Required app capability

This is mostly not a missing feature. It is a governance boundary.

The app should continue to block public/default exposure of:

- exact candidate coordinates;
- exact request-zone geometries;
- exact field-navigation KMZ/KML;
- public Google Maps target links;
- public sub-pixel target coordinates.

Internal/reviewer-only export may include exact geometry only when:

- legal gate passed;
- reviewer action is explicit;
- warning language is visible;
- export is audit-logged;
- export precision policy allows it.

### Priority

Do not implement as public functionality.

Only retain narrowly controlled reviewer/internal export behavior.

---

## 11. Safety and terminology gap

### Issue

Some notebook-parity names and concepts are not aligned with the lawful PRD language. These labels should not appear in user-facing product surfaces:

- treasure;
- gold;
- silver;
- jars;
- tunnel;
- hidden doors;
- field operations;
- zero-point target;
- Tesla protocol;
- archaeology certainty;
- sub-pixel target claims;
- artifact-specific labels.

### Required app capability

Rename or hide unsafe/speculative labels before production exposure.

Use neutral terminology such as:

| Unsafe / speculative term | Safer app term |
| --- | --- |
| Gold halo | SWIR/NIR ratio layer |
| Silver oxide | visible-band ratio layer |
| Tunnel ceiling | NIR/red contrast layer |
| Hidden doors | directional hillshade contrast |
| Zero-point targets | threshold intersection mask |
| Field operations | reviewer-only local location artifact |
| Treasure / artifact classifier | anomaly class / review class |
| Target found | candidate anomaly |
| Confidence of discovery | confidence for review priority |

### Priority

High.

This is required for PRD alignment and risk control.

---

## 12. App strengths to preserve

The app should preserve the advantages it already has over the notebook:

- backend service-account Earth Engine flow;
- no Colab `ee.Authenticate()` dependency;
- run status lifecycle;
- stage manifests;
- artifact records;
- artifact classification;
- filesystem-only handling for sensitive outputs;
- fixed GRID discipline;
- alignment QA;
- public/internal export separation;
- local-only sensitive artifacts;
- controlled API access rather than free-form notebook execution.

Do not weaken these controls while adding notebook capabilities.

---

## 13. Recommended implementation order

### Step 1 — v6 import scaffold

Add a `gee-import-v6` importer that validates package presence, required files, schema, hashes, and final safety-rule text.

### Step 2 — candidate persistence

Persist imported v6 candidate rows with the required score, stability, warning, and provenance fields.

### Step 3 — request-zone persistence

Persist imported v6 request zones and add review states.

### Step 4 — quote-comparison persistence

Persist quote template/comparison rows and require explicit human selection.

### Step 5 — safer UI/review views

Expose candidate and request-zone review tables with public/internal coordinate rules.

### Step 6 — terminology cleanup

Rename unsafe notebook-parity labels or keep them strictly internal with neutral aliases.

### Step 7 — false-positive filter upgrades

Add stronger road/building/settlement/quarry/construction/field-boundary warnings.

---

## 14. Final rule

This project supports lawful desk-based remote-sensing triage only.

It does not prove treasure, authorize entry, authorize metal detecting, authorize excavation, authorize collection, or replace landowner, heritage, environmental, or protected-area permits.
