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
[ ] Special Track G2 — Operator-only private generated-overlay UI
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

Status: later, not implemented.

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

Goal: make deep-learning model attempts feasible only when good data, approved weights, dependency policy, and evaluation requirements exist.

## Special Track I — Training cells with a real dataset

Goal: turn notebook training-cell ideas into a real dataset-driven training roadmap.

## Special Track J — Full Tesla inference flow decomposition and implementation decision

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
[ ] Special Track G2 — operator-only private generated-overlay UI design
[ ] Special Track H1 — deep-learning model feasibility with good data/weights
[ ] Special Track I1 — real dataset/training design
[ ] Special Track J1 — full Tesla inference flow decomposition
```

Do not run Special Track G2 implementation, Special Track H implementation, Special Track I training, or Special Track J runtime implementation until their design/decomposition phases are accepted by the user.
