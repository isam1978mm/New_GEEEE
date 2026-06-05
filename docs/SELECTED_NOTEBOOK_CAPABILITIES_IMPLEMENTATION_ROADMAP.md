# Selected Notebook Capabilities Implementation Roadmap

This is a new implementation roadmap created after the notebook-parity roadmap closed at Phase 10.

It is not Phase 11. It does not reopen the notebook-parity roadmap.

Purpose: turn selected notebook capabilities into controlled app implementation phases and Codex-ready goals.

## Source context

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md`
- `docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`
- `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`
- `docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md`
- `docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md`
- notebook-cell audit / extracted notebook summary supplied by the user

## User-approved scope

### Approved for implementation planning now

```text
[x] Phase A — Add app map point picker + ROI/grid preview
[ ] Phase B — Add controlled backend Earth Engine run flow
[ ] Phase C — Add only defensible missing raster/feature writers
[ ] Phase D — Add private KMZ/GeoJSON/heatmap artifact writers
[ ] Phase E — Add private parity verifier against frozen notebook outputs
[ ] Phase F — Add optional private CLI classifier using neutral labels and probability/score wording only
```

### Not approved

```text
[x] Excluded — Colab/Drive folder logic
[x] Excluded — duplicated notebook cells
```

### Still needed, but later / special track

```text
[ ] Special Track G — Exact-coordinate public map overlays
[ ] Special Track H — Deep-learning model attempts with good data/weights
[ ] Special Track I — Training cells with a real dataset
[ ] Special Track J — Full Tesla inference flow decomposition and implementation decision
```

## Non-negotiable rules

- Do not copy Colab/Drive folder logic into the app.
- Do not port duplicated notebook cells.
- Do not port the full Tesla inference flow as one unreviewed monolithic app engine.
- Full Tesla inference flow is still needed, but it must first be decomposed into small source-driven, reference-driven modules under Special Track J.
- Do not expose private coordinate, map, classifier, or model artifacts publicly without a later explicit user-approved exposure phase.
- Keep classifier/model work neutral-label and probability/score wording only unless a later user-approved roadmap changes that policy.
- Runtime output presence and notebook-value parity remain separate.
- Frozen notebook references are required before notebook-value parity can pass.
- No formulas, writers, model outputs, or public exposure may be guessed from nearby outputs.

## What “full Tesla inference flow” means in this roadmap

The notebook’s Tesla-style flow is not one clean module. It combines many behaviors:

- data acquisition
- grid alignment
- raster and feature formulas
- hard classifier logic
- model/CNN attempts
- coordinate outputs
- KMZ/GeoJSON/heatmap outputs
- visual overlays
- repeated variants and duplicate cells

Therefore:

```text
Allowed:
- analyze the full Tesla flow
- inventory every sub-function
- split it into safe modules
- implement approved modules one at a time

Not allowed:
- copy the full Tesla flow into the app as one large engine
- mix data acquisition, classifier, map exports, model inference, and public overlays in one Codex task
- introduce hard claims or public coordinate exposure without separate approval
```

## Phase A — Add app map point picker + ROI/grid preview

Goal: add a normal app UI/operator workflow for selecting a point or small AOI and previewing the resulting ROI/grid before a backend run.

Status: complete by `docs/IMPLEMENTATION_PHASE_A_MAP_ROI_PREVIEW.md`; implementation commit `dec33d213317a3ce97befe34c28941aa82b1dacb`.

Scope:

- map point picker
- manual coordinate entry fallback
- ROI preview
- grid preview
- validation of CRS/grid metadata
- no Earth Engine execution in this phase
- no raster generation in this phase
- no coordinate export artifacts in this phase

Codex goal summary:

```text
Build an app-side operator point picker and ROI/grid preview only. Do not start Earth Engine jobs. Do not generate rasters or map artifacts. Keep existing API/frontend/database boundaries unless a small preview endpoint is already consistent with current architecture. Add tests for coordinate validation, ROI construction, grid preview payload, and no artifact generation.
```

Acceptance gates:

- operator can select or enter a coordinate
- app can show ROI/grid preview metadata
- invalid coordinates are rejected
- no Earth Engine call occurs
- no output artifacts are created
- no private coordinate artifacts are exposed as downloads

## Phase B — Add controlled backend Earth Engine run flow

Goal: add a controlled backend execution path for Earth Engine data acquisition and export, replacing notebook/Colab behavior with app-safe backend behavior.

Scope:

- service-account or approved backend authentication only
- no notebook `ee.Authenticate()` flow
- AOI/date/cloud/orbit parameter validation
- job lifecycle states
- safe timeout/error reporting
- no Google Drive dependency
- no Colab folder dependency

Codex goal summary:

```text
Add a controlled backend Earth Engine run flow using approved backend auth and app run directories. Do not use Colab, Google Drive mounting, or notebook auth fallback. Do not change raster math. Add tests for parameter validation, auth-boundary behavior, dry-run/smoke behavior, and safe failure reporting.
```

Acceptance gates:

- backend can validate run parameters
- unsafe or missing auth fails safely
- no Colab/Drive path is used
- run status is persisted or reported consistently with current app architecture
- no public coordinate artifact exposure is added

## Phase C — Add only defensible missing raster/feature writers

Goal: implement only selected missing raster/feature writers that have exact source formula, clear metadata contract, and frozen or obtainable reference expectations.

Scope:

- choose one small writer slice at a time
- source formula must be documented
- metadata/grid contract must be documented
- writer must be private or clean-app appropriate by Phase 10 boundary
- add tests with tiny fixtures
- no broad mixed-flow port

Codex goal summary:

```text
Implement one defensible raster/feature writer slice only. Use exact source formula and existing grid metadata. Do not guess formulas. Do not implement unrelated notebook stacks. Add focused tests for metadata, shape, dtype, nodata behavior, and safe output path. Keep notebook-value parity false until a frozen reference comparison passes.
```

Acceptance gates:

- exact formula evidence exists
- writer is small and testable
- output path is safe
- grid metadata is locked
- tests cover metadata and values on tiny fixtures
- no unrelated notebook features are added

## Phase D — Add private KMZ/GeoJSON/heatmap artifact writers

Goal: add private filesystem-only writers for selected map artifacts, without public exposure.

Scope:

- private KMZ writer
- private GeoJSON writer
- private heatmap image/HTML/KMZ writer if approved per slice
- redaction and artifact-class metadata
- no public API download by default
- no frontend preview by default

Codex goal summary:

```text
Add private filesystem-only map artifact writers for selected outputs. Do not add public downloads, frontend previews, map tiles, or HTTP serving. Add tests for artifact class, local path safety, redaction metadata, and no public DTO leakage.
```

Acceptance gates:

- private artifacts are written only under run directory
- artifact class is private/local-sensitive
- public DTOs do not include raw coordinates, local paths, geometry, or sensitive hashes
- artifact serving policy is unchanged
- tests prove no accidental HTTP/frontend exposure

## Phase E — Add private parity verifier against frozen notebook outputs

Goal: make the existing Phase 9 harness useful with a real frozen notebook reference bundle.

Scope:

- define expected reference bundle layout
- add reference-bundle validator
- run existing family verifiers where available
- report missing references as incomplete, not success
- preserve runtime-output vs notebook-value parity separation

Codex goal summary:

```text
Add frozen-reference bundle validation and private verifier execution around the existing Phase 9 harness. Do not generate app outputs. Do not run the live pipeline. Do not call Earth Engine. Add tests for missing references, matching tiny fixtures, mismatches, and comparison_unavailable behavior.
```

Acceptance gates:

- frozen reference bundle contract exists
- verifier reports are deterministic
- missing references are not success
- comparison_unavailable is not success
- notebook-value parity only passes when comparison passes

## Phase F — Add optional private CLI classifier using neutral labels and probability/score wording only

Goal: add or refine a private CLI-only classifier path using neutral labels and probability/score wording only.

Scope:

- CLI-only
- env-gated
- neutral labels only
- no API/frontend/background/core orchestrator calls
- probability/score/uncertainty wording only
- no hard claims
- no model training unless Special Track H and Special Track I are approved

Codex goal summary:

```text
Implement or refine a private CLI-only classifier output path using neutral class labels and probability/score fields only. Keep it env-gated and filesystem-only. Do not connect it to API, frontend, BackgroundTasks, or core orchestration. Do not train models. Add tests for label neutrality, probability-only schema, gating, output paths, and forbidden wording.
```

Acceptance gates:

- classifier remains CLI-only
- requires experimental enable flag
- labels are neutral
- outputs use probability/score/uncertainty wording only
- no public exposure
- no training or model downloads

## Special Track G — Exact-coordinate public map overlays

Goal: design and later implement exact-coordinate public map overlays only after access-control, redaction, audit, and explicit public-exposure rules are approved.

Scope:

- operator-only overlay mode first
- role/access checks
- redaction options
- audit log requirements
- public/private toggle decision
- no default public exposure
- no public overlay implementation until the design is accepted

Codex goal summary:

```text
Design exact-coordinate public map overlay policy and access control. Do not expose overlays publicly by default. Define operator-only mode, redaction rules, audit logging, DTO boundaries, and artifact-serving constraints. Implementation requires separate user approval after the design is accepted.
```

Acceptance gates:

- exact-coordinate exposure policy is documented
- public/private modes are explicit
- redaction rules are explicit
- audit requirements are explicit
- no public map overlay is added during design phase

## Special Track H — Deep-learning model attempts with good data/weights

Goal: make deep-learning model attempts feasible only when good data, approved weights, dependency policy, and evaluation requirements exist.

Scope:

- identify candidate architectures from notebook evidence
- define dependency policy
- define weights policy
- define minimum data requirements
- define evaluation metrics
- define private inference boundary
- no training or inference in this design phase

Codex goal summary:

```text
Create a deep-learning model feasibility and implementation design. Do not train models yet. Do not run inference. Define candidate architectures, data requirements, weights policy, dependency policy, evaluation metrics, and private inference boundary. Implementation requires later user approval after data and weights are ready.
```

Acceptance gates:

- approved data/weights requirements are documented
- dependency policy is documented
- metrics are documented
- private inference boundary is documented
- no model training or inference is added

## Special Track I — Training cells with a real dataset

Goal: turn notebook training-cell ideas into a real dataset-driven training roadmap.

Scope:

- dataset schema
- label QA
- train/validation/test split
- baseline training plan
- evaluation metrics
- reproducibility requirements
- no training until dataset readiness is proven

Codex goal summary:

```text
Create a real dataset and training roadmap for future ML work. Do not train models yet. Define dataset schema, label QA, split policy, baseline training plan, metrics, reproducibility requirements, and private inference boundary. Implementation and training require later approval after dataset readiness is proven.
```

Acceptance gates:

- dataset schema exists
- label quality process exists
- train/validation/test split is defined
- evaluation metrics are defined
- reproducibility requirements are defined
- no training is added yet

## Special Track J — Full Tesla inference flow decomposition and implementation decision

Goal: preserve the full Tesla inference flow as a desired capability, but decompose it before implementation.

Scope:

- inventory every Tesla-flow substep from notebook evidence
- classify each substep as data acquisition, grid alignment, feature writer, classifier, model attempt, map artifact, overlay, or report
- map each substep to Phase A-F or Special Track G-I
- identify unsafe, duplicate, or unsupported substeps
- decide which substeps become future implementation tasks
- no runtime implementation during the decomposition phase

Codex goal summary:

```text
Analyze the full Tesla inference flow and decompose it into approved app modules. Do not implement it as one engine. Produce an inventory mapping each substep to Phase A-F or Special Track G-I, mark unsupported duplicates, and recommend safe future slices. Do not add runtime behavior, model inference, public overlays, or artifact exposure in this phase.
```

Acceptance gates:

- full Tesla flow inventory exists
- every substep is mapped to an approved phase or marked unsupported
- duplicate cells are excluded
- unsafe exposure is blocked
- future implementation slices are small and user-approvable
- no runtime behavior is added

## Recommended Codex execution order

```text
[ ] Phase A
[ ] Phase B
[ ] Phase C1 — first selected writer slice
[ ] Phase D1 — private map artifact writer contract and first writer
[ ] Phase E1 — frozen reference bundle validator
[ ] Phase E2 — verifier execution against frozen references
[ ] Phase F1 — private neutral probability CLI classifier, if still desired
[ ] Special Track G1 — exact-coordinate public overlay access-control design
[ ] Special Track H1 — deep-learning model feasibility with good data/weights
[ ] Special Track I1 — real dataset/training design
[ ] Special Track J1 — full Tesla inference flow decomposition
```

Do not run Special Track G implementation, Special Track H implementation, Special Track I training, or Special Track J runtime implementation until their design/decomposition phases are accepted by the user.
