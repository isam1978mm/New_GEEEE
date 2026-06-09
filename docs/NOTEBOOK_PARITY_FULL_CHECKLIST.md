# Notebook Parity Full Checklist

This file is the repository source of truth for the full notebook-parity roadmap.

The roadmap through Phase 10 is closed as a **contract/inventory roadmap**. That does not mean every runtime output has a frozen reference comparison. Remaining operational closure work is tracked in:

- `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`

Future work for this project must read this file before proposing or executing notebook-parity work. Chat-only checklist changes are not authoritative until this file or the prioritized checklist is updated in the repository.

## Current Scope Rule

Notebook parity means the app reproduces outputs that come from the in-scope notebook:

- `notebooks/new.ipynb`

Before any item is treated as a notebook-parity gap, it must answer:

1. Which `notebooks/new.ipynb` cell or phase produces it?
2. Which output artifact proves it exists?
3. Which app component reproduces it or should reproduce it?
4. Is a frozen notebook reference available for comparison?

If the item does not come from `notebooks/new.ipynb`, it is not a `new.ipynb` parity item.

## V6 Separation

The V6 paid-archive package is now treated as a separate external-notebook/package track, not part of `notebooks/new.ipynb` parity.

Historical Phase 2 covered V6 package import/export handling already present in the app. It does not prove that `notebooks/new.ipynb` generates the V6 package. V6 work remains parked until the external V6 notebook/export is deliberately brought back into scope.

See:

- `docs/V6_PACKAGE_GENERATION_SCOPE.md`
- `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`

## Reference-Freeze Gate

Any value-parity comparison against notebook outputs requires a frozen `notebooks/new.ipynb` reference bundle first.

Current required gate:

- **D1 — Freeze `notebooks/new.ipynb` reference bundle outside Git.**

D1 must capture:

- notebook version / repo commit / run date
- output file inventory
- SHA256 and file sizes
- private coordinate-bearing artifacts as filesystem-only reference material

No downstream comparison should claim notebook-value parity until D1 exists.

## Related Detailed Indexes and Contracts

- `docs/PHASE_4_COVERAGE_CHECKLIST.md`
- `docs/PHASE_4_FINAL_COVERAGE_SUMMARY.md`
- `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md`
- `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`
- `docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md`
- `docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md`
- `docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`
- `docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md`

## Rules

- Keep this as the full roadmap contract history.
- Use `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md` for the current remaining-job sequence.
- Do not create competing phase lists in chat or docs.
- Do not treat recommended-next text as approved scope unless it matches this checklist or the prioritized checklist is updated first.
- Notebook parity means real notebook outputs must be tracked as covered, pending, blocked, or explicitly out of scope by user decision.
- Runtime output presence and notebook-value parity are separate.
- Notebook-parity outputs are not public or HTTP outputs by default.
- Use neutral label-family names in docs and public-facing text.

```text
[x] Phase 0 — Output inventory lock — approved — 430969ddb583e140e20dd982b4d22420fe401e99
[x] Phase 1 — Parity mode architecture contract — approved — f8a62434c945292e9393429a21e749c676eb54d8
[x] Phase 2 — V6 package import/export parity — historical/import-only; V6 source remains external/parked — approved — 12f66a87ca88550daf80153d62ab542b8e325ce2
[x] Phase 3 — Raster/tensor parity alias helpers — approved — f30e69d4b3b9bb651ff20b7505790595d8976c04
[x] Phase 4A — Missing raster family registry — approved — e7129b6f26f033a2649f07df97c4701c006c27ea
[x] Phase 4B — Report-layer runtime/value parity verifier — approved — c36923090a57d46907b0e0bf39b9bc6522d10fb5
[x] Phase 4C — Private layer runtime/value parity verifier — approved — ddfc3d279666cd04c5a4c374186148bb85ad942e
[x] Phase 4D1 — DEM curvature formula reconstruction/status lock — approved — c273cc4da88968c45aaabb913e15f32198b11102
[x] Phase 4D2 — DEM Laplacian-style curvature verifier — approved — 7e41846a61769e5a9405112e09f6b1ac709aaa89
[x] Phase 4D3 — plan/profile curvature formula recovery lock — approved — 430325e2ff0e22ed2a0b38e32d5bd6f003330872
[x] Phase 4E1 — ASC/DESC Sentinel-1 source recovery contract — approved — 858494d88e74a2f8f72214a19a414c7907123b46
[x] Phase 4E2 — ASC/DESC Sentinel-1 support stack verifier — approved — 4081bfafe780e11074e7f0502e994e7e85af8270
[x] Phase 4E3 — S1 filtered layers stack recovery + verifier — approved — e8d17704d7ddba3ef1035c8e717bf14782971ee2
[x] Phase 4F1 — PAN layers stack recovery + verifier — approved — 22bae91ccc39831cac2f2e1f5235b1faf77b643b
[x] Phase 4F2 — PAN component layer verifier — approved — 5df882ee76356c2b249ee19f0f45711d2a878376
[x] Phase 4G1 — 2.5 m resampled hypercube recovery + verifier — approved — 64759eddc28fb5bb6eb2f4e88c09bf0f224515d7
[x] Phase 4H1 — neutral semantic raster recovery inventory — approved — ec5e1efaa2b2c0d097aa46d6b6945451f49f1aca
[x] Phase 4H2 — neutral semantic anomaly recovery + verifier — approved — 9a5f3b210931e6545fa60d01e3a7b4438d433685
[x] Phase 4H3 — neutral semantic hardness recovery + verifier — approved — 4237e4322b9700d8045733b8cd0b99c797ee6c19
[x] Phase 4H4 — neutral semantic fraction recovery + verifier — approved — dff0725473193c38a844ce3ef3332af186c369e5
[x] Phase 4H5 — neutral semantic relation rasters recovery + verifier — approved — 88ccf5b4094092766a203967599b399bcdfa632d
[x] Phase 4H6 — extended neutral semantic rasters recovery + verifier — approved — 9051c36d905b4d715e9b2fde227cdf7431bf4d73
[x] Phase 4H7 — neutral semantic logic rasters recovery + verifier — approved — 4c550313f89dd55f7f09ef1bab36d24a401d1822
[x] Phase 4H8 — neutral semantic density/artifact rasters recovery + verifier — approved — 3ce545e43a6dd0d455b0816ee33555a33ddc2ac4
[x] Phase 4H9 — remaining neutral semantic group recovery + verifier — approved — 19550c010405a5cfce56358fec040d1163b1e4a0
[x] Phase 4H10 — remaining neutral semantic group recovery + verifier — approved — 23308ae0ed1cf6a28cc761af949e88f208d4ab80
[x] Phase 4H11 — anchor / non-TIF neutral semantic patterns decision — approved — 28cc36325f7443a695727ce8a14812bd7242f040
[x] Phase 4Z — Phase 4 final coverage summary / naming cleanup — approved — ddb362ed7175bda4d65446f6278a3d54fe130e05
[x] Phase 5 — QA and intermediate parity — approved — 8ec135c68957cc92f3d62b91dd445896b8d4eb85 — contract: `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md`
[x] Phase 6 — Coordinate/map/private parity outputs — approved — b17dacbbe07bd40cc40b0e10022d51669e142578 — contract: `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`
[x] Phase 7 — Classifier/model parity — approved — 383446289214b52012c3ce9d49745cec3bdce376 — contract: `docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md`
[x] Phase 8 — Probability-only ML classifier design — approved — 8abab1a556c9788bc00555c856375c9921c26074 — contract: `docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md`
[x] Phase 9 — End-to-end parity harness — approved — ff5fb2f31abeaa40912e2486de6d5bf17ee8bb6c — contract: `docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`
[x] Phase 10 — Clean app vs parity app decision — approved — ff07adc5be43ea83186dbd55f69dab1bcfbc49bd — contract: `docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md`
```

Roadmap contract status: closed at Phase 10.

Current remaining operational work: continue from `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`, starting with D1 reference freeze.

## Required Read Order for Future Work

Future work must read:

1. `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
2. `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`
3. the specific phase contract docs referenced by the task

If these files conflict, stop and reconcile the checklist docs before changing runtime code.

(End of NOTEBOOK_PARITY_FULL_CHECKLIST.md.)
