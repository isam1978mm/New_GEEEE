# Selected Notebook Capabilities Implementation Roadmap

This is a new implementation roadmap created after the notebook-parity roadmap closed at Phase 10.

It is not Phase 11. It does not reopen the parity roadmap.

Purpose: turn selected notebook capabilities into controlled app implementation phases and Codex-ready goals.

Source context:

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md`
- `docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`
- `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`
- `docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md`
- `docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md`
- notebook-cell audit / extracted notebook summary supplied by the user

## Non-negotiable rules

- Do not copy Colab/Drive folder logic into the app.
- Do not port duplicated notebook cells.
- Do not port the mixed notebook inference flow as one large engine.
- Split notebook behavior into small source-driven, reference-driven app capabilities.
- Do not expose private coordinate, map, classifier, or model artifacts publicly without a later explicit user-approved exposure phase.
- Keep classifier/model work neutral-label and probability/score wording only.
- Runtime output presence and notebook-value parity remain separate.
- Frozen notebook references are required before notebook-value parity can pass.
- No formulas, writers, or public exposure may be guessed from nearby outputs.

## Approved implementation roadmap

```text
[ ] Implementation Phase A — Operator map point picker and ROI/grid preview
[ ] Implementation Phase B — Controlled backend Earth Engine run flow
[ ] Implementation Phase C — Defensible raster/feature writers
[ ] Implementation Phase D — Private KMZ/GeoJSON/heatmap artifact writers
[ ] Implementation Phase E — Frozen-reference private parity verifier
[ ] Implementation Phase F — Optional private CLI classifier with neutral probability/score outputs
[ ] Special Track G — Exact-coordinate overlay access-control and public-exposure decision
[ ] Special Track H — Real dataset and deep-learning training roadmap
```

## Not approved

These notebook behaviors are explicitly not approved for implementation:

- Colab/Drive folder logic
- duplicated notebook cells
- one-block port of the mixed notebook inference flow

## Still needed, later / special track

These are still desired, but require separate safety, data, access-control, and validation work:

- exact-coordinate public map overlays
- deep-learning model attempts only when good data/weights exist
- training cells only when a real dataset exists

## What “do not port the mixed inference flow as one block” means

The notebook contains a large mixed workflow that combines data pulls, grid alignment, feature formulas, classifier logic, map artifacts, exact-coordinate outputs, visual overlays, model attempts, and repeated variants.

Codex must not copy that as one monolithic app feature.

Instead, Codex must split it into the implementation phases below:

1. map point picker and ROI/grid preview
2. controlled Earth Engine backend flow
3. selected defensible feature writers
4. private map artifact writers
5. frozen-reference verifier
6. optional private neutral probability classifier
7. later exact-coordinate exposure decision
8. later dataset/training roadmap

## Phase A — Operator map point picker and ROI/grid preview

Goal: add a normal app UI/operator workflow for selecting a point or small AOI and previewing the resulting ROI/grid before a backend run.

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

## Phase B — Controlled backend Earth Engine run flow

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

## Phase C — Defensible raster/feature writers

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

## Phase D — Private KMZ/GeoJSON/heatmap artifact writers

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

## Phase E — Frozen-reference private parity verifier

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

## Phase F — Optional private CLI classifier with neutral probability/score outputs

Goal: add or refine a private CLI-only classifier path using neutral labels and probability/score wording only.

Scope:

- CLI-only
- env-gated
- neutral labels only
- no API/frontend/background/core orchestrator calls
- probability/score/uncertainty wording only
- no hard claims
- no model training unless Special Track H is approved

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

## Special Track G — Exact-coordinate overlay access-control and public-exposure decision

Goal: design and later implement exact-coordinate overlays only after access-control, redaction, audit, and user-approval rules are explicit.

Scope:

- operator-only overlay mode
- role/access checks
- redaction options
- audit log requirements
- public/private toggle decision
- no default public exposure

Codex goal summary:

```text
Design exact-coordinate overlay access control. Do not expose overlays publicly by default. Define operator-only policy, redaction rules, audit logging, DTO boundaries, and artifact-serving constraints. Implementation requires a separate approval after the design is accepted.
```

Acceptance gates:

- exact-coordinate exposure policy is documented
- public/private modes are explicit
- redaction rules are explicit
- audit requirements are explicit
- no public map overlay is added during design phase

## Special Track H — Real dataset and deep-learning training roadmap

Goal: make deep-learning/model work feasible only after a real dataset, weights policy, and evaluation plan exist.

Scope:

- dataset schema
- label QA
- training/validation/test split
- baseline model plan
- dependency policy
- weights policy
- evaluation metrics
- private inference boundary
- later app integration decision

Codex goal summary:

```text
Create a real dataset and training roadmap for future ML work. Do not train models yet. Define dataset schema, label QA, split policy, metrics, dependency/weights policy, baseline candidates, and private inference boundary. Implementation and training require a later approval after dataset readiness is proven.
```

Acceptance gates:

- dataset schema exists
- label quality process exists
- train/validation/test split is defined
- evaluation metrics are defined
- dependency and weights policy is defined
- no training or inference is added yet

## Recommended Codex execution order

```text
[ ] Phase A
[ ] Phase B
[ ] Phase C1 — first selected writer slice
[ ] Phase D1 — private map artifact writer contract and first writer
[ ] Phase E1 — frozen reference bundle validator
[ ] Phase E2 — verifier execution against frozen references
[ ] Phase F1 — private neutral probability CLI classifier, if still desired
[ ] Special Track G1 — exact-coordinate overlay exposure design
[ ] Special Track H1 — real dataset/training design
```

Do not run Special Track G implementation or Special Track H training until their design phases are accepted by the user.
