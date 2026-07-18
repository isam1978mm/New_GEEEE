# Local Private Core Classifier Execution Plan — 2026-07-15

## Status

This document is the current execution guide for the app hardening and screening-accuracy work that follows the 2026-07-15 code review.

It intentionally supersedes older audit assumptions that treated the app as a public product or treated PRD v0.5 as the current source of truth.

## Governing project decision

For this execution plan, use these rules before inspecting, auditing, planning, or patching code:

1. Treat the app as a local private app for one operator.
2. Treat the classifier as an app feature, not as a forbidden PRD v0.5 experimental boundary violation.
3. Do not prioritize or block on public-SaaS safety findings unless they also affect local correctness, local reliability, or false confidence.
4. Do not use PRD v0.5 as the current source of truth for classifier placement, API visibility, frontend visibility, or old CLI-only restrictions.
5. Preserve old-run compatibility for legacy `experimental/*` classifier outputs.
6. Fix result-correctness, data-quality, pipeline-integrity, artifact-integrity, and UI/backend contract bugs first.
7. After each completed run, the app must produce an easy-English final area findings summary that ranks direct classifier findings and shows the app's probability or score for each. The owner understands these are app estimates rather than physical confirmation.

## Explicit exclusions for future audits

Future audits must not raise the following as blockers under this local-private execution plan:

| Excluded audit class | Reason |
|---|---|
| Public web exposure assumptions | The app is local/private unless deployment surface changes. |
| Old PRD v0.5 classifier boundary | The owner changed the app direction: classifier is core app functionality. |
| “Classifier must be CLI-only” | Superseded by current project decision. |
| “Classifier must not appear in frontend/API” | Superseded by current project decision. |
| Public-SaaS severity ratings | Use local-private severity unless the server is exposed outside localhost. |
| Removing legacy `experimental/*` compatibility | Forbidden. Old completed runs must still render classifier results. |

Public-safety issues may still be recorded separately, but they are not the current repair track unless the owner explicitly reopens public deployment or sharing.

## Non-negotiable compatibility contracts

### Classifier output compatibility

The app must support both current core classifier outputs and legacy experimental outputs.

Current core paths:

```text
classifier/classifications.csv
classifier/summary.json
classifier/neutral_target_labels.json
```

Legacy compatibility paths:

```text
experimental/classifications.csv
experimental/summary.json
experimental/neutral_target_labels.json
```

If either set exists for a completed run, the Classifier Results panel must not show “No classifier result.”

The backend must serve current core classifier artifact URLs correctly. The frontend may keep legacy fallback only for old-run compatibility, not as a mask for broken core URLs.

### Final area findings summary contract — owner revision 2026-07-17

The previous neutral-wording requirement is superseded for this local private app.

Required operator-facing result:

- Title: `Final area findings summary`.
- Use easy English suitable for a non-expert.
- Rank possible findings from strongest to weakest.
- Show the classifier probability or score for every listed finding.
- State which finding is best supported in the area.
- Add one short explanation of what deserves the most attention.
- Show `No strong result` or `Unclear result` when evidence is insufficient.
- Preserve access to detailed classifier rows and downloadable output files.
- Support both current `classifier/*` outputs and legacy `experimental/*` outputs.
- Direct domain labels are allowed; future audits must not force generic neutral score bands.
- Do not display numerical depth in metres unless the separate depth-estimation plan has passed its calibration and validation gates.

Example:

> The strongest result in this area is a metal-like target with an app probability of 72%. A cavity or chamber is the second possibility at 19%. Natural ground variation is 9%. The metal-like target is the main result to review.

The probability or score must be presented as the app's result, not silently changed, normalized, or replaced by invented certainty.

## Remaining issues to execute

The following table ignores public-safety-only issues and ignores old PRD classifier-boundary issues.

| # | Issue | Type | Local severity | Why |
|---:|---|---|---|---|
| 1 | Core classifier download URLs return 404 | Backend/frontend contract | High | Core classifier is the current feature path. Legacy fallback must not hide a broken backend route. |
| 2 | Hypercube can ingest pseudo-target `REPORT_640` TIFFs | Screening accuracy / circular leakage | High | PCA/classifier may rediscover upstream threshold-derived target-like layers instead of independent sensor evidence. |
| 3 | Hypercube/PCA behavior does not match stated notebook contract | Scientific correctness / provenance | High | NaN/mask behavior, band removal, and whitening can change results while still appearing parity-like. |
| 4 | S2 validation can pass with zero valid derived pixels | Data quality gate | High | App can continue even when derived indices have no usable pixels. |
| 5 | SAR pairing is greedy and SAR output can be all nodata | Data quality / SAR reliability | High | SAR stage can pass with suboptimal pairing or no usable signal. |
| 6 | Artifact reruns can create duplicate DB records | Data integrity | Medium-High | Downloads can fail or select the wrong artifact if duplicate `(run_id, name)` rows exist. |
| 7 | One-active-run rule is racy; queued runs can survive restart | Runtime reliability | Medium-High | Two runs can start together, or a stale queued run can block future work. |
| 8 | File responses are fully buffered by middleware | Performance / reliability | Medium | Large downloads can waste memory and defeat streaming. |
| 9 | Classifier is an uncalibrated heuristic | Screening accuracy | High | Scores are relative screening priorities, not probability, confidence, detection, or validation. |
| 10 | Classifier uses rectangular bounding boxes | Screening accuracy | Medium-High | Feature summaries can include unrelated background pixels around the component. |
| 11 | Classifier lacks a final ranked area findings summary | Result communication | Medium-High | The operator needs an easy-English conclusion showing the best-supported findings and the app probability or score for each. |

## Execution order

Execute in this order. Do not jump to classifier enhancement before the pipeline input and artifact contracts are stable.

### Phase 0 — Audit stance lock

Goal: prevent future sessions from undoing the current project direction.

Tasks:

1. Mark PRD v0.5 as historical/non-authoritative for current audits.
2. Keep this execution document as the current repair guide.
3. Keep `AUDIT_DO_NOT_BREAK_CONTRACTS.md` as a compatibility guard.
4. Do not remove legacy classifier fallback without an old-run compatibility test.

Acceptance:

```powershell
git grep -n "PRD v0.5 is historical" docs
```

The grep should find an explicit warning.

### Phase 1 — Core classifier backend download contract

Goal: core classifier URLs must return 200 without relying on legacy `experimental/*` fallback.

Problem:

The frontend requests core artifact names such as:

```text
classifier_classifications
classifier_summary
classifier_neutral_labels
```

But backend filename mapping recognizes only old experimental names.

Fix:

1. Update backend artifact filename map to include current core classifier names.
2. Keep legacy names for old runs.
3. Add tests that core classifier artifact download URLs return 200.
4. Add tests that legacy fallback still works for old runs.
5. Frontend fallback remains only compatibility fallback, not the only working route.

Expected allowed artifact names:

```text
classifier_classifications -> classifications.csv
classifier_summary -> summary.json
classifier_neutral_labels -> neutral_target_labels.json
experimental_classifications -> classifications.csv
experimental_summary -> summary.json
experimental_neutral_labels -> neutral_target_labels.json
```

Required tests:

```powershell
pytest tests/unit/test_classifier_stage.py tests/integration/test_artifact_serving.py tests/integration/test_frontend_static.py
```

Acceptance:

- `/runs/{id}/artifacts/classifier_classifications/download/classifications.csv` returns 200 for a current run.
- `/runs/{id}/artifacts/classifier_summary/download/summary.json` returns 200 for a current run.
- `/runs/{id}/artifacts/classifier_neutral_labels/download/neutral_target_labels.json` returns 200 for a current run.
- Legacy `experimental/*` run still renders in the panel.

### Phase 2 — Hypercube explicit feature manifest

Goal: prevent circular leakage by controlling exactly which TIFFs become hypercube input bands.

Problem:

Hypercube dynamically discovers broad root TIFFs. That can ingest downstream/generated decision layers such as `REPORT_640_*.tif`, causing PCA/classifier to rediscover earlier rule-derived target-like information.

Fix:

1. Replace dynamic root-TIFF discovery with an explicit, versioned, ordered feature manifest.
2. Record the feature schema version in hypercube metadata.
3. Fail if a required feature is missing unless explicitly configured as optional.
4. Block any downstream/generated or target-like TIFF from hypercube input.
5. Add a test fixture with `REPORT_640_*.tif` present and assert it is not included.

Allowed input classes should be independent sensor/derived feature layers only, such as:

```text
NDVI
NDWI
NDMI
NBR
IRONOX
IRON_SWIR
BSI
SAR bands / radar derived bands intended as independent features
DEM derivatives
thermal feature layers
approved secret/source feature layers only if they are not target labels or screening outputs
```

Blocked from hypercube input:

```text
REPORT_640_*.tif
threshold masks
screening result TIFFs
PCA output
classifier output
object masks
cluster maps
location exports
field-ops exports
any downstream-generated decision layer
```

Required tests:

```powershell
pytest tests/unit/test_hypercube.py tests/notebook_parity/test_hypercube_parity.py
```

Acceptance:

- Hypercube band order is deterministic.
- Hypercube metadata includes feature schema version.
- `REPORT_640_*.tif` cannot enter the hypercube.
- Any intentional non-notebook behavior is labelled honestly.

### Phase 3 — Hypercube/PCA parity label correction

Goal: stop claiming notebook parity where behavior intentionally differs.

Problem:

Hypercube and PCA behavior changed relative to the notebook: NaN/mask behavior, band filtering, and PCA whitening. Only the `IRON_SWIR` formula correction was previously identified as a known correction.

Fix options:

Option A — strict parity mode:

1. Reproduce notebook mask/NaN behavior.
2. Reproduce notebook PCA band list.
3. Reproduce notebook PCA math, including whether whitening is used.
4. Add frozen notebook-output tests.

Option B — app-corrected mode:

1. Keep improved behavior.
2. Rename metadata to an app-specific method version.
3. Do not label it `PARITY_CORRECTS` unless the correction is explicitly documented.
4. Add an ADR explaining why behavior diverges from the notebook.

Preferred execution:

- Keep the app mode if it is technically better, but document it as app-corrected, not notebook parity.
- Reserve `PARITY_CORRECTS` only for explicitly approved corrections such as `IRON_SWIR`.

Required tests:

```powershell
pytest tests/notebook_parity/test_hypercube_parity.py tests/notebook_parity/test_pca_anomaly_parity.py tests/unit/test_notebook_output_metadata_contract.py
```

Acceptance:

- Metadata no longer overclaims parity.
- Intentional divergence is documented.
- Tests distinguish strict notebook parity from app-corrected behavior.

### Phase 4 — S2 per-band and shared-valid data gates

Goal: prevent S2 from passing when derived index layers have no usable pixels.

Problem:

Coverage can be averaged across a cube instead of requiring each necessary band and the shared mask for each index.

Fix:

1. Compute valid fraction per source band.
2. Compute valid fraction per derived index.
3. Compute shared valid mask for each index formula.
4. Block if any required derived index has zero valid pixels.
5. Warn or block if valid fraction is below configured threshold.
6. Write these checks into S2 summary and run quality summary.

Required output fields:

```text
per_source_band_valid_fraction
per_index_valid_fraction
per_index_shared_mask_valid_fraction
zero_valid_indices
low_valid_indices
s2_quality_status
```

Required tests:

```powershell
pytest tests/unit/test_s2_nodata_dtype_contract.py tests/unit/test_run_quality_summary.py
```

Acceptance:

- All-zero NDVI/NDWI/NDMI/NBR/IRONOX/IRON_SWIR/BSI blocks or warns according to policy.
- Run quality reports the exact failing index.
- Pipeline does not proceed silently with empty S2 features.

### Phase 5 — SAR pairing and all-nodata gate

Goal: prevent SAR stage from passing with poor pairing or no usable output.

Problem:

Pairing is greedy and may miss a feasible matching. SAR outputs can also be entirely nodata without failing.

Fix:

1. Replace greedy pairing with deterministic feasible matching or scoring over candidate pairs.
2. Record selected pair metadata and rejected alternatives.
3. Compute valid pixel fraction for each SAR output.
4. Block when required SAR bands are all nodata.
5. Warn when valid coverage is low.
6. Add pair-quality and coverage fields to SAR summary and run quality summary.

Required output fields:

```text
pairing_strategy
candidate_pair_count
selected_pairs
rejected_pairs_reason
per_sar_band_valid_fraction
all_nodata_outputs
sar_quality_status
```

Required tests:

```powershell
pytest tests/unit/test_sar_rtc.py tests/unit/test_run_quality_summary.py
```

Acceptance:

- A feasible non-greedy pairing fixture passes.
- A greedy-miss fixture is handled correctly.
- All-nodata SAR output blocks run quality.

### Phase 6 — Artifact uniqueness and rerun integrity

Goal: prevent duplicate DB artifacts and unstable downloads.

Problem:

There is no uniqueness guarantee for `(run_id, name)`. Reruns can create duplicate artifacts and downloads can fail with multiple rows.

Fix:

1. Add a DB uniqueness constraint or index on `(run_id, name)`.
2. Convert artifact recording to upsert/replace semantics.
3. Preserve created/updated timestamps clearly.
4. Add a migration that deduplicates existing rows before adding the constraint.
5. Add tests for rerunning a stage and downloading the artifact.

Required tests:

```powershell
pytest tests/unit/test_full_job_artifact_inventory.py tests/integration/test_artifact_serving.py
```

Acceptance:

- Rerunning a stage does not create duplicate artifact rows.
- Download selects exactly one artifact.
- Existing duplicate rows are handled safely by migration.

### Phase 7 — Active-run lock and queued recovery

Goal: prevent duplicate active runs and avoid stuck queued rows after restart.

Problem:

Two concurrent sessions can both pass the active-run SELECT check and commit queued runs. Queued runs may survive restart and block future work.

Fix:

1. Serialize active-run creation using DB transaction semantics appropriate for SQLite.
2. Treat queued rows as recoverable on startup according to age/status.
3. Add a clear policy for queued recovery: stale queued -> stale_failed or requeue, not indefinite block.
4. Add integration tests with concurrent create requests.

Required tests:

```powershell
pytest tests/unit/test_run_state.py tests/integration/test_runs_api.py tests/integration/test_startup_stale_run_cleanup.py
```

Acceptance:

- Concurrent run creation cannot produce two active queued/running rows.
- Stale queued runs after restart are recovered according to policy.
- Active delete remains blocked.

### Phase 8 — Streaming response middleware

Goal: avoid buffering file downloads in memory.

Problem:

Middleware concatenates response bytes and defeats streaming.

Fix:

1. Do not buffer streaming/file responses.
2. Apply response redaction/verification only to JSON responses.
3. Keep file responses as `FileResponse` or streaming iterables.
4. Add a regression test proving large file responses are not consumed by middleware.

Required tests:

```powershell
pytest tests/integration/test_artifact_serving.py
```

Acceptance:

- File downloads still work.
- JSON redaction still works.
- Middleware does not consume full file bodies.

### Phase 9 — Final area findings summary

Goal: turn detailed classifier output into a clear end-of-run conclusion for the private operator.

Required implementation:

1. Read the completed run's classifier summary and classification rows.
2. Support both current core `classifier/*` files and legacy `experimental/*` files.
3. Aggregate results by finding label using a documented deterministic rule.
4. Rank findings from strongest to weakest.
5. Display the app probability or score for each finding.
6. Generate one easy-English paragraph naming the strongest finding and the next most likely alternatives.
7. Show an explicit unclear/no-strong-result result when data quality is insufficient or no score passes the configured reporting threshold.
8. Keep links to the detailed CSV, summary JSON, and label metadata.
9. Do not convert direct domain labels into generic neutral bands.
10. Do not add a depth-in-metres field until the separate depth-estimation plan is implemented and validated.

Recommended summary fields:

```text
summary_version
run_id
best_finding
best_finding_score
ranked_findings[]
finding_label
finding_score
score_type
supporting_candidate_count
data_quality_status
summary_text_easy_english
```

Required tests:

```powershell
pytest tests/unit/test_classifier_stage.py tests/integration/test_frontend_static.py tests/integration/test_classifier_legacy_ui_fallback_contract.py
```

Acceptance:

- A completed run shows `Final area findings summary`.
- Findings are ordered from highest to lowest score.
- Each displayed finding includes its app probability or score.
- The easy-English paragraph names the strongest finding.
- Weak or insufficient evidence produces an unclear/no-strong-result summary.
- Current core and legacy classifier outputs both work.
- Detailed downloads remain available.
- No numerical depth is displayed.

### Phase 10 — Classifier feature improvement

Goal: improve classifier quality while preserving transparent scores, data-quality warnings, and deterministic output.

Fix:

1. Use exact connected-component pixels instead of bounding boxes.
2. Compute per-object valid pixel fraction.
3. Compute per-band median, MAD, quantiles, and local contrast.
4. Use raw anomaly values, not display-stretched values.
5. Add `INSUFFICIENT_DATA` abstention.
6. Add deterministic tie handling for cluster aggregation.
7. Include method/schema/provenance version fields.

Required tests:

```powershell
pytest tests/unit/test_classifier_stage.py tests/unit/test_run_quality_summary.py
```

Acceptance:

- Classifier refuses or abstains on insufficient data.
- Bounding-box-only summaries are replaced or clearly deprecated.
- Outputs include method version and quality warnings.

## Improving screening accuracy roadmap

| Improvement | Type | Local priority | Why |
|---|---|---|---|
| Explicit feature manifest | Feature control | Very High | Prevents circular leakage and makes inputs reproducible. |
| Per-band and shared-valid coverage gates | Data quality | Very High | Prevents S2/SAR/fusion stages from passing with empty data. |
| Block downstream/generated layers from Hypercube | Leakage prevention | Very High | Prevents `REPORT_640`, PCA, classifier, object, and threshold outputs from becoming input features. |
| S2 cloud/shadow/snow/edge masking | Sensor QA | High | Reduces false positives from invalid optical pixels. |
| SAR layover/shadow/nodata/pairing QA | Sensor QA | High | Reduces false positives and broken SAR outputs. |
| Observation dates/counts/dispersion/resolution report | Provenance | High | Shows whether evidence is stable or weak. |
| Season/acquisition-window matching | Comparability | Medium-High | Avoids comparing incompatible acquisition conditions. |
| Connected-component pixel features | Object scoring | High | Prevents background pixels from corrupting object features. |
| Local-background contrast features | Object scoring | High | Measures whether a candidate is locally unusual. |
| Robust statistics: median/MAD/quantiles/texture | Object scoring | High | More stable than mean/std/max alone. |
| Raw anomaly values | PCA/classifier correctness | High | Display stretching can distort scores. |
| `INSUFFICIENT_DATA` abstention | Result quality | High | Prevents ranking when valid data is too weak. |
| Deterministic cluster aggregation | Result stability | Medium-High | Prevents unstable summaries under ties/overlaps. |
| Threshold sensitivity report | Confidence control | Medium-High | Shows whether results survive small threshold changes. |
| Bootstrap/stability report | Confidence control | Medium-High | Separates robust candidates from fragile ones. |
| Control areas and hard negatives | Calibration | High | Needed before scores can mean more than within-run priority. |
| Spatially blocked validation if labels exist | Validation | High | Prevents spatial leakage/overfitting. |
| PR-AUC, recall at fixed FPR, calibration error | Model evaluation | High if labels exist | Gives real performance numbers if labels become available. |

## Standard validation command set

After each phase, run the smallest relevant tests first, then the broader affected set.

Minimum recurring set:

```powershell
pytest tests/unit/test_classifier_stage.py tests/unit/test_run_quality_summary.py tests/integration/test_artifact_serving.py tests/integration/test_frontend_static.py
```

Pipeline correctness set:

```powershell
pytest tests/unit/test_s2_nodata_dtype_contract.py tests/unit/test_sar_rtc.py tests/unit/test_hypercube.py tests/notebook_parity/test_hypercube_parity.py tests/notebook_parity/test_thermal_parity.py
```

Runtime/data integrity set:

```powershell
pytest tests/unit/test_run_state.py tests/integration/test_runs_api.py tests/integration/test_startup_stale_run_cleanup.py tests/unit/test_full_job_artifact_inventory.py
```

Full affected set before push:

```powershell
pytest tests/unit/test_classifier_stage.py tests/unit/test_run_quality_summary.py tests/integration/test_artifact_serving.py tests/integration/test_frontend_static.py tests/unit/test_s2_nodata_dtype_contract.py tests/unit/test_sar_rtc.py tests/unit/test_hypercube.py tests/notebook_parity/test_hypercube_parity.py tests/unit/test_run_state.py tests/integration/test_runs_api.py tests/integration/test_startup_stale_run_cleanup.py tests/unit/test_full_job_artifact_inventory.py
```

## Required future-audit instruction

Future audits must start by reading this document and `AUDIT_DO_NOT_BREAK_CONTRACTS.md` before reading PRD v0.5.

PRD v0.5 is historical context only. It is not the active source of truth for classifier placement, classifier frontend/API visibility, or the local-private severity model.

## Current owner intent

The owner intent is:

```text
Ignore public-safety issues.
Ignore old PRD classifier-boundary issues.
Treat this as a local private app with classifier as an app feature.
Require an easy-English final area findings summary with ranked direct labels and the app probability or score for each.
Prioritize result correctness, data quality, artifact integrity, runtime reliability, and screening accuracy.
```
