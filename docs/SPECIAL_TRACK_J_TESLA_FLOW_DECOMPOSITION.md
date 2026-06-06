# Special Track J1 Tesla Flow Decomposition

Special Track J1 is decomposition, inventory, mapping, and decision only.

It does not implement runtime behavior, port the Tesla-style flow as one block,
train models, run inference, retrieve weights, create datasets, call Earth
Engine, generate artifacts, or change API, frontend, database, raster/math, or
artifact-serving behavior.

## Source Of Truth

The J1 helper is:

```text
app/pipeline/parity/tesla_flow_decomposition.py
```

It writes one private JSON report:

```text
data/runs/<run_id>/manifests/special_track_j1_tesla_flow_decomposition.json
```

The report is metadata only. It must not create model weights, datasets, chips,
labels, rasters, NPY files, map artifacts, coordinate artifacts, public
classifier outputs, or training outputs.

## Decomposition Categories

J1 decomposes the notebook Tesla-style flow into these categories:

| Category | Mapping decision |
| --- | --- |
| `roi_grid_alignment` | Covered by Phase A for preview-only point/ROI/GRID metadata. |
| `data_acquisition` | Maps to Phase B planning and later controlled provider slices. |
| `raster_feature_writer` | Maps to Phase C only when formula and GRID evidence are locked. |
| `private_map_artifact` | Maps to Phase D only when filesystem-only and private. |
| `provenance_report` | Maps to Phase E verifier and private report behavior. |
| `private_classifier_scoring` | Maps to Phase F only with neutral probability/score outputs. |
| `generated_overlay_ui` | Maps to G2 and remains blocked until operator-only gates are implemented. |
| `public_exposure` | Maps to G/G1 and remains blocked now. |
| `ml_model_attempt` | Maps to H/H1 and remains blocked by ML/data gates. |
| `dataset_training` | Maps to I/I1 and remains blocked until dataset gates pass. |
| `duplicate_or_variant` | Excluded or mapped to a canonical substep. |
| `unsupported_or_unclear` | Not implementation-ready. |
| `blocked_by_policy` | Must not be ported as-is. |

## Completed Phase Mappings

Phase A covers pre-run ROI and GRID preview only.

Phase B covers controlled backend planning and auth readiness. It does not run
the full acquisition stack by default.

Phase C covers the first defensible AI_BEH relation feature writer slice. Other
feature writers require one future source/reference-driven slice at a time.

Phase D covers the first private GeoJSON writer slice. Other map artifacts such
as KMZ, KML, or heatmap metadata require later private filesystem-only slices.

Phase E covers frozen-reference bundle validation and private verifier reporting.
Missing references or missing app outputs are not success.

Phase F covers the private neutral CLI classifier boundary. It does not port all
notebook rule variants or model attempts.

G1 and G2 cover public exposure and operator-overlay design gates only.

H1 and I1 cover ML feasibility and dataset/training gates only.

## Blocked Or Deferred Items

The full Tesla-style driver flow is blocked as a monolithic runtime path. It
mixes acquisition, feature writers, classifier logic, ML attempts, private map
artifacts, generated overlays, and global notebook state. It must never be
ported as one app engine.

Public exact-coordinate exposure is blocked pending separate user approval,
access-control design, redaction review, audit logging, frontend review, and
artifact-serving review.

ML/model attempts are blocked until H/I gates pass, including independent
evidence-backed labels, dataset manifest hashes, leakage-safe splits, holdout
size, baseline margin, dependency policy, weights policy, and private output
boundary.

Training remains blocked until the I1 dataset contract is satisfied by real
private data outside git.

Unsupported, unclear, broken, Colab-only, Drive-only, install-only, and repeated
notebook cells are not implementation-ready.

## Safe Future Execution Order

Recommended future order:

1. J2 optional: source-lock one future private slice from this decomposition.
2. H1 revisit: update model feasibility ranking after I1 data gates.
3. I2 optional: build private dataset pack outside git only after evidence gates pass.
4. H2 optional: dependency sandbox only if model path and validation gates justify it.
5. Phase C follow-up: add one formula-backed private raster writer at a time.
6. Phase D follow-up: add one filesystem-only private map writer at a time.
7. Phase E follow-up: add verifier comparators only with frozen references.
8. G2 implementation slice: add auth and role policy before overlay UI.
9. Later public exposure review: separate user approval before any public map surface.

This order does not start with a full Tesla runtime. Every future slice requires
later user approval and its own tests.

## J1 Safety Boundary

J1 does not:

- implement runtime behavior
- port the Tesla-style flow as one block
- train models
- run inference
- retrieve weights
- create datasets
- call Earth Engine
- generate rasters, NPY files, maps, coordinate files, labels, chips, or model artifacts
- connect anything to API or frontend
- change artifact-serving policy
- change raster or math logic

Runtime output presence and notebook-value parity remain separate. Frozen
references remain required before notebook-value parity can pass.
