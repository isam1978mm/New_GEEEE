# Phase 4 Coverage Checklist

This file is the repository source of truth for Phase 4 coverage tracking.

Future Codex goals for this project must read this file before proposing or executing any Phase 4, Phase 5, or later notebook-parity work. Chat-only checklist changes are not authoritative until this file is updated in the repository.

Rules:

- Keep this as one checklist, not separated into competing phase lists.
- Do not rename phases without updating this file in the same commit.
- Do not treat Codex recommended-next text as approved scope unless it matches this checklist or this checklist is updated first.
- Notebook parity means real notebook outputs must be tracked as covered, pending, blocked, or explicitly out of scope by user decision.
- Do not mark an output as covered only because a similar app output exists.
- Runtime output presence and notebook-value parity are separate.
- Notebook-parity outputs are not public or HTTP outputs by default.

## Checklist

```text
[x] Phase 0 — Output inventory lock — approved — 430969ddb583e140e20dd982b4d22420fe401e99
[x] Phase 1 — Parity mode architecture contract — approved — f8a62434c945292e9393429a21e749c676eb54d8
[x] Phase 2 — v6 package import/export parity — approved — 12f66a87ca88550daf80153d62ab542b8e325ce2
[x] Phase 3 — Raster/tensor parity alias helpers — approved — f30e69d4b3b9bb651ff20b7505790595d8976c04
[x] Phase 4A — Missing raster family registry — approved — e7129b6f26f033a2649f07df97c4701c006c27ea
[x] Phase 4B — REPORT_640 runtime/value parity verifier — approved — c36923090a57d46907b0e0bf39b9bc6522d10fb5
[x] Phase 4C — Secret layer runtime/value parity verifier — approved — ddfc3d279666cd04c5a4c374186148bb85ad942e
[x] Phase 4D1 — DEM curvature formula reconstruction/status lock — approved — c273cc4da88968c45aaabb913e15f32198b11102
[x] Phase 4D2 — DEM Laplacian-style curvature verifier — approved — 7e41846a61769e5a9405112e09f6b1ac709aaa89
[x] Phase 4D3 — plan/profile curvature formula recovery lock — approved — 430325e2ff0e22ed2a0b38e32d5bd6f003330872
[x] Phase 4E1 — ASC/DESC Sentinel-1 source recovery contract — approved — 858494d88e74a2f8f72214a19a414c7907123b46
[x] Phase 4E2 — ASC/DESC Sentinel-1 support stack verifier — approved — 4081bfafe780e11074e7f0502e994e7e85af8270
[x] Phase 4E3 — S1 filtered layers stack recovery + verifier — approved — e8d17704d7ddba3ef1035c8e717bf14782971ee2
[x] Phase 4F1 — PAN layers stack recovery + verifier — approved — 22bae91ccc39831cac2f2e1f5235b1faf77b643b
[x] Phase 4F2 — PAN component layer verifier — approved — 5df882ee76356c2b249ee19f0f45711d2a878376
[x] Phase 4G1 — 2.5 m resampled hypercube recovery + verifier — approved — 64759eddc28fb5bb6eb2f4e88c09bf0f224515d7
[x] Phase 4H1 — semantic raster recovery inventory — approved — ec5e1efaa2b2c0d097aa46d6b6945451f49f1aca
[x] Phase 4H2 — AI_READY anomaly recovery + verifier — approved — 9a5f3b210931e6545fa60d01e3a7b4438d433685
[x] Phase 4H3 — AI_READY metal hardness recovery + verifier — approved — 4237e4322b9700d8045733b8cd0b99c797ee6c19
[x] Phase 4H4 — AI_READY fraction recovery + verifier — approved — dff0725473193c38a844ce3ef3332af186c369e5
[x] Phase 4H5 — semantic relation rasters recovery + verifier — approved — 88ccf5b4094092766a203967599b399bcdfa632d
[x] Phase 4H6 — extended semantic rasters recovery + verifier — approved — 9051c36d905b4d715e9b2fde227cdf7431bf4d73
[x] Phase 4H7 — semantic logic rasters recovery + verifier — approved — 4c550313f89dd55f7f09ef1bab36d24a401d1822
[x] Phase 4H8 — semantic density/artifact rasters recovery + verifier — approved — 3ce545e43a6dd0d455b0816ee33555a33ddc2ac4
[ ] Phase 4H9 — remaining rare-material semantic rasters recovery + verifier
[ ] Phase 4H10 — remaining alloy/statue semantic rasters recovery + verifier
[ ] Phase 4H11 — anchor / non-TIF semantic patterns decision
[ ] Phase 4Z — Phase 4 final coverage summary / naming cleanup
[ ] Phase 5 — QA and intermediate parity
[ ] Phase 6 — private coordinate/map parity outputs
[ ] Phase 7 — classifier/model parity
[ ] Phase 8 — probability-only ML classifier design
[ ] Phase 9 — end-to-end parity harness
[ ] Phase 10 — clean app vs parity app decision
```

## Detail sources

Detailed output names must be read from the approved contract docs and parity modules for each phase. This index intentionally avoids duplicating every output name so it does not drift from the phase contracts.

Phase 4Z must reconcile this index with the contract docs and semantic inventory after Phase 4H9 through Phase 4H11.
