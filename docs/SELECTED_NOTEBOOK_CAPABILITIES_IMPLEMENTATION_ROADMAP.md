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
[x] Phase B — Add controlled backend Earth Engine run flow
[x] Phase C — Add only defensible missing raster/feature writers
[x] Phase D — Add private KMZ/GeoJSON/heatmap artifact writers
[x] Phase E — Add private parity verifier against frozen notebook outputs
[x] Phase F — Add optional private CLI classifier using neutral labels and probability/score wording only
```

### Not approved

```text
[x] Excluded — Colab/Drive folder logic
[x] Excluded — duplicated notebook cells
```

### Still needed, but later / special track

```text
[ ] Special Track G — Controlled location overlay policy and public-exposure decision
[x] Special Track G2 — Operator-only private generated-overlay UI design
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

## Phase A — Add app map point picker + ROI/grid preview

Status: complete by `docs/IMPLEMENTATION_PHASE_A_MAP_ROI_PREVIEW.md`; implementation commit `dec33d213317a3ce97befe34c28941aa82b1dacb`.

Goal: add a normal app UI/operator workflow for selecting a point or small AOI and previewing the resulting ROI/grid before a backend run.

## Phase B — Add controlled backend Earth Engine run flow

Status: complete by `docs/IMPLEMENTATION_PHASE_B_CONTROLLED_EE_RUN_FLOW.md`; implementation commit `1c5a84b619de1e70a49f16ba98c8f07702044a38`.

Goal: add a controlled backend execution path for Earth Engine data acquisition and export, replacing notebook/Colab behavior with app-safe backend behavior.

## Phase C — Add only defensible missing raster/feature writers

Status: complete by `docs/IMPLEMENTATION_PHASE_C_DEFENSIBLE_RASTER_FEATURE_WRITERS.md`; implementation commit `28e8c6234d1d4bffe9af79f806a1c49421955570`.

Goal: implement only selected missing raster/feature writers that have exact source formula, clear metadata contract, and frozen or obtainable reference expectations.

## Phase D — Add private KMZ/GeoJSON/heatmap artifact writers

Status: complete by `docs/IMPLEMENTATION_PHASE_D_PRIVATE_MAP_ARTIFACT_WRITERS.md`; implementation commit `747662f00d38dbebf569ee0290f31d5cd47bfa20`.

Goal: add private filesystem-only writers for selected map artifacts, without public exposure.

## Phase E — Add private parity verifier against frozen notebook outputs

Status: complete by `docs/IMPLEMENTATION_PHASE_E_PRIVATE_PARITY_VERIFIER.md`; implementation commit `c7412bcc838f2c26bec6845ec2fb724a4782fa27`.

Goal: make the existing Phase 9 harness useful with a real frozen notebook reference bundle.

## Phase F — Add optional private CLI classifier using neutral labels and probability/score wording only

Status: complete by `docs/IMPLEMENTATION_PHASE_F_PRIVATE_CLI_CLASSIFIER.md`; implementation commit is recorded in the Phase F final report.

Goal: add or refine a private CLI-only classifier path using neutral labels and probability/score wording only.

## Special Track G — Controlled location overlay policy and public-exposure decision

Status: G1 access-control design complete by `docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md`; public overlay implementation remains blocked until a later explicit user-approved phase.

Goal: design and later implement controlled location overlays only after access-control, redaction, audit, and explicit exposure rules are approved.

## Special Track G2 — Operator-only private generated-overlay UI

Status: G2 design complete by `docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md`; operator-only UI implementation remains blocked until a later explicit user-approved phase.

Goal: allow an authorized operator to view generated private overlay results in the UI without making them public.

G2 is different from Phase A. Phase A lets the operator enter or click the starting point and preview ROI/GRID metadata. G2 is about viewing generated private overlay results after outputs exist.

G2 must require:

- authentication
- operator role
- per-run authorization
- default-off configuration
- audit logging
- redacted denial responses
- no public download path by default
- no general public visibility
- explicit later user approval before implementation

G2 must not be mixed with Special Track H, I, or J.

## Special Track H — Deep-learning model attempts with good data/weights

Status: H1 feasibility and candidate-ranking design complete by `docs/SPECIAL_TRACK_H_DEEP_LEARNING_FEASIBILITY.md`; model training, inference, weights, ML dependencies, and runtime integration remain blocked by the binding gates in `docs/ML_DATA_TRAINING_READINESS_PLAN.md`.

Goal: make deep-learning model attempts feasible only when good data, approved weights, dependency policy, and evaluation requirements exist.

H1 recommends the first future ML candidate as a private probability classifier over verified feature summaries, only after I1 defines the dataset, independent evidence, split, holdout, baseline-margin, and storage gates.

## Special Track I — Training cells with a real dataset

Status: I1 dataset/training design complete by `docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md`; dataset creation, training, inference, and model integration remain blocked until the I1 gates are satisfied by real private data.

Goal: turn notebook training-cell ideas into a real dataset-driven training roadmap.

## Special Track J — Full Tesla inference flow decomposition and implementation decision

Status: J1 decomposition complete by `docs/SPECIAL_TRACK_J_TESLA_FLOW_DECOMPOSITION.md`; full runtime implementation remains blocked unless a later user-approved slice is opened.

Goal: preserve the full Tesla inference flow as a desired capability, but decompose it before implementation.

## Recommended Codex execution order

```text
[x] Phase A
[x] Phase B
[x] Phase C1 — first selected writer slice
[x] Phase D1 — private map artifact writer contract and first writer
[x] Phase E1 — frozen reference bundle validator
[x] Phase E2 — verifier execution against frozen references
[x] Phase F1 — private neutral probability CLI classifier
[x] Special Track G1 — controlled location overlay access-control design
[x] Special Track G2 — operator-only private generated-overlay UI design
[x] Special Track H1 — deep-learning model feasibility with good data/weights
[x] Special Track I1 — real dataset/training design
[x] Special Track J1 — full Tesla inference flow decomposition
```

No further execution-order item is opened by this roadmap. Do not run Special Track G2 implementation, Special Track H model implementation, Special Track I training, or Special Track J runtime implementation until a new user-approved implementation slice is accepted.

## Future Slice Decision Queue

The next decision is not another automatic roadmap phase. The next decision is which user-approved future slice to open first.

This is primarily an order and priority decision, but each choice also changes what Codex is allowed to touch.

```text
[ ] Option A — J2 source-lock one Tesla-flow substep
[ ] Option B — I2 create private dataset pack outside git
[ ] Option C — H2 optional ML dependency sandbox
[ ] Option D — G2 implementation foundation for operator-only private overlay UI
[ ] Option E — Phase C2 implement one additional formula-backed feature writer
[ ] Option F — Phase D2 implement one additional private map artifact writer
[ ] Option G — Phase E follow-up comparator for Phase C or Phase D outputs
```

### Option A — J2 source-lock one Tesla-flow substep

Purpose: choose one decomposed Tesla-flow substep and lock its evidence, source formula, inputs, outputs, status, and implementation boundary before coding.

Best when: the next priority is turning the Tesla decomposition into a safe implementation slice.

Not allowed: implementing the full Tesla runtime as one block.

### Option B — I2 create private dataset pack outside git

Purpose: start building the real private dataset pack only if independent evidence-backed labels are available or can be supplied.

Best when: the next priority is real ML/data preparation.

Required first: real independent evidence sources, dataset storage location outside git, label policy, split policy, and manifest policy from I1.

Not allowed: training or inference.

### Option C — H2 optional ML dependency sandbox

Purpose: create an optional ML dependency environment that does not affect normal app startup.

Best when: the next priority is preparing later private ML experiments.

Required first: H1/I1 gates remain binding.

Not allowed: adding PyTorch/TensorFlow as required base app dependencies, training, inference, or downloading weights.

### Option D — G2 implementation foundation for operator-only private overlay UI

Purpose: implement the foundation needed before an operator can view generated private overlays in the UI.

Best when: the next priority is operator UI access to generated private overlay results.

Required first: authentication, operator role, per-run authorization, audit logging, default-off config, and redacted denial policy.

Not allowed: public overlay exposure or public downloads.

### Option E — Phase C2 implement one additional formula-backed feature writer

Purpose: add exactly one more defensible feature writer with locked formula evidence and tests.

Best when: the next priority is expanding app-side private feature generation.

Required first: exact source formula, metadata/grid policy, and tiny fixture tests.

Not allowed: broad notebook stack port or guessed formulas.

### Option F — Phase D2 implement one additional private map artifact writer

Purpose: add exactly one more private filesystem-only map artifact writer, such as a private KMZ or heatmap slice.

Best when: the next priority is private operator artifacts.

Required first: private-only path safety, redaction metadata, and no public serving.

Not allowed: public frontend previews or public downloads.

### Option G — Phase E follow-up comparator for Phase C or Phase D outputs

Purpose: add a real comparator for outputs that are currently presence-gated or verifier-not-available.

Best when: the next priority is stronger frozen-reference parity.

Required first: frozen notebook reference files or tiny reference fixtures for tests.

Not allowed: generating app outputs or marking notebook-value parity true without comparison.

## Recommended default next slice

If no other priority is chosen, the recommended default is:

```text
Option A — J2 source-lock one Tesla-flow substep
```

Reason: it is the safest bridge from decomposition to implementation. It lets the user choose one small Tesla-flow piece, lock the evidence, and decide whether it should become a Phase C, D, E, G2, H, or I follow-up slice.
