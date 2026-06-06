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

## Completed Codex execution order

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

No further automatic execution-order item is opened by the completed roadmap. The future work below is user-approved directionally, but each item still needs its own scoped Codex goal before execution.

## Future Work Backlog: Best Order And Priority

These are not mutually exclusive options. The user wants all of this work done over time. The decision is the order, priority, and exact scope of each next Codex slice.

Recommended sequence:

```text
[ ] 01 — J2 source-lock one Tesla-flow substep
[ ] 02 — Phase C2 implement another defensible feature writer
[ ] 03 — Phase E3 add comparator for Phase C semantic feature outputs
[ ] 04 — Phase D2 add private KMZ writer
[ ] 05 — Phase D3 add private heatmap writer
[ ] 06 — Phase E4 add comparator for Phase D private map artifacts
[ ] 07 — H1 revisit after I1/J1
[ ] 08 — I2 create private dataset pack outside git
[ ] 09 — H2 optional ML dependency sandbox
[ ] 10 — G2 implementation design/details
[ ] 11 — G2 auth/role/audit foundation
[ ] 12 — G2 operator-only private overlay preview
```

### App capability track

```text
[ ] A1 — J2 source-lock one Tesla substep
[ ] A2 — Phase C2 implement another defensible feature writer
[ ] A3 — Phase D2 add private KMZ writer
[ ] A4 — Phase D3 add private heatmap writer
```

Purpose: move from decomposition into safe app capability, one small source-locked implementation slice at a time.

Best order inside this track:

1. J2 source-lock one Tesla substep.
2. Implement one formula-backed feature writer from that locked substep if it qualifies.
3. Add private KMZ writer.
4. Add private heatmap writer.

Rules:

- Do not implement the full Tesla runtime as one block.
- Do not guess formulas.
- Do not add public coordinate exposure.
- Do not add broad notebook stack ports.

### ML and data track

```text
[ ] B1 — H1 revisit after I1/J1
[ ] B2 — I2 create private dataset pack outside git
[ ] B3 — H2 optional ML dependency sandbox
```

Purpose: prepare real ML work only after the governance gates are satisfied.

Best order inside this track:

1. Revisit H1 after I1 and J1 to update candidate rankings based on real dataset constraints and Tesla-flow decomposition.
2. Create the private dataset pack outside git only if independent evidence-backed labels are available or can be supplied.
3. Add an optional ML dependency sandbox only after dataset and dependency policies remain satisfied.

Rules:

- No training until I2 data gate passes.
- No inference until training/evaluation or approved-weight validation passes.
- No required PyTorch/TensorFlow dependency in the base app.
- No model output API/frontend integration at this stage.

### Operator overlay UI track

```text
[ ] C1 — G2 implementation design/details
[ ] C2 — auth/role/audit foundation
[ ] C3 — operator-only private overlay preview
```

Purpose: let an authorized operator view generated private overlay results in the UI later, without making them public.

Best order inside this track:

1. Finalize G2 implementation details.
2. Implement auth, operator role, per-run authorization, default-off config, and audit logging foundation.
3. Add operator-only private overlay preview.

Rules:

- Do not jump straight to public overlays.
- Do not add public downloads.
- Do not expose generated private overlays to general users.
- Keep denial responses redacted.

### Parity and reference verification track

```text
[ ] D1 — collect frozen notebook reference bundle outside git
[ ] D2 — add comparator for Phase C semantic feature writer
[ ] D3 — add comparator for Phase D private GeoJSON writer
```

Purpose: make private parity stronger by comparing generated app outputs to frozen notebook references when references exist.

Best order inside this track:

1. Collect frozen notebook reference bundle outside git.
2. Add comparator for Phase C semantic feature outputs.
3. Add comparator for Phase D private GeoJSON outputs.

Rules:

- Missing references are not success.
- Do not commit frozen reference artifacts to git.
- Do not mark notebook-value parity true without comparison.
- Do not generate app outputs inside verifier-only tasks.

## Recommended next slice

The best next slice is:

```text
01 — J2 source-lock one Tesla-flow substep
```

Reason: it is the safest bridge from decomposition to implementation. It chooses one small Tesla-flow piece, locks the evidence, and decides whether it should become a Phase C writer, Phase D private artifact, Phase E comparator, G2 operator overlay task, or ML/data task.
